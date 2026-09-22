"""Shared fixtures: an isolated in-memory DB session and a fake LLM client,
so tests never touch the real database or make network calls.
"""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.ai.tool_calling import get_llm_client
from app.db import get_session
from app.main import app


class FakeLLMClient:
    """Implements LLMClient with no network calls, for tests."""

    def __init__(
        self, response: dict | None = None, error: Exception | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.last_call: dict[str, Any] | None = None

    def call_tool(self, **kwargs: Any) -> dict:
        """Record the call and return the canned response, or raise error."""
        self.last_call = kwargs
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """A fresh in-memory SQLite session, isolated per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="fake_llm_client")
def fake_llm_client_fixture() -> FakeLLMClient:
    """A FakeLLMClient defaulting to an empty task list; tests can override
    .response/.error before making a request.
    """
    return FakeLLMClient(response={"tasks": []})


@pytest.fixture(name="client")
def client_fixture(
    session: Session,
    fake_llm_client: FakeLLMClient,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """A TestClient wired to the isolated session and fake LLM client above."""

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    # The app's lifespan calls create_db_and_tables() against app.db.engine
    # directly (not through get_session), so it must be patched too - otherwise
    # every test run creates a real, if empty, todo.db file on disk.
    monkeypatch.setattr("app.db.engine", session.get_bind())
    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_llm_client] = lambda: fake_llm_client
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

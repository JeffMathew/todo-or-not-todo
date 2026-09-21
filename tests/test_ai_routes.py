from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.ai.tool_calling import LLMClientError
from app.models import Task
from tests.conftest import FakeLLMClient


def test_proposals_renders_editable_rows(
    client: TestClient, fake_llm_client: FakeLLMClient
) -> None:
    fake_llm_client.response = {
        "tasks": [{"title": "Buy milk", "due_date": "2026-09-22"}]
    }

    response = client.post("/ai/proposals", data={"text": "buy milk tomorrow"})

    assert response.status_code == 200
    assert 'value="Buy milk"' in response.text
    assert "Confirm" in response.text


def test_proposals_client_error_renders_inline_at_200(
    client: TestClient, fake_llm_client: FakeLLMClient
) -> None:
    fake_llm_client.error = LLMClientError("Bedrock is down")

    response = client.post("/ai/proposals", data={"text": "buy milk"})

    assert response.status_code == 200
    assert "Bedrock is down" in response.text


def test_confirm_creates_only_included_rows(
    client: TestClient, session: Session
) -> None:
    response = client.post(
        "/ai/proposals/confirm",
        data={
            "count": "2",
            "included_0": "1",
            "title_0": "Buy milk",
            "due_date_0": "",
            "priority_0": "",
            "title_1": "Skip me",
            "due_date_1": "",
            "priority_1": "",
        },
    )

    assert response.status_code == 200
    tasks = session.exec(select(Task)).all()
    assert len(tasks) == 1
    assert tasks[0].title == "Buy milk"
    assert tasks[0].source == "ai"


def test_confirm_skips_blank_title_row(client: TestClient, session: Session) -> None:
    response = client.post(
        "/ai/proposals/confirm",
        data={
            "count": "1",
            "included_0": "1",
            "title_0": "",
            "due_date_0": "",
            "priority_0": "",
        },
    )

    assert response.status_code == 200
    assert session.exec(select(Task)).all() == []

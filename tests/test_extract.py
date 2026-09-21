import json
from datetime import date
from pathlib import Path

import pytest

from app.ai.extract import ExtractionError, extract_tasks
from app.ai.tool_calling import LLMClientError
from tests.conftest import FakeLLMClient

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_extract_tasks_basic() -> None:
    client = FakeLLMClient(response=_load_fixture("extract_basic.json"))

    tasks = extract_tasks(client, "buy milk and call dentist", today=date(2026, 9, 21))

    assert len(tasks) == 2
    assert tasks[0].title == "Buy milk"
    assert str(tasks[0].due_date) == "2026-09-22"
    assert tasks[1].title == "Call dentist"
    assert tasks[1].due_date is None
    assert tasks[1].priority is None


def test_extract_tasks_empty() -> None:
    client = FakeLLMClient(response=_load_fixture("extract_empty.json"))

    tasks = extract_tasks(client, "no tasks here", today=date(2026, 9, 21))

    assert tasks == []


def test_extract_tasks_invalid_output_raises() -> None:
    client = FakeLLMClient(response=_load_fixture("extract_invalid.json"))

    with pytest.raises(ExtractionError):
        extract_tasks(client, "some text", today=date(2026, 9, 21))


def test_extract_tasks_client_error_raises() -> None:
    client = FakeLLMClient(error=LLMClientError("boom"))

    with pytest.raises(ExtractionError):
        extract_tasks(client, "some text", today=date(2026, 9, 21))


def test_extract_tasks_passes_today_into_prompt() -> None:
    client = FakeLLMClient(response=_load_fixture("extract_empty.json"))

    extract_tasks(client, "some text", today=date(2026, 9, 21))

    assert client.last_call is not None
    assert "2026-09-21" in client.last_call["system_prompt"]

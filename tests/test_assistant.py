from datetime import date

from app.ai.assistant import AssistantError, ask_assistant
from app.ai.tool_calling import LLMClientError
from app.models import Priority, Task
from tests.conftest import FakeLLMClient


def _task(title: str = "Sample task", priority: Priority | None = None) -> Task:
    return Task(title=title, priority=priority)


def test_ask_assistant_confident_answer() -> None:
    client = FakeLLMClient(
        response={"can_answer": True, "answer": "You have 2 high priority tasks."}
    )
    tasks = [_task(priority=Priority.high), _task(priority=Priority.high)]

    result = ask_assistant(
        client, "How many high priority tasks?", tasks, date(2026, 9, 21)
    )

    assert result.can_answer is True
    assert result.answer == "You have 2 high priority tasks."
    assert result.reason is None


def test_ask_assistant_cannot_answer() -> None:
    client = FakeLLMClient(
        response={
            "can_answer": False,
            "reason": "No tasks mention anything about the weather.",
        }
    )

    result = ask_assistant(client, "Will it rain tomorrow?", [], date(2026, 9, 21))

    assert result.can_answer is False
    assert result.answer is None
    assert result.reason == "No tasks mention anything about the weather."


def test_ask_assistant_invalid_output_raises() -> None:
    client = FakeLLMClient(response={"answer": "missing can_answer field"})

    try:
        ask_assistant(client, "Anything?", [], date(2026, 9, 21))
        raise AssertionError("expected AssistantError")
    except AssistantError:
        pass


def test_ask_assistant_client_error_raises() -> None:
    client = FakeLLMClient(error=LLMClientError("boom"))

    try:
        ask_assistant(client, "Anything?", [], date(2026, 9, 21))
        raise AssertionError("expected AssistantError")
    except AssistantError:
        pass


def test_ask_assistant_passes_today_and_tasks_into_prompt() -> None:
    client = FakeLLMClient(response={"can_answer": True, "answer": "ok"})
    tasks = [_task(title="Water the plants")]

    ask_assistant(client, "What's due?", tasks, date(2026, 9, 21))

    assert client.last_call is not None
    assert "2026-09-21" in client.last_call["system_prompt"]
    assert "Water the plants" in client.last_call["system_prompt"]

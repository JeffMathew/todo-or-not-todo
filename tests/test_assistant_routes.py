from fastapi.testclient import TestClient
from sqlmodel import Session

from app.ai.tool_calling import LLMClientError
from app.models import Task
from tests.conftest import FakeLLMClient


def test_ask_renders_confident_answer(
    client: TestClient, fake_llm_client: FakeLLMClient
) -> None:
    fake_llm_client.response = {"can_answer": True, "answer": "You have no tasks yet."}

    response = client.post("/assistant/ask", data={"question": "What's on my list?"})

    assert response.status_code == 200
    assert "You have no tasks yet." in response.text


def test_ask_renders_cannot_answer(
    client: TestClient, fake_llm_client: FakeLLMClient
) -> None:
    fake_llm_client.response = {
        "can_answer": False,
        "reason": "Nothing in the task data relates to this question.",
    }

    response = client.post(
        "/assistant/ask", data={"question": "What's the capital of France?"}
    )

    assert response.status_code == 200
    assert "I'm not sure" in response.text
    assert "Nothing in the task data relates to this question." in response.text


def test_ask_client_error_renders_inline_at_200(
    client: TestClient, fake_llm_client: FakeLLMClient
) -> None:
    fake_llm_client.error = LLMClientError("Bedrock is down")

    response = client.post("/assistant/ask", data={"question": "Anything?"})

    assert response.status_code == 200
    assert "Bedrock is down" in response.text


def test_ask_includes_existing_tasks_in_prompt(
    client: TestClient, session: Session, fake_llm_client: FakeLLMClient
) -> None:
    session.add(Task(title="Renew car insurance"))
    session.commit()
    fake_llm_client.response = {"can_answer": True, "answer": "ok"}

    client.post("/assistant/ask", data={"question": "What's outstanding?"})

    assert fake_llm_client.last_call is not None
    assert "Renew car insurance" in fake_llm_client.last_call["system_prompt"]

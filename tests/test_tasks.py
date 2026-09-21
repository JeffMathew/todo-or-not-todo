from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Priority, Task


def test_create_task_persists_it(client: TestClient, session: Session) -> None:
    response = client.post("/tasks", data={"title": "Buy milk"})

    assert response.status_code == 200
    assert "Buy milk" in response.text
    tasks = session.exec(select(Task)).all()
    assert len(tasks) == 1
    assert tasks[0].source == "manual"
    assert tasks[0].completed is False


def test_create_task_with_due_date_and_priority(
    client: TestClient, session: Session
) -> None:
    client.post(
        "/tasks",
        data={"title": "Ship it", "due_date": "2026-01-01", "priority": "high"},
    )

    task = session.exec(select(Task)).one()
    assert str(task.due_date) == "2026-01-01"
    assert task.priority == "high"


def test_create_task_requires_title(client: TestClient, session: Session) -> None:
    response = client.post("/tasks", data={"title": ""})

    assert response.status_code == 422
    assert session.exec(select(Task)).all() == []


def test_toggle_task_flips_completed(client: TestClient, session: Session) -> None:
    task = Task(title="Toggle me")
    session.add(task)
    session.commit()
    session.refresh(task)

    client.post(f"/tasks/{task.id}/toggle")
    session.refresh(task)
    assert task.completed is True

    client.post(f"/tasks/{task.id}/toggle")
    session.refresh(task)
    assert task.completed is False


def test_toggle_nonexistent_task_returns_404(client: TestClient) -> None:
    response = client.post("/tasks/999/toggle")
    assert response.status_code == 404


def test_edit_form_renders_current_values(client: TestClient, session: Session) -> None:
    task = Task(title="Edit me", priority=Priority.medium)
    session.add(task)
    session.commit()
    session.refresh(task)

    response = client.get(f"/tasks/{task.id}/edit")

    assert response.status_code == 200
    assert 'value="Edit me"' in response.text


def test_update_task_changes_fields(client: TestClient, session: Session) -> None:
    task = Task(title="Old title")
    session.add(task)
    session.commit()
    session.refresh(task)

    client.put(f"/tasks/{task.id}", data={"title": "New title", "priority": "low"})

    session.refresh(task)
    assert task.title == "New title"
    assert task.priority == "low"


def test_update_task_can_clear_optional_fields(
    client: TestClient, session: Session
) -> None:
    task = Task(title="Has extras", due_date=date(2026, 1, 1), priority=Priority.high)
    session.add(task)
    session.commit()
    session.refresh(task)

    client.put(
        f"/tasks/{task.id}",
        data={"title": "Has extras", "due_date": "", "priority": ""},
    )

    session.refresh(task)
    assert task.due_date is None
    assert task.priority is None


def test_update_nonexistent_task_returns_404(client: TestClient) -> None:
    response = client.put("/tasks/999", data={"title": "Nope"})
    assert response.status_code == 404


def test_delete_task_removes_it(client: TestClient, session: Session) -> None:
    task = Task(title="Delete me")
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert session.get(Task, task_id) is None


def test_delete_nonexistent_task_returns_404(client: TestClient) -> None:
    response = client.delete("/tasks/999")
    assert response.status_code == 404


def test_index_lists_existing_tasks(client: TestClient, session: Session) -> None:
    session.add(Task(title="Existing task"))
    session.commit()

    response = client.get("/")

    assert "Existing task" in response.text


def test_index_shows_empty_state_when_no_tasks(client: TestClient) -> None:
    response = client.get("/")
    assert "No tasks yet" in response.text

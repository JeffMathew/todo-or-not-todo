from sqlmodel import Session, col, select

from app.models import Task, TaskCreate, TaskSource, TaskUpdate


def list_tasks(session: Session) -> list[Task]:
    return list(session.exec(select(Task).order_by(col(Task.id))).all())


def get_task(session: Session, task_id: int) -> Task | None:
    return session.get(Task, task_id)


def create_task(
    session: Session, data: TaskCreate, source: TaskSource = TaskSource.manual
) -> Task:
    task = Task.model_validate(data, update={"source": source})
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def update_task(session: Session, task_id: int, data: TaskUpdate) -> Task | None:
    task = session.get(Task, task_id)
    if task is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def toggle_task(session: Session, task_id: int) -> Task | None:
    task = session.get(Task, task_id)
    if task is None:
        return None
    task.completed = not task.completed
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: int) -> bool:
    task = session.get(Task, task_id)
    if task is None:
        return False
    session.delete(task)
    session.commit()
    return True

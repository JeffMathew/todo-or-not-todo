from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskSource(StrEnum):
    manual = "manual"
    ai = "ai"


class TaskFields(SQLModel):
    due_date: date | None = None
    priority: Priority | None = None

    @field_validator("due_date", "priority", mode="before")
    @classmethod
    def blank_string_to_none(cls, value: object) -> object:
        return None if value == "" else value


class TaskBase(TaskFields):
    title: str = Field(min_length=1)


class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    completed: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    source: TaskSource = TaskSource.manual


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskFields):
    title: str | None = Field(default=None, min_length=1)

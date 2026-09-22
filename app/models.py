from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskSource(StrEnum):
    """How a task was created: typed by hand, or confirmed from an AI proposal."""

    manual = "manual"
    ai = "ai"


class TaskFields(SQLModel):
    """Fields shared by every task schema - the table and every input schema."""

    due_date: date | None = None
    priority: Priority | None = None

    @field_validator("due_date", "priority", mode="before")
    @classmethod
    def blank_string_to_none(cls, value: object) -> object:
        """Treat "" the same as not provided.

        HTML forms submit an empty string for a cleared date input or an
        unselected <select>, which Pydantic won't coerce to None on its own.
        """
        return None if value == "" else value


class TaskBase(TaskFields):
    """TaskFields plus a required title - the shape of a full task."""

    title: str = Field(min_length=1)


class Task(TaskBase, table=True):
    """The task table."""

    id: int | None = Field(default=None, primary_key=True)
    completed: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    source: TaskSource = TaskSource.manual


class TaskCreate(TaskBase):
    """Input schema for creating a task."""


class TaskUpdate(TaskFields):
    """Input schema for editing a task; title stays optional here so a
    partial edit is valid (see app.tasks.update_task).
    """

    title: str | None = Field(default=None, min_length=1)

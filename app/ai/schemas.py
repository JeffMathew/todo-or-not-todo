"""Plain Pydantic output schemas for AI task extraction.

Deliberately separate from the DB models (app/models.py) - see CLAUDE.md's
architecture rules on why LLM output schemas never double as DB schemas.
"""

from datetime import date

from pydantic import BaseModel

from app.models import Priority


class ExtractedTask(BaseModel):
    """One task as proposed by the LLM, before the user reviews/edits it."""

    title: str
    due_date: date | None = None
    priority: Priority | None = None


class ExtractionResult(BaseModel):
    """The tool call's top-level shape: a list of proposed tasks."""

    tasks: list[ExtractedTask]


class AssistantAnswer(BaseModel):
    """A DB-grounded answer to a question about the user's tasks.

    answer is populated only when can_answer is True; reason (what's
    missing/unclear) only when it's False. This is how "say so if unclear,
    don't guess" gets enforced structurally, rather than hoped for in prose.
    """

    can_answer: bool
    answer: str | None = None
    reason: str | None = None

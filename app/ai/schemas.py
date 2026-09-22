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

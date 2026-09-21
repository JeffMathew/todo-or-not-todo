from datetime import date

from pydantic import BaseModel

from app.models import Priority


class ExtractedTask(BaseModel):
    title: str
    due_date: date | None = None
    priority: Priority | None = None


class ExtractionResult(BaseModel):
    tasks: list[ExtractedTask]

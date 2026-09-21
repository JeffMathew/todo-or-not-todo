from datetime import date

from app.ai.schemas import ExtractedTask, ExtractionResult
from app.ai.structured_output import StructuredOutputError, get_structured_output
from app.ai.tool_calling import LLMClient

TOOL_NAME = "propose_tasks"
TOOL_DESCRIPTION = (
    "Records the structured tasks extracted from the user's freeform text."
)

TASK_EXTRACTION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short, concrete, imperative task title.",
                    },
                    "due_date": {
                        "type": "string",
                        "format": "date",
                        "description": "ISO 8601 date, if implied. Omit if unsure.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Only if urgency is explicit. Omit otherwise.",
                    },
                },
                "required": ["title"],
            },
        }
    },
    "required": ["tasks"],
}


class ExtractionError(Exception):
    pass


def _system_prompt(today: date) -> str:
    return (
        "You are a task-extraction assistant for a to-do app. Read the "
        "user's freeform note and identify each discrete, actionable task "
        "mentioned in it. For each task, write a short, concrete, "
        "imperative-style title (e.g. 'Call the dentist', not 'I need to "
        f"call the dentist'). Today's date is {today.isoformat()}. If the "
        "text states or implies a due date (e.g. 'tomorrow', 'next "
        "Friday', 'in two weeks', 'by the 5th'), resolve it to an absolute "
        "date relative to today and include it as due_date in YYYY-MM-DD "
        "format; if no date is implied for a task, omit due_date - do not "
        "guess one. Only include a priority (low, medium, or high) when "
        "the text clearly signals urgency or importance for that specific "
        "task (e.g. 'urgent', 'ASAP', 'critical' -> high; 'whenever', 'low "
        "priority', 'not important' -> low); if nothing implies a "
        "priority, omit the priority field - do not assign a default "
        "priority to every task. If the text contains no actionable "
        "tasks, call the tool with an empty tasks list. Always respond by "
        "calling the propose_tasks tool exactly once - never respond with "
        "plain text."
    )


def extract_tasks(client: LLMClient, text: str, today: date) -> list[ExtractedTask]:
    try:
        result = get_structured_output(
            client,
            output_model=ExtractionResult,
            json_schema=TASK_EXTRACTION_SCHEMA,
            tool_name=TOOL_NAME,
            tool_description=TOOL_DESCRIPTION,
            system_prompt=_system_prompt(today),
            user_message=text,
        )
    except StructuredOutputError as exc:
        raise ExtractionError(str(exc)) from exc
    return result.tasks

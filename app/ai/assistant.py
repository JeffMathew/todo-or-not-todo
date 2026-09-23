"""Task assistant: answers questions grounded only in the user's own task data.

The one module under app/ai that knows about the assistant feature - like
extract.py, everything it calls into (structured_output.py, tool_calling.py)
is generic.
"""

from datetime import date

from app.ai.schemas import AssistantAnswer
from app.ai.structured_output import StructuredOutputError, get_structured_output
from app.ai.tool_calling import LLMClient
from app.models import Task

TOOL_NAME = "answer_question"
TOOL_DESCRIPTION = (
    "Records a DB-grounded answer to the user's question about their tasks."
)

ANSWER_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "can_answer": {
            "type": "boolean",
            "description": (
                "True only if the given task data actually supports a "
                "confident answer. False if the data doesn't contain what's "
                "needed, or the question isn't about the task data at all."
            ),
        },
        "answer": {
            "type": "string",
            "description": "Required if can_answer is true, omit otherwise.",
        },
        "reason": {
            "type": "string",
            "description": (
                "What's missing or unclear. Required if can_answer is "
                "false, omit otherwise."
            ),
        },
    },
    "required": ["can_answer"],
}


class AssistantError(Exception):
    """Raised when answering fails - either the LLM call or its output shape."""


def _format_tasks(tasks: list[Task]) -> str:
    """Render the task list as plain text for the prompt.

    One line per task, every field the assistant might need to answer with -
    including completed and source, since a question could ask about either.
    """
    if not tasks:
        return "(no tasks exist yet)"
    lines = []
    for t in tasks:
        lines.append(
            f"- id={t.id}, title={t.title!r}, due_date={t.due_date or 'none'}, "
            f"priority={t.priority.value if t.priority else 'none'}, "
            f"completed={t.completed}, source={t.source.value}, "
            f"created_at={t.created_at.date().isoformat()}"
        )
    return "\n".join(lines)


def _system_prompt(tasks: list[Task], today: date) -> str:
    """Build the assistant's system prompt for a given task list and "today"."""
    return (
        "You are a task-data assistant for a to-do app. Answer the user's "
        "question using ONLY the task data listed below - never use any "
        "outside knowledge, general facts, or information from the "
        f"internet. Today is {today.strftime('%A')}, {today.isoformat()}, "
        "in case the question is date-relative (e.g. 'what's overdue', "
        "'what's due this week').\n\n"
        f"Task data:\n{_format_tasks(tasks)}\n\n"
        "If the task data actually answers the question, set can_answer to "
        "true and give a concise answer. If the task data does not contain "
        "enough information to answer confidently - including if the "
        "question isn't about these tasks at all - set can_answer to false "
        "and explain what's missing or why it can't be answered from this "
        "data. Do not guess, and do not fill gaps with general knowledge. "
        "Always respond by calling the answer_question tool exactly once - "
        "never respond with plain text."
    )


def ask_assistant(
    client: LLMClient, question: str, tasks: list[Task], today: date
) -> AssistantAnswer:
    """Answer a question grounded only in the given tasks.

    tasks and today are always passed in, never read internally, so this
    stays deterministic and testable. Raises AssistantError on any failure.
    """
    try:
        return get_structured_output(
            client,
            output_model=AssistantAnswer,
            json_schema=ANSWER_SCHEMA,
            tool_name=TOOL_NAME,
            tool_description=TOOL_DESCRIPTION,
            system_prompt=_system_prompt(tasks, today),
            user_message=question,
        )
    except StructuredOutputError as exc:
        raise AssistantError(str(exc)) from exc

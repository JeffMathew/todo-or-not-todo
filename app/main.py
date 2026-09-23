from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.datastructures import FormData

from app.ai.assistant import AssistantError, ask_assistant
from app.ai.extract import ExtractionError, extract_tasks
from app.ai.schemas import AssistantAnswer, ExtractedTask
from app.ai.tool_calling import LLMClientDep
from app.db import SessionDep, create_db_and_tables
from app.models import TaskCreate, TaskSource, TaskUpdate
from app.tasks import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    toggle_task,
    update_task,
)

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def _page_context(
    request: Request,
    session: SessionDep,
    editing_id: int | None = None,
    proposals: list[ExtractedTask] | None = None,
    error: str | None = None,
    assistant_answer: AssistantAnswer | None = None,
    assistant_error: str | None = None,
) -> dict:
    """Context shared by every template response: the current task list,
    plus whichever row is being edited, AI-review state, and/or assistant
    answer state, if any.
    """
    return {
        "request": request,
        "tasks": list_tasks(session),
        "editing_id": editing_id,
        "proposals": proposals,
        "error": error,
        "assistant_answer": assistant_answer,
        "assistant_error": assistant_error,
    }


@app.get("/")
def index(request: Request, session: SessionDep):
    """Full page load."""
    return templates.TemplateResponse(
        request, "index.html", _page_context(request, session)
    )


@app.get("/tasks")
def get_tasks(request: Request, session: SessionDep):
    """Re-render the task list with no row in edit mode - used by "Cancel"."""
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _page_context(request, session)
    )


@app.post("/tasks")
def post_task(
    request: Request, session: SessionDep, data: Annotated[TaskCreate, Form()]
):
    """Create a task from the manual-add form."""
    create_task(session, data)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _page_context(request, session)
    )


# Think of it as 'completing' a task. But we can also 'uncomplete' it. So it's a toggle.
@app.post("/tasks/{task_id}/toggle")
def toggle(request: Request, session: SessionDep, task_id: int):
    """Flip a task between complete and incomplete."""
    if toggle_task(session, task_id) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _page_context(request, session)
    )


@app.get("/tasks/{task_id}/edit")
def edit_task(request: Request, session: SessionDep, task_id: int):
    """Enter edit mode for one row."""
    if get_task(session, task_id) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_task_list.html",
        _page_context(request, session, editing_id=task_id),
    )


@app.put("/tasks/{task_id}")
def put_task(
    request: Request,
    session: SessionDep,
    task_id: int,
    data: Annotated[TaskUpdate, Form()],
):
    """Save edits to a task."""
    if update_task(session, task_id, data) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _page_context(request, session)
    )


@app.delete("/tasks/{task_id}")
def remove_task(request: Request, session: SessionDep, task_id: int):
    """Delete a task."""
    if not delete_task(session, task_id):
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _page_context(request, session)
    )


@app.post("/ai/proposals")
def create_proposals(
    request: Request,
    session: SessionDep,
    client: LLMClientDep,
    text: Annotated[str, Form(min_length=1)],
):
    """Ask the LLM to propose tasks from freeform text.

    Renders the editable review UI on success, or an inline error (still
    HTTP 200 - a valid partial showing "extraction failed" isn't a
    framework validation failure).
    """
    proposals: list[ExtractedTask] | None
    try:
        proposals = extract_tasks(client, text, today=date.today())
        error = None
    except ExtractionError as exc:
        proposals = None
        error = str(exc)
    return templates.TemplateResponse(
        request,
        "partials/_ai_review.html",
        _page_context(request, session, proposals=proposals, error=error),
    )


def _form_str(form: FormData, key: str) -> str:
    """Read a form field as plain text, defaulting to "".

    Form values are typed as str | UploadFile; this rules out the
    UploadFile case, since nothing here ever submits a file.
    """
    value = form.get(key, "")
    return value if isinstance(value, str) else ""


@app.post("/ai/proposals/confirm")
async def confirm_proposals(request: Request, session: SessionDep):
    """Save whichever proposed tasks are still checked; discard the rest.

    Proposal rows arrive as indexed form fields (title_0, due_date_0, ...)
    rather than FastAPI's usual Annotated[Model, Form()] binding, since that
    doesn't support a variable-length list of rows. Resets the review panel
    either way - nothing stays "pending".
    """
    form = await request.form()
    count = int(_form_str(form, "count") or 0)
    for i in range(count):
        if not _form_str(form, f"included_{i}"):
            continue
        try:
            data = TaskCreate.model_validate(
                {
                    "title": _form_str(form, f"title_{i}"),
                    "due_date": _form_str(form, f"due_date_{i}") or None,
                    "priority": _form_str(form, f"priority_{i}") or None,
                }
            )
        except ValidationError:
            continue
        create_task(session, data, source=TaskSource.ai)
    return templates.TemplateResponse(
        request, "partials/_app_body.html", _page_context(request, session)
    )


@app.post("/assistant/ask")
def ask(
    request: Request,
    session: SessionDep,
    client: LLMClientDep,
    question: Annotated[str, Form(min_length=1)],
):
    """Answer a question about the user's tasks, grounded only in the DB.

    Renders the answer (or an explicit "can't answer" reason) on success,
    or an inline call-failure error - still HTTP 200, same reasoning as
    /ai/proposals.
    """
    assistant_answer: AssistantAnswer | None
    try:
        assistant_answer = ask_assistant(
            client, question, list_tasks(session), today=date.today()
        )
        assistant_error = None
    except AssistantError as exc:
        assistant_answer = None
        assistant_error = str(exc)
    return templates.TemplateResponse(
        request,
        "partials/_assistant_answer.html",
        _page_context(
            request,
            session,
            assistant_answer=assistant_answer,
            assistant_error=assistant_error,
        ),
    )

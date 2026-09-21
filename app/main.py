from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.db import SessionDep, create_db_and_tables
from app.models import TaskCreate, TaskUpdate
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
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def _list_context(
    request: Request, session: SessionDep, editing_id: int | None = None
) -> dict:
    return {"request": request, "tasks": list_tasks(session), "editing_id": editing_id}


@app.get("/")
def index(request: Request, session: SessionDep):
    return templates.TemplateResponse(
        request, "index.html", _list_context(request, session)
    )


@app.get("/tasks")
def get_tasks(request: Request, session: SessionDep):
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _list_context(request, session)
    )


@app.post("/tasks")
def post_task(
    request: Request, session: SessionDep, data: Annotated[TaskCreate, Form()]
):
    create_task(session, data)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _list_context(request, session)
    )


# Think of it as 'completing' a task. But we can also 'uncomplete' it. So it's a toggle.
@app.post("/tasks/{task_id}/toggle")
def toggle(request: Request, session: SessionDep, task_id: int):
    if toggle_task(session, task_id) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _list_context(request, session)
    )


@app.get("/tasks/{task_id}/edit")
def edit_task(request: Request, session: SessionDep, task_id: int):
    if get_task(session, task_id) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request,
        "partials/_task_list.html",
        _list_context(request, session, editing_id=task_id),
    )


@app.put("/tasks/{task_id}")
def put_task(
    request: Request,
    session: SessionDep,
    task_id: int,
    data: Annotated[TaskUpdate, Form()],
):
    if update_task(session, task_id, data) is None:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _list_context(request, session)
    )


@app.delete("/tasks/{task_id}")
def remove_task(request: Request, session: SessionDep, task_id: int):
    if not delete_task(session, task_id):
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        request, "partials/_task_list.html", _list_context(request, session)
    )

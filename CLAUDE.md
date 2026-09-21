# CLAUDE.md

@SPEC.md

## Stack
Python 3.12+, uv, FastAPI, Jinja2 + HTMX, Pico CSS (CDN). SQLModel + sync
SQLite sessions, `create_all` on startup (no Alembic). Pydantic v2 +
pydantic-settings. AWS Bedrock via boto3 Converse API (forced tool use).
black + ruff (lint only) + pyright + pytest.

## Commands
- `uv run uvicorn app.main:app --reload` - run the app
- `uv run pytest` - tests
- `uv run ruff check .` - lint
- `uv run black .` - format
- `uv run pyright` - types
- `/checks` - run all of the above and summarize

## Architecture rules
- SQLModel only: `session.exec(select(...))`, never `session.query`.
- Table models are never API input; use separate Create/Update/Read models.
- LLM output schemas are plain Pydantic `BaseModel`, separate from DB models,
  always validated before use.
- DB session and LLM client are injected via FastAPI `Annotated` dependencies
  (e.g. `SessionDep`), defined once next to their `get_*` function. Never
  `= Depends(...)` as a default argument value.
- LLM client is a small `Protocol` so tests can inject a fake with no network
  calls.
- "today" is always passed in as a parameter, never read inside business
  logic.
- Routes stay thin; logic lives in modules. Calendar grid building is a pure,
  unit-testable function.
- No credentials in code, templates, or git; `.env` is gitignored.

## Definition of done
black, ruff, pyright, and pytest all pass, and the user has reviewed the diff.

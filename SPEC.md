# SPEC.md

## 1. Original brief

Pre-interview brief: small AI enabled todo app
We'd like you to build a small AI enabled todo app with one genuine AI integration, then walk us through how you built it. Budget 2 to 4 hours. The stack is up to you.
 
What we'd like you to build
The todo basics. Add a task, complete it, remove or edit it.
 
We’d also like to see one genuine AI feature. At least one real feature. Calling a hosted LLM API directly is completely fine. You don't need agents or RAG unless you want to show them off.
Pick whatever interests you. Some ideas (but you can choose your own):
Turn a freeform sentence into structured tasks
Suggest priority or due dates
Auto-categorise tasks
Summarise what's overdue
Generate subtasks
Your calls. Stack, framework, UI polish, hosting, local only or deployed. All yours.
 
What to bring
A runnable app: Local or deployed, either is fine.
The code: A repo link or a zip, something we can open before or during the interview.
Your reasoning: Why you made the choices you did, and how you used AI tools to build it.
What we're not grading
Visual design
Framework choice
Test coverage
Feature count
So please don't spend your time budget on polish. We care that the AI feature does real work and that you can talk us through your decisions.
 
In the interview
We expect you to be able to:
 
Walkthrough what you built, and how you built it
Explain your process, what you asked AI to build, where you pushed back and drove, what skills you used etc
Build a live extension, we will add a feature during the interview

## 2. Scope decisions

- Stack: Python 3.12+, uv, FastAPI, Jinja2 + HTMX (no npm/JS build step), Pico
  CSS via CDN.
- Data: SQLModel with sync sessions over SQLite; `SQLModel.metadata.create_all()`
  on startup; no Alembic/migrations.
- Config: Pydantic v2 + pydantic-settings, loaded from `.env` (gitignored).
- AI: AWS Bedrock via boto3 Converse API using forced tool use for structured
  output. Model ID and region come from env vars (`BEDROCK_MODEL_ID`,
  `AWS_REGION`) — never hardcoded or guessed. Credentials via the standard AWS
  chain.
- Tooling: black (format), ruff (lint only), pyright (types), pytest (tests).
- Task fields: id, title, due_date (optional), priority (optional:
  low/medium/high), completed, created_at, source ("manual" | "ai").
- AI extraction flow: user pastes free text -> LLM proposes structured tasks
  -> user reviews/edits/deselects them in the UI -> user confirms -> tasks are
  saved. The LLM never writes to the DB directly; all LLM output is validated
  with Pydantic before use.
- Calendar: a month grid showing which dates have tasks due; clicking a day
  shows/manages that day's tasks in a panel. Not part of the original brief
  (todo basics + one AI feature) and feature count isn't graded, so this is
  undecided for now — whether to build it as Slice 3 or treat it as a
  post-MVP / live-extension exercise gets decided when Slice 3 comes around.
- Architecture: SQLModel table models are never used as API input (separate
  Create/Update/Read models); LLM output schemas are separate plain Pydantic
  models; DB session and LLM client are injected via `Annotated` FastAPI
  dependencies; "today" is always passed in as a parameter, never read inside
  business logic; routes stay thin, logic lives in modules; calendar grid
  building is a pure, unit-testable function.
- Delivery: built in vertical slices (setup -> CRUD -> AI extraction ->
  wrap-up), each slice checked with black/ruff/pyright/pytest before commit.
  Calendar is an optional slice, decided on later (see above).

## 3. Out of scope

- Authentication / authorization / multi-user support
- Deployment (containers, CI/CD, hosting)
- Database migrations (Alembic or otherwise) - `create_all` only
- Real-time updates / websockets / polling
- Notifications, reminders, recurring tasks
- Task sharing, collaboration, comments
- Search, tags/labels beyond the fixed priority field
- Internationalization / localization
- Accessibility auditing beyond basic semantic HTML
- Visual design polish (explicitly not graded)
- Offline support / PWA
- Import/export
- Rate limiting, request throttling
- LLM cost tracking, observability, or prompt-tuning UI
- Mobile app / responsive-design guarantees beyond what Pico CSS gives for free

## 4. Future ideas (not scoped, not committed)

Calendar view stays undecided per §2 - possibly a live/rehearsed extension
exercise rather than pre-built. Two additional AI features discussed and
deferred until after Slice 4 wrap-up, both reusing the existing
`tool_calling.py`/`structured_output.py` layer from the extraction feature:

- Duplicate/similar-task detection on create (manual or AI) - flag likely
  duplicates against existing incomplete tasks before saving.
- "What should I work on next?" - suggest one task from the current
  incomplete list with a one-line reason, given title/due_date/priority as
  context (not freeform text parsing, unlike extraction - a different shape
  of structured-output problem, better reusability demonstration).

# To-Do or Not To-Do

A small to-do app with one genuine AI feature: paste a freeform note, an LLM
proposes structured tasks (title, due date, priority), you review/edit/
deselect them in the UI, and only confirmed tasks get saved.

## Stack

Python 3.12+, FastAPI, Jinja2 + HTMX (no npm, no JS build step), Pico CSS via
CDN, SQLModel over SQLite, AWS Bedrock via boto3's Converse API with forced
tool use for structured output. See `CLAUDE.md`/`SPEC.md` for the full
architecture rules and scope decisions.

## Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- **An AWS account with Bedrock model access enabled** for whichever model
  you set `BEDROCK_MODEL_ID` to. This is the one real requirement to run the
  app "off the shelf" — see [AWS / Bedrock setup and costs](#aws--bedrock-setup-and-costs)
  below before you start.

## Dev environment setup (pyenv)

This is how the project's own environment was actually set up. If you use
something other than pyenv, any Python 3.12+ interpreter works the same way.

```bash
pyenv install 3.14.3   # or any version satisfying .python-version / >=3.12
python -m venv .venv
source .venv/bin/activate
make install            # installs exactly what's pinned in uv.lock
```

## AWS / Bedrock setup and costs

- **Do not run this with AWS root account credentials.** Use a dedicated IAM
  user or role with least-privilege Bedrock access instead (this project was
  built and tested against a non-root IAM user).
- **Calling Bedrock costs real money**, per token, with no free tier. As of
  writing, the recommended model (`openai.gpt-oss-120b-1:0`, `eu-west-2`) is
  priced at approximately **$0.15 per 1M input tokens** and **$0.60 per 1M
  output tokens** (confirmed against AWS's own pricing page, not estimated —
  but this will drift over time, so check
  [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing/)
  for current rates before relying on this for budgeting). A single task
  extraction call is a few hundred tokens at most, but costs add up if you
  leave the app running and testing repeatedly.
- Credentials are picked up via the standard AWS credential chain (env vars,
  `~/.aws/credentials`, or an IAM role) - nothing app-specific to configure.

## Setup

```bash
cp .env.example .env
# fill in BEDROCK_MODEL_ID and AWS_REGION in .env
make install
```

## Running

```bash
make run
```

Then open <http://127.0.0.1:8000/>.

## Testing

```bash
make test    # or: /checks for the full black/ruff/pyright/pytest sweep
```

The test suite needs **no AWS or Bedrock access at all** - the `LLMClient`
Protocol (see below) is faked in tests with zero network calls, so you can
verify the app's correctness even without Bedrock access, though you won't
be able to exercise the live AI feature end-to-end without it.

## Extending `LLMClient` for other providers

The app only ever talks to an `LLMClient` Protocol (`app/ai/tool_calling.py`)
with one method, `call_tool(system_prompt, user_message, tool_name,
tool_description, tool_schema) -> dict`. `BedrockLLMClient` is the only
implementation shipped, but nothing else in the app (`app/ai/extract.py`,
`app/ai/structured_output.py`, the routes) depends on Bedrock specifically -
they only depend on that Protocol.

To plug in a direct integration with another provider (e.g. calling
Anthropic's or OpenAI's own API instead of going through Bedrock), implement
a new class satisfying `LLMClient` and wire it up in `get_llm_client()`
(`app/ai/tool_calling.py`).

One thing this isn't: a drop-in config toggle. AWS Bedrock's Converse API
normalizes every model it hosts (Anthropic, OpenAI's open-weight models,
others) into one consistent request/response shape, which is what lets the
current `BedrockLLMClient` work unchanged across different vendors' models
on Bedrock. A *direct* integration talks to that vendor's own native API
instead, which has its own response shape (e.g. Anthropic's and OpenAI's
native tool-calling responses are both structured differently from
Bedrock's `output.message.content[].toolUse.input`, and differently from
each other) - so each direct integration needs its own response-parsing
logic in `call_tool`, not just a new API key.

## Reasoning

For why specific choices were made (stack, scope, architecture), see
`SPEC.md`. For notes on the AI-assisted build process itself, see
`AI_LOG.md`.

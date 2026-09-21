---
name: checks
description: Run black, ruff, pyright, and pytest, and summarize pass/fail.
allowed-tools: Bash(uv run black*) Bash(uv run ruff*) Bash(uv run pyright*) Bash(uv run pytest*)
---

Run these checks in order and report a short pass/fail summary for each,
including the first failure's key error text if any check fails:

1. `uv run black --check .`
2. `uv run ruff check .`
3. `uv run pyright`
4. `uv run pytest`

# Agent Guidance

This repo is a single-agent LangGraph pipeline. Notes for AI coding assistants:

## Running tests

```bash
.venv/bin/python -m pytest tests/ -v          # all unit tests (no keys needed)
.venv/bin/python -m pytest tests/ -m smoke    # live end-to-end (needs Tavily + Bedrock)
```

## Running the agent

```bash
.venv/bin/python src/main.py --target "..." --location "..."
```

Always run from the repo root. `src/` is automatically added to `sys.path` by Python when executing `src/main.py` directly; this is why imports inside `src/` use bare names (`from graph.graph import graph`) while tests use `from src.graph.graph import graph`.

## Key files

| File | Purpose |
|------|---------|
| `src/graph/graph.py` | All node functions + graph wiring |
| `src/graph/state.py` | `AgentState` TypedDict — add new state keys here |
| `src/research/queries.py` | Search query builder |
| `src/research/search.py` | `TavilySearchProvider` + `MockSearchProvider` |
| `src/utils.py` | `slugify` for filename generation |

## Models

- **Haiku 4.5** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) — research extraction, pillar analysis. 120 s read timeout.
- **Sonnet 4.5** (`us.anthropic.claude-sonnet-4-5-20250929-v1:0`) — scope definition, synthesis, evaluation. 300 s read timeout.

Both use AWS Bedrock cross-region inference profiles (`us.*` prefix). Requires use-case form approval in the AWS Bedrock console.

## What not to change

- Do not remove `parents=True` from `mkdir` in `src/main.py` — needed for fresh clones.
- Do not widen the `except` clause in `research()` back to `Exception` — it was narrowed intentionally to surface Python bugs.
- Do not hardcode `thread_id` — it is intentionally slug+timestamp to prevent checkpoint bleed.

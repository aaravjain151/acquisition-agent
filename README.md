# Acquisition Research Agent

CLI agent that evaluates small/mid-size businesses for acquisition potential and produces a McKinsey-style report.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in AWS + Tavily keys

python src/main.py --target "Air conditioning repair services" --location "Los Angeles, CA"
```

Report is saved to `reports/YYYYMMDD_HHMM_<slug>.md` and printed to terminal.

## Pipeline

```
scope_target (Sonnet)
      │
      ▼
  research (Tavily → Haiku extraction)
      │
      ├──────────────────────────────────┐
      ▼                                  ▼
analyze_viability   analyze_buildout   analyze_profitability   analyze_competitive
      │                   │                    │                        │
      └───────────────────┴────────────────────┴────────────────────────┘
                                      │
                              synthesize_report (Sonnet)
                                      │
                                 evaluate (Sonnet)
                                      │
                                    END
```

Four analysis nodes run **in parallel** (LangGraph fan-out/fan-in). Each run gets a unique `thread_id` based on slug + timestamp so InMemorySaver checkpoints never bleed between invocations.

## Report sections

| Section | Content |
|---------|---------|
| Executive Recommendation | GO / NO-GO / PROCEED WITH CAUTION + rationale |
| Market Attractiveness | TAM, CAGR, demand drivers |
| Competitive Position | Concentration, moat, barriers to entry |
| Unit Economics | Margin model, CAC, LTV, pricing power |
| Automation Opportunity | Build cost, ROI, timeline |
| Risk Profile | Regulatory, operational, market risks |
| Acquisition Scorecard | 5–7 weighted criteria, 0–10 scale |
| Assumptions & Limitations | Data quality, recency, gaps |

## Requirements

- Python 3.12+
- AWS credentials with Bedrock access in `us-west-2`
  - `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  - `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  - Requires Anthropic use-case form approval in the AWS Bedrock console
- `TAVILY_API_KEY` for live web search — omit to run with `[SIMULATED]` fallback data

## Environment variables

Copy `.env.example` to `.env` and fill in:

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2
TAVILY_API_KEY=tvly-...
```

## Tests

```bash
pytest tests/ -v          # 26 unit tests + 1 skipped integration
pytest tests/ -m smoke    # smoke tests only (requires live keys)
```

## Project layout

```
src/
  main.py          # CLI entry point
  utils.py         # slugify
  graph/
    graph.py       # LangGraph pipeline + all node functions
    state.py       # AgentState TypedDict
  research/
    queries.py     # search query builder
    search.py      # TavilySearchProvider + MockSearchProvider
tests/
reports/           # generated reports — gitignored, not committed
```

> **Note:** `reports/` is in `.gitignore`. Generated markdown files stay local and don't travel with the repo. Commit a specific report manually if you want to share one.

## Models

| Role | Model |
|------|-------|
| Scope definition, synthesis, evaluation | Claude Sonnet 4.5 (Bedrock, 300 s timeout) |
| Research extraction, pillar analysis | Claude Haiku 4.5 (Bedrock, 120 s timeout) |

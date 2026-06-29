# Acquisition Research Agent

A CLI agent that evaluates small/mid-size businesses for acquisition potential and produces a McKinsey-style report.

## What it does

1. **Scopes the target** — Sonnet defines 5 key diligence questions for the business category
2. **Researches the market** — Tavily web search extracts structured intelligence (market size, competitors, unit economics, regulatory, CAC channels)
3. **Adaptively loops** — Haiku self-assesses data quality; if gaps exist, generates targeted follow-up queries and re-searches (up to 2 extra passes)
4. **Analyzes in parallel** — 4 Haiku nodes run simultaneously: market viability, build-out costs, profitability, competitive position
5. **Synthesizes the report** — Sonnet writes an 8-section McKinsey-style report
6. **Evaluates** — Sonnet produces a weighted scorecard and GO / NO-GO / PROCEED WITH CAUTION recommendation

Reports are saved to `reports/` as timestamped markdown files.

## Quickstart

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure API keys
cp .env.example .env
# Edit .env — add AWS credentials and TAVILY_API_KEY

# Run
python src/main.py --target "Air conditioning repair services" --location "Los Angeles, CA"
```

## Requirements

- Python 3.12+
- AWS credentials with Bedrock access (`us-west-2`)
  - Models: `us.anthropic.claude-haiku-4-5-20251001-v1:0`, `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  - Requires Anthropic use-case form approval in the AWS Bedrock console
- `TAVILY_API_KEY` for live web search (falls back to `[SIMULATED]` data if missing)

## Environment variables

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2
TAVILY_API_KEY=...
```

## Report format

Each report includes:

- **Executive Recommendation** — GO / NO-GO / PROCEED WITH CAUTION with rationale
- **Market Attractiveness** — TAM, growth rate, demand drivers
- **Competitive Position** — market concentration, moat, barriers to entry
- **Unit Economics** — margin model, CAC, LTV, pricing power
- **Automation Opportunity** — build cost, ROI, implementation timeline
- **Risk Profile** — regulatory, operational, market risks
- **Acquisition Scorecard** — 5–7 weighted criteria scored 0–10
- **Assumptions & Limitations** — data quality, recency, gaps

## Pipeline architecture

```
scope_target (Sonnet)
    │
    ▼
research (Tavily + Haiku)
    │
    ▼
assess_research (Haiku) ◄─────────────────┐
    │                                      │
    ├─ SUFFICIENT ──► start_analysis       │
    │                  ├─ analyze_viability│
    │                  ├─ analyze_buildout │  (parallel)
    │                  ├─ analyze_profit   │
    │                  └─ analyze_competitive
    │                         │
    │                  synthesize_report (Sonnet)
    │                         │
    │                    evaluate (Sonnet)
    │                         │
    │                        END
    │
    └─ INSUFFICIENT ──► refine_research (Haiku + Tavily) ─┘
                         (max 2 extra passes)
```

## Tests

```bash
pytest tests/ -v
```

## Models used

| Role | Model |
|------|-------|
| Scope, synthesis, evaluation | Claude Sonnet 4.5 (via Bedrock) |
| Research extraction, analysis, assessment | Claude Haiku 4.5 (via Bedrock) |

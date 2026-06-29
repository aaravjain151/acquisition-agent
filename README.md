# Acquisition Research Agent

CLI agent that evaluates small/mid-size businesses for acquisition potential and produces a McKinsey-style PE diligence memo — complete with investment thesis, Porter's Five Forces, normalized EBITDA model, deal structure, and weighted acquisition scorecard.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in AWS + Tavily keys

python src/main.py --target "AC repair services" --location "Los Angeles, CA"
```

Report is saved to `reports/YYYYMMDD_HHMM_<slug>.md` and printed to terminal.

## Sample Reports

Three live reports generated with real Tavily search data are in [`sample_reports/`](sample_reports/):

| Target | Location | Score | Recommendation |
|--------|----------|-------|----------------|
| [AC Repair Services](sample_reports/ac-repair-services_los-angeles-ca.md) | Los Angeles, CA | 6.2 / 10 | Proceed with Caution |
| [Commercial Cleaning Services](sample_reports/commercial-cleaning-services_denver-co.md) | Denver, CO | 5.8 / 10 | Proceed with Caution |
| [Plumbing Services](sample_reports/plumbing-services_austin-tx.md) | Austin, TX | 6.5 / 10 | Proceed with Caution |

## Pipeline

```
scope_target (Sonnet)          ← Investment thesis, bear case, 5 decision-critical
        │                         questions, KPI benchmarks, research gaps
        ▼
   research (Tavily → Haiku)   ← 10 M&A-focused queries; extracts 16-field JSON:
        │                         EBITDA multiples, M&A comps, recurring revenue %,
        │                         labor market, seasonality, gross/EBITDA margins
        │
        ├─────────────────────────────────────────────────┐
        ▼                 ▼                  ▼             ▼
  analyze_viability  analyze_buildout  analyze_profitability  analyze_competitive
  TAM/SAM, CAGR,    CapEx, key-person  Normalized P&L,       Porter's Five Forces,
  consolidation,    dependency risk,   owner add-backs,       moat rating,
  ATTRACTIVE verdict tech maturity,    revenue quality,       barrier height
                    scalability ceiling working capital
        │                 │                  │             │
        └─────────────────┴──────────────────┴─────────────┘
                                    │
                          synthesize_report (Sonnet)
                                    │
                              evaluate (Sonnet)
                                    │
                                   END
```

Four analysis nodes run **in parallel** (LangGraph fan-out/fan-in). Each run gets a unique `thread_id` based on slug + timestamp so InMemorySaver checkpoints never bleed between invocations.

## Report Sections

| # | Section | What it contains |
|---|---------|-----------------|
| 1 | Executive Recommendation | GO / PROCEED WITH CAUTION / NO-GO + 3-sentence investment thesis and primary downside risk |
| 2 | Market Attractiveness | TAM, local market size, CAGR, top demand drivers, consolidation landscape, key market risk |
| 3 | Competitive Position | Porter's Five Forces (each rated HIGH/MED/LOW), moat durability, biggest competitive threat |
| 4 | Unit Economics | Normalized EBITDA margin (PE basis after owner add-backs), revenue per technician, revenue quality, pricing power, working capital |
| 5 | Operational Profile | Business complexity, key-person dependency risk, CapEx requirements, technology maturity, scalability ceiling |
| 6 | Risk Register | Table: Risk × Severity × Likelihood × Mitigation — 4–6 named risks |
| 7 | Acquisition Scorecard | 5 criteria on 0–10 scale with weights; TOTAL WEIGHTED SCORE / 10; GO ≥7.0 / CAUTION 5.0–6.9 / NO-GO <5.0 |
| 8 | Deal Structure | Entry multiple range, earnout % and trigger metric, 3 pre-close conditions, 100-day priorities |
| 9 | Assumptions & Limitations | Data quality, key assumptions that could flip the decision, information gaps to close before LOI |

## Research Layer

Search queries are M&A-focused, not generic — examples:

- `{target} private equity acquisition EBITDA multiples recent transactions`
- `{target} recurring revenue maintenance contracts customer retention`
- `{target} technician wages labor market turnover hiring`
- `{target} regulatory licensing requirements certifications bonds`
- `{target} seasonality demand patterns cash flow`

The Haiku extraction step pulls 16 structured fields from search results: market size, CAGR, local market, top competitors, recent M&A activity, EBITDA multiples, gross/EBITDA margin ranges, revenue per employee, average job ticket, recurring revenue %, CAC channels, regulatory requirements, labor market, seasonality, and key risks.

## Requirements

- Python 3.12+
- AWS credentials with Bedrock access in `us-west-2`
  - `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  - `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  - Requires Anthropic use-case form approval in the AWS Bedrock console
- `TAVILY_API_KEY` for live web search — omit to run with `[SIMULATED]` fallback data

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2
TAVILY_API_KEY=tvly-...
```

## Tests

```bash
pytest tests/ -v          # 26 unit tests, no API keys required
pytest tests/ -m smoke    # end-to-end smoke test (requires live keys)
```

## Project Layout

```
src/
  main.py          # CLI entry point
  utils.py         # slugify for filename generation
  graph/
    graph.py       # LangGraph pipeline + all node prompts + node functions
    state.py       # AgentState TypedDict
  research/
    queries.py     # M&A-focused search query builder (10 topics)
    search.py      # TavilySearchProvider + MockSearchProvider
tests/
  test_nodes.py    # 12 unit tests (analysis nodes, scope, synthesis, slugify)
  test_research.py # 5 unit tests (success path, error paths, empty fallback)
  test_queries.py  # 6 unit tests (query builder edge cases)
  test_search.py   # 3 unit tests (MockSearchProvider)
  test_smoke.py    # end-to-end smoke test (skipped without live keys)
sample_reports/    # 3 live reports committed for reference
reports/           # generated reports — gitignored, stays local
```

## Models

| Role | Model | Timeout |
|------|-------|---------|
| Scope definition, synthesis, evaluation | Claude Sonnet 4.5 (Bedrock cross-region) | 300 s |
| Research extraction, pillar analysis (×4) | Claude Haiku 4.5 (Bedrock cross-region) | 120 s |

Both use `us.*` cross-region inference profile IDs, which require use-case form approval in the AWS Bedrock console (`us-west-2`).

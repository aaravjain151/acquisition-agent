# Acquisition Research Agent — MVP Brief

## Goal
Ship a working end-to-end agent for pre-acquisition research by tonight.

This is a **real first working agent**, not a toy. It evaluates small/mid-size businesses for acquisition potential and produces a high-quality McKinsey-style report.

## Target Demo
**Input:**
Business category: Air conditioning repair services

Location: Los Angeles, CA

**Output:**
A markdown report with executive recommendation, five analytical modules, weighted acquisition scorecard, and go/no-go decision.

## Build Priorities (in order)
1. ✅ Make the end-to-end pipeline work (Phase 1-5 nodes complete, test locally)
2. Keep architecture clean for future extension (state pattern, module isolation)
3. Do not over-engineer (no UI, no MCP complexity, no agent teams)
4. Ship with real or fallback data (Tavily if available, simulated data marked clearly)
5. Produce a real report artifact (markdown saved to `reports/`)

## MVP Requirements

### Input
- ness category (string)
- Location (string)
- Example: `python main.py --target "AC repair services" --location "Los Angeles, CA"`

### Pipeline

scope_target       → Define research questions (Sonnet)
research           → Web search or fallback data (Tavily + Haiku cleanup)
analyze_viability  → Market size, demand, growth (Haiku)
analyze_buildout   → Automation costs, complexity (Haiku)
analyze_profitability → Margin model, pricing power (Haiku)
analyze_competitive → Competitive moat, defensibility (Haiku)
synthesize_report  → McKinsey-style markdown (Sonnet)
evaluate           → Scorecard + recommendation (Sonnet)


### Report Format
- **Executive Recommendation** (go/no-go/caution with rationale)
- **Market Attractiveness** (TAM, growth, defensibility)
- **Competitive Position** (market share, differentiation, barriers)
- **Unit Economics** (margin model, CAC, LTV)
- **Automation Opportunity** (build cost, ROI, timeline)
- **Risk Profile** (regulatory, operational, market)
- **Acquisition (5-7 weighted criteria, 0-10 scale)
- **Assumptions & Limitations** (data quality, recency, gaps)

### Data Sources
- **Primary:** Tavily web search (if TAVILY_API_KEY set)
- **Fallback:** Simulated data with clear `[SIMULATED]` labels
- **Transparency:** Every fact marked real or fallback

### State Management
- Use existing `AgentState` TypedDict (already defined in `src/graph/state.py`)
- Each node returns a dict updating one or more state keys
- No external databases or caching

### Output
- Save markdown report to `reports/YYYYMMDD_HHMM_businessname_location.md`
- Include timestamp, business name, location in filename
- Print report path to terminal on completion

## Testing
- Unit tests for core node logic (at least one per module)
- Smoke test: run full pipeline with demo input, verify report is generated
- pytest must pass before shipping

## Out of Scope (Do Not Build)
- Web UI or frontend
- Persistent database
- Email delivery or distribution
- Agent-to-agent handoffs
- Browser automation
- Multi-turn conversation loop

## Implementation Rules
- First inspect current code (graph.py, state.py, main.py, tests/)
- Make smallest changes needed to ship
- Run pytest after each major change
- Ask before spending API credits (Tavily calls)
- Do not commit or push
- Do not hardcode secrets
- Keep .env in .gitignore, .env.example placeholder-only

## Definition of Done
1. ✅ Unit tests pass (pytest)
2. ✅ Smoke run completes (demo input → report generated)
3. ✅ Report saved to reports/
4. ✅ Report includes scorecard and recommendation
5. ✅ README or terminal shows exact command to reproduce
6. ✅ Final summary: what was built, what was tested, remaining gaps

## Workflow
1. Inspect existing repo and test coverage
2. Implement missing nodes (phases 2-8)
3. Add or update tests
4. Run pytest
5. Run smoke test with demo input
6. Verify report is generated
7. Summary + final command

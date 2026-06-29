from botocore.config import Config
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from research.queries import build_search_queries
from research.search import TavilySearchProvider

_haiku_config = Config(read_timeout=120, connect_timeout=10)
_sonnet_config = Config(read_timeout=300, connect_timeout=10)

llm_haiku = ChatBedrockConverse(
    model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="us-west-2",
    temperature=0,
    config=_haiku_config,
)

llm_sonnet = ChatBedrockConverse(
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-west-2",
    temperature=0,
    config=_sonnet_config,
)


# ── Node prompts ─────────────────────────────────────────────────────────────

_SCOPE_PROMPT = """\
You are a Managing Director at a top-tier private equity firm framing the research \
agenda for a potential SMB acquisition before deploying analysts. Your output will \
directly drive what gets researched.

Produce the following — be industry-specific, not generic:

## Investment Thesis
2-3 sentences: What is the bull case? What value creation levers would make this \
a 20%+ IRR acquisition?

## Bear Case
1-2 sentences: What is the single most likely reason this deal fails or \
underperforms?

## Five Decision-Critical Questions
Questions whose answers could flip the GO/NO-GO decision. Must be specific to \
this industry. BAD example: "Is the market growing?" GOOD example: \
"What % of revenue is under multi-year maintenance contracts, and what is the \
average contract renewal rate?"

## Five KPIs to Benchmark
Industry-specific metrics with their typical benchmark ranges. \
Example: "Revenue per technician: $180K–$220K/year (industry median)."

## Biggest Research Gaps
The 3 data points hardest to find from public sources but most important to the \
investment decision.
"""

_RESEARCH_EXTRACTION_PROMPT = """\
You are a research analyst at a private equity firm extracting structured \
intelligence from web search snippets for an acquisition diligence. Return ONLY \
a valid JSON object with these exact keys. Use null for any field not supported \
by the search results — do not estimate or hallucinate.

{
  "market_size_usd": "TAM in USD with year, e.g. '$4.2B in 2024'",
  "market_cagr": "projected growth rate, e.g. '6.8% CAGR 2024-2029'",
  "local_market_size": "estimated market size in the target geography, or null",
  "top_competitors": ["named competitors; include PE-backed rollups if mentioned"],
  "recent_ma_activity": "any acquisitions, consolidators, or rollup platforms in this sector",
  "typical_ebitda_multiples": "acquisition multiples for this sector, e.g. '4-7x EBITDA'",
  "gross_margin_range": "typical gross margin % for operators, e.g. '38-45%'",
  "ebitda_margin_range": "typical EBITDA margin % for operators, e.g. '12-18%'",
  "revenue_per_employee": "revenue per technician or employee per year if available",
  "avg_job_ticket": "average revenue per service call or job",
  "recurring_revenue_pct": "% of revenue from maintenance contracts or recurring work",
  "customer_acquisition_channels": ["top channels with estimated CAC if available"],
  "regulatory_requirements": ["licenses, certifications, insurance, bonds required to operate"],
  "labor_market": "technician availability, wage trends, turnover rates, union presence",
  "seasonality": "peak/off-peak demand patterns and their magnitude",
  "key_risks": ["top 2-3 sector-specific risks mentioned in the search results"]
}
"""

_VIABILITY_PROMPT = """\
You are a McKinsey senior associate writing the Market Attractiveness module for \
a PE acquisition committee memo. Use only the data provided. Where numbers are \
unavailable, say so explicitly — do not estimate.

Structure your output exactly as follows:

## Market Attractiveness Assessment
**VERDICT: ATTRACTIVE | ACCEPTABLE | UNATTRACTIVE**
One sentence justifying the verdict.

### 1. Market Size & Growth
- National TAM: [figure, year, source if known]
- Local market (target geography): [estimate with sizing methodology]
- CAGR: [rate and timeframe]
- Top 3 demand drivers: [specific, quantified where possible]
- Top 2 structural headwinds

### 2. Demand Resilience
- Recession sensitivity: [essential service or discretionary?]
- Seasonality: [peak/trough pattern, magnitude, cash flow impact]
- Secular tailwinds: [e.g. aging housing stock, climate trends, regulation]

### 3. Market Structure & Consolidation
- Fragmentation: [estimated # of operators in local market; HHI if known]
- PE / rollup activity: [named platforms, recent transactions, pace of consolidation]
- Consolidation implication: [does fragmentation create acquisition opportunity or race-to-bottom pricing?]

### 4. Local Market Specifics (target geography)
- Competitive density vs. national average
- Geography-specific demand drivers or regulatory environment

### 5. Analyst Verdict
One paragraph: Is the market large enough, resilient enough, and structurally \
attractive enough to support a 4–7× EBITDA entry with 15–20% IRR potential?
"""

_OPERATIONS_PROMPT = """\
You are a McKinsey senior associate writing the Operational Scalability & \
Integration module for a PE acquisition committee memo. This section answers: \
"How hard is this business to run, scale, and integrate — and what will it cost?"

Structure your output exactly as follows:

## Operational Scalability & Integration Assessment
**VERDICT: LOW COMPLEXITY | MODERATE COMPLEXITY | HIGH COMPLEXITY**
One sentence justifying the verdict.

### 1. Business Model Complexity
- Revenue model: [project-based, recurring contracts, emergency calls, mixed?]
- Delivery mechanism: [field technicians, routes, subcontractors, or employees?]
- Geographic footprint: [single location, multi-location, or scalable routes?]

### 2. Key Person & Owner Dependency Risk
- Typical owner role in operations: [does the owner hold key customer relationships, licenses, or technical knowledge?]
- Estimated timeline and cost to replace owner-operator with professional management
- Key person risk rating: HIGH | MEDIUM | LOW

### 3. Workforce & Labor
- Technician/labor availability in target market
- Typical turnover rate vs. industry benchmark
- Training time for new hires (weeks to productivity)
- Licensing/certification requirements per employee (time and cost)
- Labor cost as % of revenue

### 4. Technology & Systems Maturity
- Field service management software in use (e.g. ServiceTitan, Jobber, Housecall Pro)
- Scheduling, dispatch, invoicing — manual or automated?
- CRM and customer retention systems
- Technology upgrade cost estimate (if applicable)

### 5. Capital Expenditure Requirements
- Vehicle fleet: [owned/leased, replacement cycle, cost per unit]
- Equipment and tools: [owned/rented, major ticket items]
- Facilities: [owned/leased, lease terms]
- Estimated annual maintenance CapEx as % of revenue

### 6. Scalability Ceiling
- What limits growth: [technicians, geography, capital, permits?]
- Marginal cost of adding one new service route or location
- Platform vs. lifestyle business: can this scale to 3–5× revenue with proportional EBITDA expansion?

### 7. Analyst Verdict
One paragraph: How difficult and expensive is post-acquisition integration, and \
does the operational model support the scalability required for the target IRR?
"""

_PROFITABILITY_PROMPT = """\
You are a McKinsey senior associate writing the Unit Economics & Profitability \
module for a PE acquisition committee memo. This section answers: "What does the \
P&L actually look like, and what is the true normalized EBITDA a PE buyer is \
acquiring?"

Structure your output exactly as follows:

## Unit Economics & Profitability Assessment
**VERDICT: STRONG | ACCEPTABLE | WEAK**
One sentence justifying the verdict.

### 1. Normalized P&L Model
| Line Item | % of Revenue | Notes |
|-----------|-------------|-------|
| Revenue | 100% | |
| Direct Labor | ~X% | technician wages + benefits |
| Materials / Parts | ~X% | |
| Gross Profit | ~X% | |
| Vehicle / Equipment | ~X% | |
| Marketing | ~X% | |
| G&A / Admin | ~X% | |
| EBITDA (as reported) | ~X% | |
| Owner compensation add-back | +X% | salary above market replacement cost |
| Other add-backs | +X% | personal expenses, one-time items |
| **EBITDA (normalized, PE basis)** | **~X%** | **this is the number that matters** |

Note where figures are estimated vs. sourced.

### 2. Revenue Quality
- Recurring revenue %: [maintenance contracts, service agreements]
- Emergency / one-time callout %
- Average customer lifetime value
- Customer concentration: [top 3 and top 10 customers as estimated % of revenue]
- Revenue predictability: HIGH | MEDIUM | LOW

### 3. Unit Economics per Technician / per Job
- Revenue per technician (annual)
- Jobs per technician per day
- Average ticket / job value
- Gross profit per job

### 4. Pricing Power
- Evidence of ability to raise prices 3–5% annually
- Commodity pricing pressure: is this a price-taker or price-setter?
- Premium pricing enablers: brand, certifications, response time, specialization

### 5. Working Capital & Cash Conversion
- Cash conversion cycle estimate (days)
- Accounts receivable terms (B2B vs. B2C dynamics)
- Inventory / parts working capital requirement
- Seasonal cash flow stress points

### 6. Analyst Verdict
One paragraph: Do the unit economics support a 4–7× EBITDA entry multiple with \
a path to 15–20% IRR through organic growth and margin improvement?
"""

_COMPETITIVE_PROMPT = """\
You are a McKinsey senior associate writing the Competitive Position module for \
a PE acquisition committee memo using a structured Porter's Five Forces analysis. \
This section answers: "Can a skilled operator build a durable competitive \
advantage in this market, or is this a commodity business where margins are \
always competed away?"

Structure your output exactly as follows:

## Competitive Position Assessment
**VERDICT: DEFENSIBLE | MODERATE | COMMODITIZED**
One sentence justifying the verdict.

### 1. Competitive Rivalry (Intensity of existing competition)
- Number of direct competitors in local market (estimate)
- Market share concentration: [top 3 players' estimated combined share]
- Primary competitive dimensions: [price / speed / quality / brand / certifications]
- Evidence of price competition or margin erosion
- Competitive intensity rating: HIGH | MEDIUM | LOW

### 2. Threat of New Entrants (Barriers to entry)
- Capital required to start a competing operation ($)
- Licensing and certification timeline (months to become operational)
- Time to build brand/reputation sufficient to win B2B accounts
- Incumbent advantage: [customer relationships, fleet, trained workforce]
- Barrier height: HIGH | MEDIUM | LOW

### 3. Supplier Power
- Key input suppliers (equipment manufacturers, parts distributors, utilities)
- Supplier concentration and pricing leverage over operators
- Alternatives available to operators
- Supplier power rating: HIGH | MEDIUM | LOW

### 4. Buyer Power
- Customer mix: B2B (commercial) vs. B2C (residential) — which dominates?
- Switching cost for customers (ease of changing providers)
- Price sensitivity by segment
- Concentration of key accounts
- Buyer power rating: HIGH | MEDIUM | LOW

### 5. Threat of Substitutes
- Technology disruption risk (e.g. IoT sensors reducing service calls, smart systems)
- DIY substitution risk and trajectory
- Adjacent service providers expanding into this space
- Substitute threat: HIGH | MEDIUM | LOW

### 6. Moat Assessment
- What sustainable competitive advantage can a PE-backed operator build?
  (geography lock-in / long-term contracts / brand / licensed workforce / proprietary systems)
- Moat durability horizon: 1–3 yrs / 3–7 yrs / 7+ yrs
- Moat strength: STRONG | MODERATE | WEAK

### 7. Analyst Verdict
One paragraph: Given the competitive dynamics, is this a market where an \
operationally excellent acquirer can command premium pricing and fend off \
competition — or will scale advantages be competed away?
"""

_SYNTHESIS_PROMPT = """\
You are a McKinsey engagement manager writing the final pre-acquisition memo for \
a PE investment committee. Synthesize the four analytical modules below into a \
single, crisp, decision-quality document. Answer first, justify second — \
this is a McKinsey memo, not a literature review.

Write the following sections in order:

---

# [TARGET BUSINESS] — Pre-Acquisition Investment Memo

## 1. Executive Recommendation
**[GO | PROCEED WITH CAUTION | NO-GO]**
3–4 sentences: the investment thesis in plain language, the one key condition \
for proceeding, and the primary downside risk. A senior partner should be able \
to read only this section and understand the recommendation.

## 2. Market Attractiveness
- TAM, local market size, CAGR
- Top 2 demand drivers (specific, quantified)
- Consolidation landscape: fragmented / PE-active / consolidating
- 1 key market risk

## 3. Competitive Position
- Competitive intensity and moat assessment in 2–3 sentences
- Barrier height and primary moat source
- Biggest competitive threat

## 4. Unit Economics
- Normalized EBITDA margin range (PE basis, after owner add-backs)
- Revenue per technician or equivalent productivity metric
- Revenue quality: recurring % and customer concentration risk
- 1 key profitability risk

## 5. Operational Profile
- Business complexity: LOW / MODERATE / HIGH — and why in one sentence
- Key person dependency: what is at risk if the owner leaves day 1?
- Primary CapEx requirement
- Technology maturity: manual / partially automated / tech-enabled

## 6. Risk Register
| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| [Risk 1] | HIGH/MED/LOW | HIGH/MED/LOW | [Action] |
| [Risk 2] | HIGH/MED/LOW | HIGH/MED/LOW | [Action] |
| [Risk 3] | HIGH/MED/LOW | HIGH/MED/LOW | [Action] |
| [Risk 4] | HIGH/MED/LOW | HIGH/MED/LOW | [Action] |

## 7. Acquisition Scorecard
Score each criterion on 0–10 and compute the weighted total.

| Criterion | Score (0–10) | Weight | Weighted Score | Commentary |
|-----------|-------------|--------|----------------|------------|
| Market Attractiveness | X | 20% | X.X | |
| Competitive Position | X | 15% | X.X | |
| Unit Economics | X | 25% | X.X | |
| Operational Risk (inverted) | X | 25% | X.X | 10 = lowest risk |
| Scalability Potential | X | 15% | X.X | |
| **TOTAL** | | **100%** | **X.X / 10** | |

Threshold: ≥7.0 = GO · 5.0–6.9 = PROCEED WITH CAUTION · <5.0 = NO-GO

## 8. Deal Structure Recommendation
- Target entry multiple: X–Yx EBITDA (normalized)
- Suggested structure: % upfront / % earnout tied to [specific metric]
- Key pre-closing conditions (2–3 must-haves)
- 100-day priorities post-close (3 bullet points)

## 9. Assumptions & Data Limitations
- Data quality: what came from live search vs. industry estimates
- Key assumptions that could materially change the recommendation
- Information gaps that should be closed before LOI
"""

_EVALUATE_PROMPT = """\
From the acquisition memo below, extract and return ONLY the following — do not \
add commentary or new content:

**RECOMMENDATION:** GO | PROCEED WITH CAUTION | NO-GO

**TOTAL WEIGHTED SCORE:** X.X / 10

**SCORECARD:**
[Copy the scorecard table verbatim from the memo]

**TOP 3 RISKS:**
1.
2.
3.

**TOP 3 VALUE-CREATION LEVERS:**
1.
2.
3.

**DEAL STRUCTURE SUMMARY:**
[Copy the deal structure section verbatim from the memo, or state "Not included" if absent]
"""


# ── Node functions ────────────────────────────────────────────────────────────

def scope_target(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content=_SCOPE_PROMPT),
        HumanMessage(content=f"Target business: {state['target']}"),
    ])
    return {"scope": resp.content}


def research(state: AgentState) -> dict:
    try:
        search = TavilySearchProvider()
        queries = build_search_queries(state["target"], scope=state.get("scope", ""))
        raw_snippets = []
        for query in queries:
            for r in search.search(query, max_results=3):
                snippet = r.snippet[:400].strip()
                if snippet:
                    raw_snippets.append(f"[{r.title}] {snippet}")
        if not raw_snippets:
            return {"research": "[SIMULATED] No search results returned. Using fallback data."}
        combined = "\n\n".join(raw_snippets)
        resp = llm_haiku.invoke([
            SystemMessage(content=_RESEARCH_EXTRACTION_PROMPT),
            HumanMessage(content=f"Target: {state['target']}\n\nSearch results:\n{combined}"),
        ])
        return {"research": resp.content}
    except (ValueError, RuntimeError, ConnectionError, OSError) as e:
        return {"research": f"[SIMULATED] Market research unavailable ({e}). Using fallback data."}


def analyze_viability(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content=_VIABILITY_PROMPT),
        HumanMessage(content=(
            f"Target: {state['target']}\n"
            f"Investment thesis & diligence questions:\n{state.get('scope', '')}\n\n"
            f"Research data:\n{state.get('research', '')}"
        )),
    ])
    return {"viability": resp.content}


def analyze_buildout(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content=_OPERATIONS_PROMPT),
        HumanMessage(content=(
            f"Target: {state['target']}\n"
            f"Investment thesis & diligence questions:\n{state.get('scope', '')}\n\n"
            f"Research data:\n{state.get('research', '')}"
        )),
    ])
    return {"buildout_costs": resp.content}


def analyze_profitability(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content=_PROFITABILITY_PROMPT),
        HumanMessage(content=(
            f"Target: {state['target']}\n"
            f"Investment thesis & diligence questions:\n{state.get('scope', '')}\n\n"
            f"Research data:\n{state.get('research', '')}"
        )),
    ])
    return {"profitability": resp.content}


def analyze_competitive(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content=_COMPETITIVE_PROMPT),
        HumanMessage(content=(
            f"Target: {state['target']}\n"
            f"Investment thesis & diligence questions:\n{state.get('scope', '')}\n\n"
            f"Research data:\n{state.get('research', '')}"
        )),
    ])
    return {"competitive_advantage": resp.content}


_PILLAR_CAP = 3500  # chars per pillar — keeps synthesis prompt under ~18k tokens


def synthesize_report(state: AgentState) -> dict:
    def cap(text: str) -> str:
        return text[:_PILLAR_CAP] + ("…" if len(text) > _PILLAR_CAP else "")

    resp = llm_sonnet.invoke([
        SystemMessage(content=_SYNTHESIS_PROMPT),
        HumanMessage(content=(
            f"Target: {state['target']}\n\n"
            f"--- MARKET ATTRACTIVENESS MODULE ---\n{cap(state['viability'])}\n\n"
            f"--- OPERATIONAL SCALABILITY MODULE ---\n{cap(state['buildout_costs'])}\n\n"
            f"--- UNIT ECONOMICS MODULE ---\n{cap(state['profitability'])}\n\n"
            f"--- COMPETITIVE POSITION MODULE ---\n{cap(state['competitive_advantage'])}"
        )),
    ])
    return {"report": resp.content}


def evaluate(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content=_EVALUATE_PROMPT),
        HumanMessage(content=f"Acquisition memo:\n{state['report']}"),
    ])
    return {"evaluation": resp.content}


# ── Build graph ──────────────────────────────────────────────────────────────

builder = StateGraph(AgentState)

for name, fn in [
    ("scope_target", scope_target),
    ("research", research),
    ("analyze_viability", analyze_viability),
    ("analyze_buildout", analyze_buildout),
    ("analyze_profitability", analyze_profitability),
    ("analyze_competitive", analyze_competitive),
    ("synthesize_report", synthesize_report),
    ("evaluate", evaluate),
]:
    builder.add_node(name, fn)

builder.add_edge(START, "scope_target")
builder.add_edge("scope_target", "research")

# Fan-out: all 4 pillars run in parallel after research
builder.add_edge("research", "analyze_viability")
builder.add_edge("research", "analyze_buildout")
builder.add_edge("research", "analyze_profitability")
builder.add_edge("research", "analyze_competitive")

# Fan-in: synthesize waits for all 4 pillars
builder.add_edge("analyze_viability", "synthesize_report")
builder.add_edge("analyze_buildout", "synthesize_report")
builder.add_edge("analyze_profitability", "synthesize_report")
builder.add_edge("analyze_competitive", "synthesize_report")

builder.add_edge("synthesize_report", "evaluate")
builder.add_edge("evaluate", END)

graph = builder.compile(checkpointer=InMemorySaver())

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from botocore.config import Config
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state import AgentState
from research.queries import build_search_queries
from research.search import TavilySearchProvider

_boto_config = Config(read_timeout=120, connect_timeout=10)

llm_haiku = ChatBedrockConverse(
    model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="us-west-2",
    temperature=0,
    config=_boto_config,
)

llm_sonnet = ChatBedrockConverse(
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-west-2",
    temperature=0,
    config=_boto_config,
)


def scope_target(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content="You are a pre-acquisition research lead. Be concrete and skeptical."),
        HumanMessage(content=f"Target: {state['target']}\n\nDefine research scope and 5 key diligence questions."),
    ])
    return {"scope": resp.content}


_RESEARCH_EXTRACTION_PROMPT = """\
You are extracting structured market intelligence from raw web search snippets.
Return ONLY a concise JSON object with these keys:
- market_size: estimated market size and growth rate (string or null)
- top_players: list of up to 5 named competitors
- unit_economics: gross margin range or revenue-per-job estimates (string or null)
- regulatory: key licenses, certifications, or compliance requirements (list of strings)
- cac_channels: top customer acquisition channels (list of strings)

Be specific. Use numbers when present. Null when not found.
"""


def _run_searches(queries: list[str]) -> str:
    search = TavilySearchProvider()
    snippets = []
    for query in queries:
        for r in search.search(query, max_results=3):
            snippet = r.snippet[:300].strip()
            if snippet:
                snippets.append(f"[{r.title}] {snippet}")
    return "\n\n".join(snippets)


def research(state: AgentState) -> dict:
    try:
        queries = build_search_queries(state["target"], scope=state.get("scope", ""))
        combined = _run_searches(queries)
        resp = llm_haiku.invoke([
            SystemMessage(content=_RESEARCH_EXTRACTION_PROMPT),
            HumanMessage(content=f"Target: {state['target']}\n\nSearch results:\n{combined}"),
        ])
        return {"research": resp.content, "research_iterations": 0}
    except Exception as e:
        return {
            "research": f"[SIMULATED] Market research unavailable ({e}). Using fallback data.",
            "research_iterations": 0,
        }


_QUALITY_ASSESSMENT_PROMPT = """\
You are a due-diligence quality assessor. Given the research collected so far and the diligence \
scope, decide if the data is sufficient to support a credible acquisition analysis.

Reply with EXACTLY one of these two prefixes, followed by a brief explanation (≤2 sentences):
  SUFFICIENT: <explanation>
  INSUFFICIENT: <explanation listing specific missing data points>

Be strict but fair — only say INSUFFICIENT if important diligence areas are genuinely uncovered.
"""


def assess_research(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content=_QUALITY_ASSESSMENT_PROMPT),
        HumanMessage(
            content=(
                f"Target: {state['target']}\n"
                f"Scope / diligence questions:\n{state.get('scope', '')}\n\n"
                f"Research collected so far:\n{state.get('research', '')}"
            )
        ),
    ])
    quality = resp.content.strip()
    iteration = state.get("research_iterations", 0)
    verdict = "SUFFICIENT" if quality.upper().startswith("SUFFICIENT") else "INSUFFICIENT"
    print(f"\n[Research loop] Iteration {iteration} — {verdict}: {quality[:120]}...")
    return {"research_quality": quality}


def refine_research(state: AgentState) -> dict:
    """Generate gap-filling queries and append results to existing research."""
    gap_resp = llm_haiku.invoke([
        SystemMessage(content="Generate exactly 3 targeted web search queries to fill the identified data gaps. Return only the queries, one per line, no numbering."),
        HumanMessage(
            content=(
                f"Target: {state['target']}\n"
                f"Gaps identified: {state.get('research_quality', '')}\n"
                f"Existing research:\n{state.get('research', '')}"
            )
        ),
    ])
    queries = [q.strip() for q in gap_resp.content.strip().splitlines() if q.strip()][:3]
    iteration = state.get("research_iterations", 0) + 1
    print(f"\n[Research loop] Refining with {len(queries)} gap-filling queries (iteration {iteration})...")

    try:
        new_snippets = _run_searches(queries)
        merged = (
            state.get("research", "")
            + f"\n\n--- ADDITIONAL RESEARCH (iteration {iteration}) ---\n\n"
            + new_snippets
        )
    except Exception as e:
        merged = state.get("research", "") + f"\n\n[Refinement failed: {e}]"

    return {"research": merged, "research_iterations": iteration}


def start_analysis(state: AgentState) -> dict:
    """No-op pass-through that enables fan-out from conditional edge."""
    return {}


def analyze_viability(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess market viability: size, demand, concentration, stability."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state['scope']}\nResearch: {state['research']}"),
    ])
    return {"viability": resp.content}


def analyze_buildout(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess automation investment, tech stack, process documentation, scaling."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state['scope']}\nResearch: {state['research']}"),
    ])
    return {"buildout_costs": resp.content}


def analyze_profitability(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess margins, CAC, LTV, pricing power, scalability."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state['scope']}\nResearch: {state['research']}"),
    ])
    return {"profitability": resp.content}


def analyze_competitive(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess competitive moat, market concentration, brand strength, barriers."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state['scope']}\nResearch: {state['research']}"),
    ])
    return {"competitive_advantage": resp.content}


def synthesize_report(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content="Write McKinsey-style report: Executive Rec, Market, Competition, Economics, Automation, Risk, Scorecard, Assumptions."),
        HumanMessage(content=f"Target: {state['target']}\n\nViability:\n{state['viability']}\n\nBuild-out:\n{state['buildout_costs']}\n\nProfitability:\n{state['profitability']}\n\nCompetitive:\n{state['competitive_advantage']}"),
    ])
    return {"report": resp.content}


def evaluate(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content="Extract scorecard and final recommendation: GO / NO-GO / PROCEED_WITH_CAUTION."),
        HumanMessage(content=f"Report:\n{state['report']}"),
    ])
    return {"evaluation": resp.content}


def _route_after_assessment(state: AgentState) -> str:
    iterations = state.get("research_iterations", 0)
    quality = state.get("research_quality", "")
    if iterations >= 2 or quality.upper().startswith("SUFFICIENT"):
        return "proceed"
    return "loop"


# ── Build graph ──────────────────────────────────────────────────────────────

builder = StateGraph(AgentState)

for name, fn in [
    ("scope_target", scope_target),
    ("research", research),
    ("assess_research", assess_research),
    ("refine_research", refine_research),
    ("start_analysis", start_analysis),
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
builder.add_edge("research", "assess_research")

# Adaptive loop: refine and re-assess, or proceed to fan-out
builder.add_conditional_edges(
    "assess_research",
    _route_after_assessment,
    {"proceed": "start_analysis", "loop": "refine_research"},
)
builder.add_edge("refine_research", "assess_research")

# Fan-out: all 4 pillars run in parallel from start_analysis
builder.add_edge("start_analysis", "analyze_viability")
builder.add_edge("start_analysis", "analyze_buildout")
builder.add_edge("start_analysis", "analyze_profitability")
builder.add_edge("start_analysis", "analyze_competitive")

# Fan-in: synthesize waits for all 4 pillars
builder.add_edge("analyze_viability", "synthesize_report")
builder.add_edge("analyze_buildout", "synthesize_report")
builder.add_edge("analyze_profitability", "synthesize_report")
builder.add_edge("analyze_competitive", "synthesize_report")

builder.add_edge("synthesize_report", "evaluate")
builder.add_edge("evaluate", END)

graph = builder.compile(checkpointer=InMemorySaver())

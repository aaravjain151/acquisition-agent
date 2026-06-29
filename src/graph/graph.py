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


def research(state: AgentState) -> dict:
    try:
        search = TavilySearchProvider()
        queries = build_search_queries(state["target"], scope=state.get("scope", ""))
        raw_snippets = []
        for query in queries:
            for r in search.search(query, max_results=3):
                snippet = r.snippet[:300].strip()
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
        SystemMessage(content="Assess market viability: size, demand, concentration, stability."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state.get('scope', '')}\nResearch: {state.get('research', '')}"),
    ])
    return {"viability": resp.content}


def analyze_buildout(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess automation investment, tech stack, process documentation, scaling."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state.get('scope', '')}\nResearch: {state.get('research', '')}"),
    ])
    return {"buildout_costs": resp.content}


def analyze_profitability(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess margins, CAC, LTV, pricing power, scalability."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state.get('scope', '')}\nResearch: {state.get('research', '')}"),
    ])
    return {"profitability": resp.content}


def analyze_competitive(state: AgentState) -> dict:
    resp = llm_haiku.invoke([
        SystemMessage(content="Assess competitive moat, market concentration, brand strength, barriers."),
        HumanMessage(content=f"Target: {state['target']}\nScope: {state.get('scope', '')}\nResearch: {state.get('research', '')}"),
    ])
    return {"competitive_advantage": resp.content}


_PILLAR_CAP = 3000  # chars — keeps synthesis prompt under ~16k tokens total


def synthesize_report(state: AgentState) -> dict:
    def cap(text: str) -> str:
        return text[:_PILLAR_CAP] + ("…" if len(text) > _PILLAR_CAP else "")

    resp = llm_sonnet.invoke([
        SystemMessage(content="Write McKinsey-style report: Executive Rec, Market, Competition, Economics, Automation, Risk, Scorecard, Assumptions."),
        HumanMessage(content=(
            f"Target: {state['target']}\n\n"
            f"Viability:\n{cap(state['viability'])}\n\n"
            f"Build-out:\n{cap(state['buildout_costs'])}\n\n"
            f"Profitability:\n{cap(state['profitability'])}\n\n"
            f"Competitive:\n{cap(state['competitive_advantage'])}"
        )),
    ])
    return {"report": resp.content}


def evaluate(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content="Extract scorecard and final recommendation: GO / NO-GO / PROCEED_WITH_CAUTION."),
        HumanMessage(content=f"Report:\n{state['report']}"),
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

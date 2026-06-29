from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState

# Three separate LLM instances
llm_haiku = ChatBedrockConverse(
    model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="us-west-2",
    temperature=0,
)

llm_sonnet = ChatBedrockConverse(
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="us-west-2",
    temperature=0,
)

# --- REAL node (today) ---
def scope_target(state: AgentState) -> dict:
    resp = llm_sonnet.invoke([
        SystemMessage(content=(
            "You are a pre-acquisition research lead at a firm that buys "
            "small/mid-size businesses and automates them. Be concrete and skeptical."
        )),
        HumanMessage(content=(
            f"Target: {state['target']}\n\n"
            "Define the research scope: industry, geography, business model, "
            "and the 5 key questions a McKinsey-style diligence report must answer."
        )),
    ])
    return {"scope": resp.content}

# --- STUBS (filled in later phases) ---
def research(state: AgentState) -> dict:
    # Phase 2: will use Haiku for cleanup/extraction
    return {"research": "[stub] market data goes here (phase 2 - Haiku cleanup)"}

def analyze_viability(state: AgentState) -> dict:
    # Phase 3: will use Haiku for module summaries
    return {"viability": "[stub] Haiku module summary"}

def analyze_buildout(state: AgentState) -> dict:
    # Phase 3: will use Haiku for module summaries
    return {"buildout_costs": "[stub] Haiku module summary"}

def analyze_profitability(state: AgentState) -> dict:
    # Phase 3: will use Haiku for module summaries
    return {"profitability": "[stub] Haiku module summary"}

def analyze_competitive(state: AgentState) -> dict:
    # Phase 3: will use Haiku for module summaries
    return {"competitive_advantage": "[stub] Haiku module summary"}

def synthesize_report(state: AgentState) -> dict:
    # Phase 5: uses Sonnet for final synthesis
    return {"report": "[stub] McKinsey-style report synthesized by Sonnet (phase 5)"}

# --- wire it up (linear for now; we parallelize the pillars in phase 4) ---
builder = StateGraph(AgentState)
for name, fn in [
    ("scope_target", scope_target),
    ("research", research),
    ("analyze_viability", analyze_viability),
    ("analyze_buildout", analyze_buildout),
    ("analyze_profitability", analyze_profitability),
    ("analyze_competitive", analyze_competitive),
    ("synthesize_report", synthesize_report),
]:
    builder.add_node(name, fn)

builder.add_edge(START, "scope_target")
builder.add_edge("scope_target", "research")
builder.add_edge("research", "analyze_viability")
builder.add_edge("analyze_viability", "analyze_buildout")
builder.add_edge("analyze_buildout", "analyze_profitability")
builder.add_edge("analyze_profitability", "analyze_competitive")
builder.add_edge("analyze_competitive", "synthesize_report")
builder.add_edge("synthesize_report", END)

graph = builder.compile(checkpointer=InMemorySaver())

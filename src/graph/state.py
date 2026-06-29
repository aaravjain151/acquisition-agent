from typing import TypedDict

class AgentState(TypedDict):
    target: str
    scope: str
    research: str
    research_quality: str   # "SUFFICIENT: ..." or "INSUFFICIENT: ..."
    research_iterations: int
    viability: str
    buildout_costs: str
    profitability: str
    competitive_advantage: str
    report: str
    evaluation: str
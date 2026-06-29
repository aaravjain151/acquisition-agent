from typing import TypedDict

class AgentState(TypedDict):
    target: str                  # raw input: "AC repair services in Los Angeles, CA"
    scope: str                   # scope_target writes this (real today)
    research: str                # phase 2
    viability: str               # phase 3
    buildout_costs: str          # phase 3
    profitability: str           # phase 3
    competitive_advantage: str   # phase 3
    report: str                  # phase 5

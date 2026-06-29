RESEARCH_TOPICS = (
    "market size revenue growth CAGR forecast",
    "private equity acquisition EBITDA multiples recent transactions",
    "gross margin EBITDA profitability benchmarks operators",
    "top competitors market share fragmentation rollup platforms",
    "recurring revenue maintenance contracts customer retention",
    "technician wages labor market turnover hiring",
    "regulatory licensing requirements certifications bonds",
    "customer acquisition cost marketing channels",
    "seasonality demand patterns cash flow",
    "industry risks technology disruption consolidation trends",
)


def build_search_queries(
    target: str,
    scope: str = "",
    *,
    max_queries: int = 5,
) -> list[str]:
    """Build M&A diligence-oriented web search queries from the acquisition target."""
    base = target.strip()
    if not base:
        raise ValueError("target must be a non-empty string")

    if scope.strip():
        # Reserve one slot for the authoritative-source query; it always wins over topics.
        topics_limit = max(0, max_queries - 1)
        queries = [f"{base} {topic}" for topic in RESEARCH_TOPICS[:topics_limit]]
        queries.append(f"{base} industry report site:.gov OR site:.edu OR site:.ibisworld.com")
    else:
        queries = [f"{base} {topic}" for topic in RESEARCH_TOPICS[:max_queries]]

    return queries[:max_queries]

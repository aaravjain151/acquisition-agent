RESEARCH_TOPICS = (
    "market size and growth trends",
    "top competitors and market fragmentation",
    "unit economics and gross margins",
    "regulatory and licensing requirements",
    "customer acquisition channels and costs",
)


def build_search_queries(
    target: str,
    scope: str = "",
    *,
    max_queries: int = 5,
) -> list[str]:
    """Build diligence-oriented web search queries from the acquisition target."""
    base = target.strip()
    if not base:
        raise ValueError("target must be a non-empty string")

    if scope.strip():
        # Reserve one slot for the authoritative-source query; it always wins over topics.
        topics_limit = max(0, max_queries - 1)
        queries = [f"{base} {topic}" for topic in RESEARCH_TOPICS[:topics_limit]]
        queries.append(f"{base} industry outlook site:.gov OR site:.edu")
    else:
        queries = [f"{base} {topic}" for topic in RESEARCH_TOPICS[:max_queries]]

    return queries[:max_queries]

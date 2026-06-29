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

    topics_limit = max_queries
    if scope.strip():
        topics_limit = max(1, max_queries - 1)

    queries = [f"{base} {topic}" for topic in RESEARCH_TOPICS[:topics_limit]]

    if scope.strip():
        queries.append(f"{base} industry outlook site:.gov OR site:.edu")

    return queries[:max_queries]

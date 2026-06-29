import pytest

from research.queries import RESEARCH_TOPICS, build_search_queries


TARGET = "Air conditioning repair services in Los Angeles, CA"


def test_build_search_queries_returns_diligence_topics():
    queries = build_search_queries(TARGET)

    assert len(queries) == len(RESEARCH_TOPICS)
    assert all(TARGET in query for query in queries)
    assert queries[0].endswith(RESEARCH_TOPICS[0])


def test_build_search_queries_respects_max_queries():
    queries = build_search_queries(TARGET, max_queries=2)

    assert len(queries) == 2
    assert queries[1].endswith(RESEARCH_TOPICS[1])


def test_build_search_queries_adds_authoritative_source_query_when_scope_present():
    queries = build_search_queries(TARGET, scope="NAICS 238220 HVAC contractors")

    assert any("site:.gov OR site:.edu" in query for query in queries)


def test_build_search_queries_rejects_empty_target():
    with pytest.raises(ValueError, match="non-empty"):
        build_search_queries("   ")

from research.search import MockSearchProvider, SearchResult


def test_mock_search_provider_returns_configured_results():
    result = SearchResult(
        title="LA HVAC market report",
        url="https://example.com/report",
        snippet="Fragmented market with 2,400 licensed contractors.",
    )
    provider = MockSearchProvider(
        {"AC repair Los Angeles market size": [result]},
    )

    hits = provider.search("AC repair Los Angeles market size")

    assert hits == [result]


def test_mock_search_provider_limits_results():
    results = [
        SearchResult(title=f"Hit {i}", url=f"https://example.com/{i}", snippet="...")
        for i in range(5)
    ]
    provider = MockSearchProvider({"query": results})

    hits = provider.search("query", max_results=2)

    assert len(hits) == 2


def test_mock_search_provider_returns_empty_for_unknown_query():
    provider = MockSearchProvider()

    assert provider.search("unknown query") == []

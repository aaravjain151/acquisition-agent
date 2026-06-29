from dataclasses import dataclass
from typing import Protocol
import os


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        ...


class MockSearchProvider:
    """In-memory search provider for tests and offline development."""

    def __init__(self, results_by_query: dict[str, list[SearchResult]] | None = None):
        self._results_by_query = results_by_query or {}

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        results = self._results_by_query.get(query, [])
        return results[:max_results]


class TavilySearchProvider:
    """Live search provider backed by the Tavily API."""

    def __init__(self, api_key: str | None = None):
        from tavily import TavilyClient
        key = api_key or os.environ.get("TAVILY_API_KEY")
        if not key:
            raise ValueError("TAVILY_API_KEY must be set in env or passed explicitly")
        self._client = TavilyClient(api_key=key)

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        response = self._client.search(query, max_results=max_results)
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
            )
            for r in response.get("results", [])
        ]

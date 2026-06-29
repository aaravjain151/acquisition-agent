from dataclasses import dataclass
from typing import Protocol


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

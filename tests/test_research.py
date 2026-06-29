import unittest
from unittest.mock import patch, MagicMock
from src.graph.graph import research

_STATE = {
    "target": "AC repair services in Los Angeles, CA",
    "scope": "Assess market size, competitors, and unit economics.",
    "research": "",
    "viability": "",
    "buildout_costs": "",
    "profitability": "",
    "competitive_advantage": "",
    "report": "",
    "evaluation": "",
}


class TestResearchNode(unittest.TestCase):

    def _make_mock_search(self, snippets=None):
        from research.search import SearchResult
        mock_provider = MagicMock()
        mock_provider.search.return_value = [
            SearchResult(
                title="HVAC Market Report",
                url="https://example.com/hvac",
                snippet=snippets or "AC repair market worth $15B, growing 6% YoY.",
            )
        ]
        return mock_provider

    def test_success_path_populates_research_key(self):
        """Happy path: Tavily returns results, Haiku extracts structured JSON."""
        mock_search = self._make_mock_search()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = (
            '{"market_size": "$15B", "top_players": ["ARS", "One Hour"], '
            '"unit_economics": "40% gross margin", "regulatory": ["EPA 608"], '
            '"cac_channels": ["Google Ads", "Angi"]}'
        )

        with patch("src.graph.graph.TavilySearchProvider", return_value=mock_search), \
             patch("src.graph.graph.llm_haiku", mock_llm):
            result = research(_STATE)

        self.assertIn("research", result)
        self.assertIn("market_size", result["research"])

    def test_success_path_calls_haiku_with_search_results(self):
        """Haiku.invoke is called exactly once with the combined snippets."""
        mock_search = self._make_mock_search("Fragmented market, 2,400 contractors in LA.")
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = '{"market_size": "large"}'

        with patch("src.graph.graph.TavilySearchProvider", return_value=mock_search), \
             patch("src.graph.graph.llm_haiku", mock_llm):
            research(_STATE)

        mock_llm.invoke.assert_called_once()
        call_messages = mock_llm.invoke.call_args[0][0]
        combined_text = " ".join(m.content for m in call_messages)
        self.assertIn("Fragmented market", combined_text)

    def test_fallback_path_on_tavily_error(self):
        """When Tavily raises, research returns [SIMULATED] fallback, not an exception."""
        mock_llm = MagicMock()

        with patch("src.graph.graph.TavilySearchProvider", side_effect=ValueError("TAVILY_API_KEY must be set")), \
             patch("src.graph.graph.llm_haiku", mock_llm):
            result = research(_STATE)

        self.assertIn("research", result)
        self.assertIn("[SIMULATED]", result["research"])
        mock_llm.invoke.assert_not_called()

    def test_fallback_path_on_haiku_error(self):
        """When Haiku raises after search succeeds, result still falls back gracefully."""
        mock_search = self._make_mock_search()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("Bedrock timeout")

        with patch("src.graph.graph.TavilySearchProvider", return_value=mock_search), \
             patch("src.graph.graph.llm_haiku", mock_llm):
            result = research(_STATE)

        self.assertIn("research", result)
        self.assertIn("[SIMULATED]", result["research"])

    def test_empty_snippets_returns_simulated_fallback(self):
        """When Tavily returns results but all snippets are empty, fall back rather than calling Haiku with nothing."""
        from research.search import SearchResult
        mock_provider = MagicMock()
        mock_provider.search.return_value = [
            SearchResult(title="Empty", url="https://example.com", snippet="   ")
        ]
        mock_llm = MagicMock()

        with patch("src.graph.graph.TavilySearchProvider", return_value=mock_provider), \
             patch("src.graph.graph.llm_haiku", mock_llm):
            result = research(_STATE)

        self.assertIn("[SIMULATED]", result["research"])
        mock_llm.invoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
from src.graph.graph import (
    analyze_viability, analyze_buildout, analyze_profitability,
    analyze_competitive, synthesize_report, evaluate,
    assess_research, refine_research,
)

_BASE_STATE = {
    "target": "AC repair in LA",
    "scope": "Test scope. Diligence questions: market size? competitors? margins?",
    "research": '{"market_size": "$5B", "top_players": ["ServiceTitan", "Aire"], "unit_economics": "40% gross margin", "regulatory": ["EPA 608"], "cac_channels": ["Google Ads"]}',
    "research_quality": "",
    "research_iterations": 0,
    "viability": "",
    "buildout_costs": "",
    "profitability": "",
    "competitive_advantage": "",
    "report": "",
    "evaluation": "",
}


class TestAnalysisNodes(unittest.TestCase):

    def test_analyze_viability(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Viability assessment"
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = analyze_viability(_BASE_STATE)
        self.assertIn("viability", result)
        self.assertEqual(result["viability"], "Viability assessment")
        mock_llm.invoke.assert_called_once()

    def test_analyze_buildout(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Build-out assessment"
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = analyze_buildout(_BASE_STATE)
        self.assertIn("buildout_costs", result)
        self.assertEqual(result["buildout_costs"], "Build-out assessment")

    def test_analyze_profitability(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Profitability assessment"
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = analyze_profitability(_BASE_STATE)
        self.assertIn("profitability", result)
        self.assertEqual(result["profitability"], "Profitability assessment")

    def test_analyze_competitive(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Competitive assessment"
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = analyze_competitive(_BASE_STATE)
        self.assertIn("competitive_advantage", result)

    def test_synthesize_report(self):
        state = {**_BASE_STATE, "viability": "Viability", "buildout_costs": "Costs",
                 "profitability": "Profit", "competitive_advantage": "Competitive"}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "# McKinsey Report\n\nExecutive recommendation: GO"
        with patch('src.graph.graph.llm_sonnet', mock_llm):
            result = synthesize_report(state)
        self.assertIn("report", result)
        self.assertIn("McKinsey", result["report"])

    def test_evaluate(self):
        state = {**_BASE_STATE, "report": "Full report text with scorecard"}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "GO — Score: 4.1/5"
        with patch('src.graph.graph.llm_sonnet', mock_llm):
            result = evaluate(state)
        self.assertIn("evaluation", result)
        self.assertIn("GO", result["evaluation"])


class TestAdaptiveResearchLoop(unittest.TestCase):

    def test_assess_research_sufficient(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "SUFFICIENT: Data covers market size, competitors, and margins adequately."
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = assess_research(_BASE_STATE)
        self.assertIn("research_quality", result)
        self.assertTrue(result["research_quality"].startswith("SUFFICIENT"))

    def test_assess_research_insufficient(self):
        sparse_state = {**_BASE_STATE, "research": "Limited data available."}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "INSUFFICIENT: Missing unit economics and regulatory data."
        with patch('src.graph.graph.llm_haiku', mock_llm):
            result = assess_research(sparse_state)
        self.assertIn("research_quality", result)
        self.assertTrue(result["research_quality"].startswith("INSUFFICIENT"))

    def test_refine_research_appends_data(self):
        insufficient_state = {
            **_BASE_STATE,
            "research": "Initial sparse research.",
            "research_quality": "INSUFFICIENT: Missing unit economics.",
            "research_iterations": 0,
        }
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "AC repair profit margins Los Angeles\nHVAC technician salary California\nAC service pricing 2024"

        mock_search = MagicMock()
        from research.search import SearchResult
        mock_search.search.return_value = [
            SearchResult(title="AC margins", url="http://example.com", snippet="HVAC gross margin 35-45%")
        ]
        with patch('src.graph.graph.llm_haiku', mock_llm), \
             patch('src.graph.graph.TavilySearchProvider', return_value=mock_search):
            result = refine_research(insufficient_state)

        self.assertIn("research", result)
        self.assertIn("ADDITIONAL RESEARCH", result["research"])
        self.assertEqual(result["research_iterations"], 1)

    def test_route_exits_after_max_iterations(self):
        from src.graph.graph import _route_after_assessment
        state = {
            **_BASE_STATE,
            "research_quality": "INSUFFICIENT: Still missing data.",
            "research_iterations": 2,
        }
        self.assertEqual(_route_after_assessment(state), "proceed")

    def test_route_loops_when_insufficient(self):
        from src.graph.graph import _route_after_assessment
        state = {
            **_BASE_STATE,
            "research_quality": "INSUFFICIENT: Missing key data.",
            "research_iterations": 0,
        }
        self.assertEqual(_route_after_assessment(state), "loop")

    def test_route_proceeds_when_sufficient(self):
        from src.graph.graph import _route_after_assessment
        state = {
            **_BASE_STATE,
            "research_quality": "SUFFICIENT: All key areas covered.",
            "research_iterations": 0,
        }
        self.assertEqual(_route_after_assessment(state), "proceed")


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from unittest.mock import patch, MagicMock
from src.graph.graph import (
    analyze_viability, analyze_buildout, analyze_profitability,
    analyze_competitive, synthesize_report, evaluate, scope_target,
)

_BASE_STATE = {
    "target": "AC repair in LA",
    "scope": "Test scope. Diligence questions: market size? competitors? margins?",
    "research": '{"market_size": "$5B", "top_players": ["ServiceTitan", "Aire"], "unit_economics": "40% gross margin", "regulatory": ["EPA 608"], "cac_channels": ["Google Ads"]}',
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


class TestScopeTarget(unittest.TestCase):

    def test_scope_target_returns_scope_key(self):
        state = {**_BASE_STATE}
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "5 diligence questions for AC repair."
        with patch('src.graph.graph.llm_sonnet', mock_llm):
            result = scope_target(state)
        self.assertIn("scope", result)
        self.assertEqual(result["scope"], "5 diligence questions for AC repair.")
        mock_llm.invoke.assert_called_once()


class TestSynthesisCapTruncation(unittest.TestCase):

    def test_synthesize_truncates_long_pillar_inputs(self):
        long_text = "X" * 5000
        state = {
            **_BASE_STATE,
            "viability": long_text,
            "buildout_costs": long_text,
            "profitability": long_text,
            "competitive_advantage": long_text,
        }
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Report"

        with patch('src.graph.graph.llm_sonnet', mock_llm):
            synthesize_report(state)

        call_content = mock_llm.invoke.call_args[0][0][1].content
        # Each pillar capped at 3000 chars + "…"; total prompt must be well under 5000*4
        self.assertLess(len(call_content), 15000)
        self.assertIn("…", call_content)


class TestSluggify(unittest.TestCase):

    def setUp(self):
        from utils import slugify
        self.slugify = slugify

    def test_slash_replaced(self):
        self.assertEqual(self.slugify("AC/HVAC repair"), "ac-hvac-repair")

    def test_ampersand_replaced(self):
        self.assertEqual(self.slugify("M&A Services"), "manda-services")

    def test_parens_stripped(self):
        self.assertEqual(self.slugify("Tech (B2B)"), "tech-b2b")

    def test_spaces_hyphenated(self):
        self.assertEqual(self.slugify("Los Angeles, CA"), "los-angeles-ca")


if __name__ == "__main__":
    unittest.main()

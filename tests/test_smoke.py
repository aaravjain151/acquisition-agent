"""
Smoke test — runs the full pipeline end-to-end with live Bedrock + Tavily.
Skipped automatically when API keys are not present.

Run explicitly:
    pytest tests/test_smoke.py -m smoke -v
"""
import os
import pytest

NEEDS_LIVE_KEYS = pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY") or not os.environ.get("AWS_ACCESS_KEY_ID"),
    reason="Requires TAVILY_API_KEY and AWS_ACCESS_KEY_ID",
)


@pytest.mark.smoke
@NEEDS_LIVE_KEYS
def test_full_pipeline_produces_report():
    from src.graph.graph import graph

    result = graph.invoke(
        {"target": "AC repair services in Los Angeles, CA"},
        {"configurable": {"thread_id": "smoke-test"}},
    )

    assert result.get("scope"), "scope_target node did not populate scope"
    assert result.get("research"), "research node did not populate research"
    assert result.get("viability"), "analyze_viability did not run"
    assert result.get("report"), "synthesize_report did not run"
    assert result.get("evaluation"), "evaluate node did not run"

    rec = result["evaluation"].upper()
    assert any(word in rec for word in ("GO", "CAUTION", "NO-GO")), (
        f"evaluation missing expected recommendation keyword: {result['evaluation'][:200]}"
    )

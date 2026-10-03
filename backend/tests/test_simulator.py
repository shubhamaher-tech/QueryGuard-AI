import pytest
from app.models import Recommendation, QueryEvent
from app.simulator import RecommendationSimulator


def test_simulation_response_metrics():
    rec = Recommendation(
        id="REC-TEST-100",
        query_id="QE-TEST-100",
        title="Test Composite Index",
        type="INDEX_COMPOSITE",
        recommended_action="CREATE INDEX CONCURRENTLY idx_test ON TBL_A12 (COL_D02, COL_R01);",
        rationale="Simulated test index",
        confidence_score=0.92,
        risk_level="LOW",
        xai_evidence={},
    )
    query = QueryEvent(
        id="QE-TEST-100",
        fingerprint="fp_123",
        anonymized_sql="SELECT * FROM TBL_A12",
        table_token="TBL_A12",
        avg_latency_ms=1500.0,
        calls_per_minute=200,
        primary_bottleneck="Sequential Scan",
        risk_level="LOW",
        plan_json={"Plan": {"Total Cost": 45000.0}},
    )

    sim = RecommendationSimulator.run_simulation(rec, query)

    assert sim["is_simulated_estimate"] is True
    assert "Simulated estimate" in sim["notice"]
    assert sim["before_latency_ms"] == 1500.0
    assert sim["after_latency_ms"] < 1500.0
    assert sim["improvement_pct"] > 50.0
    assert sim["before_cost"] == 45000.0
    assert sim["after_cost"] < 45000.0
    assert sim["write_latency_impact_ms"] > 0
    assert sim["storage_overhead_gb"] > 0
    assert sim["confidence"] == 0.92
    assert sim["risk_level"] == "LOW"

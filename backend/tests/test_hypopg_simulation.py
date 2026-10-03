"""
Tests for Real HypoPG Simulation Engine, Decision Guardrails, and Privacy Boundaries
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Recommendation, QueryEvent
from app.hypopg.candidate_generator import IndexCandidate, IndexCandidateValidator
from app.hypopg.estimator import IndexImpactEstimator
from app.hypopg.service import HypoPGSimulationService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_candidate_validator_guardrails():
    # Valid B-tree candidate
    valid, err = IndexCandidateValidator.validate_candidate(
        "CREATE INDEX idx ON transactions (region_id, transaction_date);",
        ["region_id", "transaction_date"]
    )
    assert valid is True
    assert err is None

    # Rejects expression indexes
    invalid, err = IndexCandidateValidator.validate_candidate(
        "CREATE INDEX idx ON transactions (LOWER(status));",
        ["lower(status)"]
    )
    assert invalid is False
    assert "Disallowed index feature" in err or "Expression" in err

    # Rejects partial indexes
    invalid, err = IndexCandidateValidator.validate_candidate(
        "CREATE INDEX idx ON transactions (region_id) WHERE amount > 100;",
        ["region_id"]
    )
    assert invalid is False
    assert "Disallowed" in err

    # Rejects UNIQUE indexes
    invalid, err = IndexCandidateValidator.validate_candidate(
        "CREATE UNIQUE INDEX idx ON transactions (region_id);",
        ["region_id"]
    )
    assert invalid is False
    assert "Disallowed" in err


def test_estimator_ranges_and_guardrails():
    # Large reduction -> Accepted
    decision = IndexImpactEstimator.assess_decision(
        planner_cost_reduction_pct=78.5,
        index_used=True,
        is_seq_scan_eliminated=True,
    )
    assert decision["accepted"] is True
    assert decision["confidence"] == "HIGH"
    assert decision["recommendation_status"] == "SIMULATION_PASSED"

    # Index not selected -> Rejected / No measurable benefit
    decision_unused = IndexImpactEstimator.assess_decision(
        planner_cost_reduction_pct=0.0,
        index_used=False,
        is_seq_scan_eliminated=False,
    )
    assert decision_unused["accepted"] is False
    assert "NO_MEASURABLE_BENEFIT" in decision_unused["reason_codes"]
    assert decision_unused["recommendation_status"] == "NO_MEASURABLE_BENEFIT"

    # Range estimates
    storage_range = IndexImpactEstimator.estimate_storage_overhead_gb_range(250_000, 2)
    assert len(storage_range) == 2
    assert storage_range[0] < storage_range[1]

    write_range = IndexImpactEstimator.estimate_write_latency_increase_ms_range(2, 250_000)
    assert len(write_range) == 2
    assert write_range[0] < write_range[1]


def test_hypopg_simulation_api_flow(client):
    # 1. Fetch available recommendations
    res = client.get("/api/recommendations")
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) > 0
    target_rec = recs[0]
    rec_id = target_rec["id"]

    # 2. Trigger HypoPG simulation
    sim_res = client.post(f"/api/recommendations/{rec_id}/simulate")
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    # Schema verification
    assert sim_data["simulation_type"] == "HYPOTHETICAL_INDEX"
    assert sim_data["status"] == "COMPLETED"
    assert sim_data["label"] == "Simulated estimate"
    assert "baseline" in sim_data
    assert "proposal" in sim_data
    assert "impact" in sim_data
    assert "acceptance_decision" in sim_data
    assert sim_data["baseline"]["planner_total_cost"] > 0
    assert sim_data["proposal"]["planner_total_cost"] > 0
    assert sim_data["impact"]["estimated_planner_cost_reduction_percent"] >= 0
    assert len(sim_data["impact"]["estimated_latency_improvement_percent_range"]) == 2
    assert len(sim_data["impact"]["estimated_write_latency_increase_ms_range"]) == 2
    assert len(sim_data["impact"]["estimated_storage_overhead_gb_range"]) == 2

    # Virtual Index Token verification
    proposal = sim_data["proposal"]
    assert proposal["hypothetical_index_token"].startswith("HIDX_")
    for col_token in proposal["index_pattern"]:
        assert col_token.startswith("COL_")

    # Plain-English XAI explanation present
    assert "xai_explanation" in sim_data
    assert len(sim_data["xai_explanation"]) > 20

    # Strict Privacy Check: No raw schema names in response
    resp_text = sim_res.text.lower()
    assert "transactions" not in resp_text
    assert "customers" not in resp_text
    assert "order_items" not in resp_text
    assert "region_id" not in resp_text
    assert "transaction_date" not in resp_text
    assert "select *" not in resp_text

    # 3. GET simulation endpoint
    get_res = client.get(f"/api/recommendations/{rec_id}/simulation")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == sim_data["id"]
    assert get_data["proposal"]["hypothetical_index_token"] == proposal["hypothetical_index_token"]

    # 4. Reset simulation endpoint
    reset_res = client.post(f"/api/recommendations/{rec_id}/reset-simulation")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "RESET_SUCCESSFUL"
    assert reset_data["current_status"] == "PENDING"

    # Subsequent GET simulation should now return 404
    get_after_reset = client.get(f"/api/recommendations/{rec_id}/simulation")
    assert get_after_reset.status_code == 404

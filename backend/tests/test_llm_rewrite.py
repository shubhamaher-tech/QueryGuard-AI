import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.llm.router import complexity_router
from app.llm.prompt_builder import prompt_builder
from app.safety.sql_gatekeeper import sql_gatekeeper
from app.safety.rehydrator import local_rehydrator
from app.safety.semantic_validator import semantic_validator
from app.llm.client import ollama_client

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_router_sends_simple_query_to_fast_path():
    """Verify simple single-table query routes to fast path without SLM."""
    simple_sql = "SELECT COL_001, COL_R01 FROM TBL_A12 WHERE COL_R01 = :INT;"
    res = complexity_router.analyze_complexity(
        masked_sql=simple_sql,
        plan_json={"Plan": {"Node Type": "Seq Scan", "Total Cost": 50.0, "Plans": []}},
        avg_latency_ms=12.0,
        rule_confidence=0.90,
    )
    assert res.is_complex is False
    assert res.route_decision == "SIMPLE_QUERY_FAST_PATH"
    assert "SIMPLE_QUERY_WITHIN_BOUNDS" in res.route_reason_codes

def test_router_sends_complex_query_to_slm_path():
    """Verify multi-join / deep-tree query routes to complex SLM path with reason codes."""
    complex_sql = (
        "SELECT t.COL_001, c.COL_N06, oi.COL_Q08 FROM TBL_A12 t "
        "JOIN TBL_B03 c ON t.COL_C03 = c.COL_001 "
        "JOIN TBL_C99 oi ON oi.COL_T09 = t.COL_001 "
        "JOIN TBL_D44 p ON oi.COL_P10 = p.COL_001 "
        "WHERE t.COL_R01 = :INT;"
    )
    res = complexity_router.analyze_complexity(
        masked_sql=complex_sql,
        plan_json={"Plan": {"Node Type": "Hash Join", "Total Cost": 45000.0, "Plans": [
            {"Node Type": "Hash Join", "Plans": [
                {"Node Type": "Nested Loop", "Plans": [
                    {"Node Type": "Seq Scan", "Plans": []}
                ]}
            ]}
        ]}},
        avg_latency_ms=1450.0,
        rule_confidence=0.65,
    )
    assert res.is_complex is True
    assert res.route_decision == "COMPLEX_QUERY_SLM_ROUTED"
    assert "JOIN_COUNT_EXCEEDED" in res.route_reason_codes
    assert "HIGH_HISTORICAL_LATENCY" in res.route_reason_codes

def test_cache_key_generation_has_no_raw_sql():
    """Ensure HMAC cache key does not include raw tables and produces consistent hex."""
    masked_sql = "SELECT COL_001 FROM TBL_A12 WHERE COL_R01 = :INT;"
    key1 = complexity_router._generate_cache_key(masked_sql, 2, ["Seq Scan"])
    key2 = complexity_router._generate_cache_key(masked_sql, 2, ["Seq Scan"])
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex length
    assert "transactions" not in key1

def test_prompt_builder_sanitized_context_privacy():
    """Ensure prompt builder emits only authorized tokens and passes privacy scanner."""
    masked_sql = "SELECT COL_001, COL_R01 FROM TBL_A12 WHERE COL_R01 = :INT;"
    ctx = prompt_builder.build_sanitized_context(
        masked_sql=masked_sql,
        fingerprint="FP_TEST_001",
        plan_json={"Plan": {"Node Type": "Seq Scan"}},
        bottleneck="Sequential Scan",
        join_count=0,
        plan_depth=2,
    )
    user_prompt = prompt_builder.format_user_prompt(ctx)
    assert "TBL_A12" in user_prompt
    assert "COL_R01" in user_prompt
    assert "transactions" not in user_prompt.lower()
    assert "region_id" not in user_prompt.lower()

def test_sql_gatekeeper_enforces_select_only():
    """Gatekeeper must accept valid SELECT and reject DDL/DML, comments, and multi-statements."""
    # Valid SELECT
    ok, err = sql_gatekeeper.validate_sql("SELECT COL_001 FROM TBL_A12 WHERE COL_R01 = :INT;")
    assert ok is True
    assert err is None

    # Reject DROP
    ok, err = sql_gatekeeper.validate_sql("DROP TABLE TBL_A12;")
    assert ok is False
    assert "Forbidden keyword" in err

    # Reject UPDATE
    ok, err = sql_gatekeeper.validate_sql("UPDATE TBL_A12 SET COL_R01 = 5;")
    assert ok is False

    # Reject Comments
    ok, err = sql_gatekeeper.validate_sql("SELECT COL_001 FROM TBL_A12; -- sneak comment")
    assert ok is False
    assert "comments are strictly forbidden" in err

    # Reject Multi-statement
    ok, err = sql_gatekeeper.validate_sql("SELECT COL_001 FROM TBL_A12; SELECT COL_001 FROM TBL_B03;")
    assert ok is False
    assert "Multi-statement" in err

def test_rehydrator_rejects_unauthorized_tokens():
    """Rehydrator must reject tokens not authorized for the query."""
    valid_sql = "SELECT COL_001 FROM TBL_A12;"
    ok, err = local_rehydrator.verify_tokens_authorized(
        valid_sql, authorized_table_tokens={"TBL_A12"}, authorized_column_tokens={"COL_001"}
    )
    assert ok is True

    unauthorized_sql = "SELECT COL_UNKNOWN FROM TBL_UNAUTHORIZED;"
    ok, err = local_rehydrator.verify_tokens_authorized(
        unauthorized_sql, authorized_table_tokens={"TBL_A12"}, authorized_column_tokens={"COL_001"}
    )
    assert ok is False
    assert "Unauthorized or unknown table tokens" in err

def test_semantic_validator_enforces_select_shape():
    """Semantic validator verifies column counts match."""
    orig = "SELECT COL_001, COL_R01 FROM TBL_A12;"
    matching = "SELECT COL_001, COL_R01 FROM TBL_A12 WHERE COL_R01 = :INT;"
    ok, err = semantic_validator.validate_equivalence(orig, matching)
    assert ok is True

    mismatched = "SELECT COL_001 FROM TBL_A12;"
    ok, err = semantic_validator.validate_equivalence(orig, mismatched)
    assert ok is False
    assert "Projected column count mismatch" in err

def test_api_llm_status_endpoint(client):
    """Verify /api/llm/status returns expected structure even if Ollama is not running."""
    res = client.get("/api/llm/status")
    assert res.status_code == 200
    data = res.json()
    assert "enabled" in data
    assert "service_reachable" in data
    assert "selected_model" in data
    assert "local_only_privacy_mode" in data
    assert data["local_only_privacy_mode"] is True

def test_api_query_rewrite_simple_query_fast_path(client):
    """Verify simple query uses fast path without calling SLM."""
    res = client.post("/api/queries/QE-84920/rewrite/analyze?force_refresh=true")
    assert res.status_code == 200
    data = res.json()
    assert data["query_id"] == "QE-84920"
    assert "privacy_status" in data
    assert data["route_decision"] in ["SIMPLE_QUERY_FAST_PATH", "COMPLEX_QUERY_SLM_ROUTED"]

def test_api_query_rewrite_reset_cache(client):
    """Verify cache reset endpoint clears cache entry."""
    res = client.post("/api/queries/QE-84920/rewrite/reset-cache")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

@patch("app.llm.client.ollama_client.get_status")
@patch("app.llm.client.ollama_client.generate_json_rewrite")
def test_complex_query_slm_simulation_passed_flow(mock_generate, mock_status, client):
    """Mock complex query rewrite where SLM returns valid candidate that passes EXPLAIN guardrails."""
    mock_status.return_value = MagicMock(service_reachable=True, model_available_locally=True, enabled=True)
    mock_generate.return_value = {
        "action_type": "SQL_REWRITE",
        "rewritten_sql_template": (
            "SELECT a.COL_C01, a.COL_R01, b.COL_S04, SUM(a.COL_M05)\n"
            "FROM TBL_A12 a\n"
            "JOIN TBL_B03 b ON a.COL_R01 = b.COL_R01\n"
            "WHERE b.COL_S04 = :STR\n"
            "GROUP BY a.COL_C01, a.COL_R01, b.COL_S04;"
        ),
        "rewrite_strategy": "Optimized hash join and predicate reordering",
        "suggested_index_patterns": [
            {"table_token": "TBL_A12", "columns": ["COL_R01"], "reason": "Index filter acceleration"}
        ],
        "reason_codes": ["EARLY_FILTERING"],
        "assumptions": ["Index exists or recommended"],
        "risk_notes": ["Low risk"],
        "expected_benefit_level": "HIGH",
        "confidence": "HIGH"
    }

    res = client.post("/api/queries/QE-19402/rewrite/analyze?force_refresh=true")
    assert res.status_code == 200
    data = res.json()
    assert data["route_decision"] == "COMPLEX_QUERY_SLM_ROUTED"
    assert data["status"] in ["SIMULATION_PASSED", "NO_MEASURABLE_BENEFIT", "EXPLAIN_REJECTED"]
    assert "privacy_status" in data
    assert "transactions" not in json.dumps(data)

@patch("app.llm.client.ollama_client.get_status")
@patch("app.llm.client.ollama_client.generate_json_rewrite")
def test_complex_query_slm_safety_rejected_flow(mock_generate, mock_status, client):
    """Verify safety gateway catches and rejects model proposing destructive or malformed SQL."""
    mock_status.return_value = MagicMock(service_reachable=True, model_available_locally=True, enabled=True)
    mock_generate.return_value = {
        "action_type": "SQL_REWRITE",
        "rewritten_sql_template": "DROP TABLE TBL_A12;",
        "rewrite_strategy": "Destructive query attempt",
        "suggested_index_patterns": [],
        "reason_codes": ["MALICIOUS"],
        "assumptions": [],
        "risk_notes": ["High risk"],
        "expected_benefit_level": "LOW",
        "confidence": "LOW"
    }

    res = client.post("/api/queries/QE-19402/rewrite/analyze?force_refresh=true")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SAFETY_REJECTED"
    assert data["safety_checks_passed"] is False
    assert "Forbidden keyword" in (data["safety_rejection_reason"] or "")

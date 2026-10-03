"""
Tests for Realtime Telemetry Pipeline
Validates live metrics, slow query masking, rate calculations, and strict privacy guarantees.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_realtime_status_endpoint():
    res = client.get("/api/realtime/status")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data
    assert "mode" in data
    assert data["mode"] == "SANDBOX_WORKLOAD_POSTGRES"
    assert data["anonymization_active"] is True
    assert "polling_interval_sec" in data


def test_realtime_metrics_endpoint():
    res = client.get("/api/realtime/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "avg_latency_ms" in data
    assert "total_calls_per_sec" in data
    assert "cache_hit_ratio_pct" in data
    assert "top_slow_queries" in data
    assert "latency_trend" in data
    assert "bottleneck_distribution" in data
    assert "privacy_statement" in data


def test_realtime_slow_queries_sanitization():
    res = client.get("/api/realtime/slow-queries")
    assert res.status_code == 200
    queries = res.json()
    assert isinstance(queries, list)

    for q in queries:
        assert "query_fingerprint" in q
        assert "masked_query" in q
        assert "calls" in q
        assert "mean_time_ms" in q
        assert "severity" in q

        masked = q["masked_query"]
        # Raw sensitive table names must NOT appear in queries without being tokenized
        assert "sales_transactions" not in masked.lower()
        # Verify literals like quoted customer names/emails are masked
        import re
        assert not re.search(r"'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'", masked)


def test_connection_config_scaffold_safety():
    # Fetch current connection config
    get_res = client.get("/api/realtime/connection")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["active_mode"] == "SANDBOX"
    assert data["external_mode_status"] == "DISABLED_SCAFFOLD_ONLY"
    assert "safety_message" in data

    # Attempt to switch to external mode
    post_res = client.post("/api/realtime/connection", json={
        "mode": "EXTERNAL",
        "external_host": "db.production.company.com",
        "external_database": "prod_db"
    })
    assert post_res.status_code == 200
    post_data = post_res.json()
    # Must remain safely in SANDBOX with disabled scaffold explanation
    assert post_data["active_mode"] == "SANDBOX"
    assert post_data["external_mode_status"] == "DISABLED_SCAFFOLD_ONLY"
    assert "restricted" in post_data["safety_message"].lower() or "safety" in post_data["safety_message"].lower()

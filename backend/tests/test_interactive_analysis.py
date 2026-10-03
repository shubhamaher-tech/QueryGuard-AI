"""
Pytest Test Suite for QueryGuard AI Interactive Query Analysis Workspace

Tests:
1. Benchmark catalog & status endpoint
2. Safe sample queries endpoint
3. Analysis of valid queries on synthetic e-commerce
4. Analysis of valid queries on TPC-H SF 0.1
5. Safety Gateway DML rejection (SAFETY_VIOLATION_DML_DETECTED)
6. Safety Gateway comment rejection (SAFETY_VIOLATION_COMMENTS_FORBIDDEN)
7. Safety Gateway multi-statement rejection (SAFETY_VIOLATION_MULTI_STATEMENT)
8. Safety Gateway dangerous function rejection (SAFETY_VIOLATION_DANGEROUS_FUNCTION)
9. Safety Gateway unapproved relation rejection (SAFETY_VIOLATION_UNAPPROVED_RELATION)
10. DBA approval & rejection workflow with audit logging
11. Strict privacy guarantee: zero raw SQL in database
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models import AnalysisJob, AuditLog

client = TestClient(app)


def test_benchmarks_status():
    response = client.get("/api/benchmarks/status")
    assert response.status_code == 200
    data = response.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 3
    bench_ids = [b["id"] for b in data["benchmarks"]]
    assert "synthetic_ecommerce" in bench_ids
    assert "tpch_sf01" in bench_ids
    assert "tpch_sf1" in bench_ids
    assert "job_imdb" in bench_ids

    ecom = next(b for b in data["benchmarks"] if b["id"] == "synthetic_ecommerce")
    assert ecom["is_available"] is True
    assert "transactions" in ecom["tables"]

    tpch = next(b for b in data["benchmarks"] if b["id"] == "tpch_sf01")
    assert tpch["is_available"] is True
    assert "tpch_lineitem" in tpch["tables"]


def test_sample_queries_retrieval():
    response = client.get("/api/benchmarks/sample-queries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    
    # Filter by dataset
    ecom_res = client.get("/api/benchmarks/sample-queries?dataset=synthetic_ecommerce")
    assert ecom_res.status_code == 200
    assert all(q["dataset"] == "synthetic_ecommerce" for q in ecom_res.json())

    tpch_res = client.get("/api/benchmarks/sample-queries?dataset=tpch_sf01")
    assert tpch_res.status_code == 200
    assert all(q["dataset"] == "tpch_sf01" for q in tpch_res.json())


def test_analyze_valid_ecommerce_slow_query():
    query = (
        "SELECT region_id, COUNT(*) AS total_tx, SUM(amount) AS total_amount, AVG(amount) AS avg_amount "
        "FROM transactions WHERE region_id = 5 AND transaction_date >= '2025-06-01' GROUP BY region_id;"
    )
    payload = {"query": query, "dataset": "synthetic_ecommerce"}
    response = client.post("/api/analyze-query", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "COMPLETED"
    assert data["main_bottleneck"] in ("SEQUENTIAL_SCAN", "HIGH_PLAN_COST", "BALANCED_INDEXED")
    assert data["privacy_check_passed"] == 1
    assert data["masked_literals_count"] >= 1
    assert "transactions" not in data["masked_query_template"]
    assert "TBL_" in data["masked_query_template"]
    assert "simulation" in data
    assert "gnn_prediction" in data
    assert len(data["plan_graph"]["nodes"]) >= 1


def test_analyze_valid_tpch_query():
    query = (
        "SELECT l_returnflag, l_linestatus, count(*) "
        "FROM tpch_lineitem WHERE l_shipdate <= '1998-09-01' "
        "GROUP BY l_returnflag, l_linestatus;"
    )
    payload = {"query": query, "dataset": "tpch_sf01"}
    response = client.post("/api/analyze-query", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "COMPLETED"
    assert data["sandbox_dataset"] == "tpch_sf01"
    assert "tpch_lineitem" not in data["masked_query_template"]
    assert "TBL_" in data["masked_query_template"]
    assert data["gnn_prediction"]["model_version"] == "gnn_bottleneck_v1"


def test_safety_gateway_dml_rejection():
    dml_queries = [
        "DELETE FROM transactions WHERE id = 1;",
        "UPDATE transactions SET amount = 100 WHERE id = 1;",
        "INSERT INTO transactions (id, amount) VALUES (1, 100);",
        "DROP TABLE transactions;",
        "ALTER TABLE transactions ADD COLUMN hacked boolean;",
        "TRUNCATE transactions;",
    ]
    for q in dml_queries:
        res = client.post("/api/analyze-query", json={"query": q, "dataset": "synthetic_ecommerce"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "FAILED"
        assert data["safe_error_code"] == "SAFETY_VIOLATION_DML_DETECTED"
        assert "Forbidden keyword" in data["safe_error_message"] or "Expected a SELECT" in data["safe_error_message"]


def test_safety_gateway_comments_rejection():
    comment_queries = [
        "SELECT * FROM transactions -- sneaky trailing comment",
        "SELECT /* inline comment */ * FROM transactions",
    ]
    for q in comment_queries:
        res = client.post("/api/analyze-query", json={"query": q, "dataset": "synthetic_ecommerce"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "FAILED"
        assert data["safe_error_code"] == "SAFETY_VIOLATION_COMMENTS_FORBIDDEN"


def test_safety_gateway_multi_statement_rejection():
    q = "SELECT * FROM transactions; SELECT * FROM products;"
    res = client.post("/api/analyze-query", json={"query": q, "dataset": "synthetic_ecommerce"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["safe_error_code"] == "SAFETY_VIOLATION_MULTI_STATEMENT"


def test_safety_gateway_dangerous_functions():
    funcs = [
        "SELECT pg_sleep(5);",
        "SELECT dblink('host=evil.com', 'SELECT 1');",
        "SELECT current_user;",
        "SELECT version();",
    ]
    for q in funcs:
        res = client.post("/api/analyze-query", json={"query": q, "dataset": "synthetic_ecommerce"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "FAILED"
        assert data["safe_error_code"] == "SAFETY_VIOLATION_DANGEROUS_FUNCTION"


def test_safety_gateway_unapproved_relations():
    res = client.post("/api/analyze-query", json={"query": "SELECT * FROM pg_catalog.pg_database;", "dataset": "synthetic_ecommerce"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "FAILED"
    assert data["safe_error_code"] == "SAFETY_VIOLATION_UNAPPROVED_RELATION"


def test_approval_and_rejection_workflow():
    # 1. Run query
    query = "SELECT count(*) FROM transactions;"
    res = client.post("/api/analyze-query", json={"query": query, "dataset": "synthetic_ecommerce"})
    assert res.status_code == 200
    job = res.json()
    analysis_id = job["analysis_id"]
    assert job["approval_status"] == "PENDING"

    # 2. Approve
    app_res = client.post(
        f"/api/analyze-query/{analysis_id}/approve",
        json={"decision": "APPROVED", "reason": "Verified low write risk", "actor": "TestDBA"},
    )
    assert app_res.status_code == 200
    approved_job = app_res.json()
    assert approved_job["approval_status"] == "APPROVED"
    assert approved_job["approved_by"] == "TestDBA"

    # 3. Reject another
    res2 = client.post("/api/analyze-query", json={"query": "SELECT count(*) FROM regions;", "dataset": "synthetic_ecommerce"})
    job2 = res2.json()
    rej_res = client.post(
        f"/api/analyze-query/{job2['analysis_id']}/reject",
        json={"decision": "REJECTED", "reason": "Not enough performance gain", "actor": "TestDBA"},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["approval_status"] == "REJECTED"


def test_privacy_guarantee_no_raw_sql_persisted():
    sensitive_literal = "SECRET_DISCOUNT_9999"
    query = f"SELECT count(*) FROM transactions WHERE status = '{sensitive_literal}';"
    res = client.post("/api/analyze-query", json={"query": query, "dataset": "synthetic_ecommerce"})
    assert res.status_code == 200
    data = res.json()
    analysis_id = data["analysis_id"]

    # Verify directly against database
    db = SessionLocal()
    try:
        db_job = db.query(AnalysisJob).filter(AnalysisJob.analysis_id == analysis_id).first()
        assert db_job is not None
        assert sensitive_literal not in db_job.masked_query_template
        assert "transactions" not in db_job.masked_query_template
        assert ":STRING" in db_job.masked_query_template or "%(STRING)s" in db_job.masked_query_template
        assert "TBL_" in db_job.masked_query_template

        # Check audit log as well
        db_audit = db.query(AuditLog).filter(AuditLog.query_id == analysis_id).first()
        assert db_audit is not None
        audit_str = str(db_audit.details)
        assert sensitive_literal not in audit_str
        assert "transactions" not in audit_str
    finally:
        db.close()

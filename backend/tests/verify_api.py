import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

def run_api_verification():
    print("=== Running Comprehensive API End-to-End Verification ===")
    with TestClient(app) as client:
        # 1. Health check
        print("\n1. Testing GET /health...")
        res = client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("  -> Status:", res.json())

        # 2. Dashboard summary
        print("\n2. Testing GET /api/dashboard/summary...")
        res = client.get("/api/dashboard/summary")
        assert res.status_code == 200
        summary = res.json()
        print("  -> Slow queries:", summary["slow_queries_count"])
        print("  -> Pending approvals:", summary["pending_approvals_count"])
        print("  -> Avg estimated gain:", summary["avg_estimated_gain_pct"])
        assert summary["slow_queries_count"] >= 3

        # 3. Queries listing
        print("\n3. Testing GET /api/queries...")
        res = client.get("/api/queries")
        assert res.status_code == 200
        queries = res.json()
        print(f"  -> Retrieved {len(queries)} queries")
        assert len(queries) >= 3

        # 4. Query detail
        qid = queries[0]["id"]
        print(f"\n4. Testing GET /api/queries/{qid}...")
        res = client.get(f"/api/queries/{qid}")
        assert res.status_code == 200
        q_detail = res.json()
        print("  -> Tokenized table:", q_detail["table_token"])
        print("  -> Primary bottleneck:", q_detail["primary_bottleneck"])
        print("  -> Privacy status:", q_detail["privacy_status"])
        assert "Plan" in q_detail["plan_json"]

        # 5. Query plan endpoint
        print(f"\n5. Testing GET /api/queries/{qid}/plan...")
        res = client.get(f"/api/queries/{qid}/plan")
        assert res.status_code == 200
        plan = res.json()
        assert "plan" in plan

        # 6. Recommendations listing
        print("\n6. Testing GET /api/recommendations...")
        res = client.get("/api/recommendations")
        assert res.status_code == 200
        recs = res.json()
        print(f"  -> Found {len(recs)} recommendations")
        assert len(recs) >= 3
        rec_id = recs[0]["id"]

        # 7. Recommendation detail
        print(f"\n7. Testing GET /api/recommendations/{rec_id}...")
        res = client.get(f"/api/recommendations/{rec_id}")
        assert res.status_code == 200
        rec_detail = res.json()
        print("  -> Title:", rec_detail["title"])
        print("  -> XAI bottleneck:", rec_detail["xai_evidence"]["bottleneck_type"])

        # 8. Run simulation
        print(f"\n8. Testing POST /api/recommendations/{rec_id}/simulate...")
        res = client.post(f"/api/recommendations/{rec_id}/simulate")
        assert res.status_code == 200
        sim = res.json()
        print("  -> Simulated latency improvement:", f"+{sim['improvement_pct']}%")
        print("  -> Before vs After cost:", f"{sim['before_cost']} -> {sim['after_cost']}")
        print("  -> Simulation notice:", sim["notice"])
        assert sim["is_simulated_estimate"] is True

        # 9. Approve recommendation
        print(f"\n9. Testing POST /api/recommendations/{rec_id}/approve...")
        res = client.post(
            f"/api/recommendations/{rec_id}/approve",
            json={"actor_id": "DBA_ADMIN_01", "comment": "Verified and approved in maintenance schedule."}
        )
        assert res.status_code == 200
        approval = res.json()
        print("  -> Approval response:", approval["message"])
        assert approval["action"] == "APPROVED"

        # 10. Audit logs check
        print("\n10. Testing GET /api/audit-logs...")
        res = client.get("/api/audit-logs")
        assert res.status_code == 200
        logs = res.json()
        print(f"  -> Total audit logs: {len(logs)}")
        assert any(l["action_type"] == "RECOMMENDATION_APPROVED" for l in logs)

        # 11. Privacy sanitize live endpoint
        print("\n11. Testing POST /api/privacy/sanitize...")
        sample_sql = "SELECT * FROM sales_transactions WHERE region_id = 42 AND transaction_date >= '2026-09-01';"
        res = client.post("/api/privacy/sanitize", json={"raw_sql": sample_sql})
        assert res.status_code == 200
        san = res.json()
        print("  -> Raw SQL:", sample_sql)
        print("  -> Sanitized SQL:", san["sanitized_sql"])
        assert "TBL_A12" in san["sanitized_sql"]
        assert "COL_R01 = :INT" in san["sanitized_sql"]
        assert "COL_D02 >= :DATE" in san["sanitized_sql"]
        assert "sales_transactions" not in san["sanitized_sql"]
        assert "42" not in san["sanitized_sql"]

        # 12. Telemetry collection
        print("\n12. Testing POST /api/telemetry/collect...")
        res = client.post("/api/telemetry/collect")
        assert res.status_code == 200
        t_collect = res.json()
        print("  -> Collect status:", t_collect["status"])
        print("  -> Events created:", t_collect["events_created"])
        print("  -> Privacy check passed:", t_collect["privacy_check_passed"])
        assert t_collect["status"] == "COMPLETED"
        assert t_collect["privacy_check_passed"] is True
        assert "transactions" not in res.text.lower()

        # 13. Telemetry status
        print("\n13. Testing GET /api/telemetry/status...")
        res = client.get("/api/telemetry/status")
        assert res.status_code == 200
        t_status = res.json()
        print("  -> Status:", t_status["status"])
        print("  -> Statements scanned:", t_status["statements_scanned"])
        assert t_status["privacy_check_passed"] is True

        # 14. Telemetry events list
        print("\n14. Testing GET /api/telemetry/events...")
        res = client.get("/api/telemetry/events")
        assert res.status_code == 200
        t_events = res.json()
        print(f"  -> Total telemetry events: {len(t_events)}")
        assert len(t_events) >= 1
        telem_id = t_events[0]["id"]

        # 15. Telemetry event detail with execution plan graph
        print(f"\n15. Testing GET /api/telemetry/events/{telem_id}...")
        res = client.get(f"/api/telemetry/events/{telem_id}")
        assert res.status_code == 200
        t_detail = res.json()
        print("  -> Event ID:", t_detail["id"])
        print("  -> Plan nodes count:", len(t_detail["plan_nodes"]))
        print("  -> Honesty label:", t_detail["honesty_label"])
        assert len(t_detail["plan_nodes"]) > 0
        assert "Rule-based plan graph analysis; GNN/RL-ready architecture." in t_detail["honesty_label"]
        # 16. LLM status check
        print("\n16. Testing GET /api/llm/status...")
        res = client.get("/api/llm/status")
        assert res.status_code == 200
        llm_status = res.json()
        print("  -> LLM status:", llm_status["message"])
        assert llm_status["local_only_privacy_mode"] is True

        # 17. Query rewrite analyze endpoint
        print("\n17. Testing POST /api/queries/QE-84920/rewrite/analyze...")
        res = client.post("/api/queries/QE-84920/rewrite/analyze?force_refresh=true")
        assert res.status_code == 200
        rewr_data = res.json()
        print("  -> Route decision:", rewr_data["route_decision"])
        print("  -> Rewrite status:", rewr_data["status"])
        assert "privacy_status" in rewr_data

        # 18. Query rewrite get endpoint
        print("\n18. Testing GET /api/queries/QE-84920/rewrite...")
        res = client.get("/api/queries/QE-84920/rewrite")
        assert res.status_code == 200
        assert res.json()["query_id"] == "QE-84920"

        # 19. Query rewrite reset cache endpoint
        print("\n19. Testing POST /api/queries/QE-84920/rewrite/reset-cache...")
        res = client.post("/api/queries/QE-84920/rewrite/reset-cache")
        assert res.status_code == 200
        assert res.json()["status"] == "success"

    print("\n[SUCCESS] All 19 verification checks PASSED successfully!")

if __name__ == "__main__":
    run_api_verification()

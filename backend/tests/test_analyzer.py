import pytest
from app.analyzer import QueryPlanAnalyzer


def test_sequential_scan_detection_and_xai_evidence():
    plan_seq = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "TBL_A12",
            "Total Cost": 39800.0,
            "Actual Rows": 1450000,
            "Filter": "(COL_D02 >= :DATE AND COL_R01 = :INT)",
        }
    }
    recs = QueryPlanAnalyzer.analyze_plan(
        query_id="QE-TEST-01",
        anonymized_sql="SELECT * FROM TBL_A12 WHERE COL_D02 >= :DATE AND COL_R01 = :INT",
        plan_data=plan_seq,
    )

    assert len(recs) >= 1
    idx_rec = next((r for r in recs if r["type"] == "INDEX_COMPOSITE"), None)
    assert idx_rec is not None
    assert "idx_tbl_a12" in idx_rec["recommended_action"].lower()

    # Verify structured XAI packet
    xai = idx_rec["xai_evidence"]
    assert xai["bottleneck_type"] == "Sequential Scan Bottleneck"
    assert len(xai["affected_plan_nodes"]) > 0
    assert len(xai["evidence_signals"]) > 0
    assert "recommended_action" in xai
    assert len(xai["expected_read_improvement_percent_range"]) == 2
    assert len(xai["estimated_write_latency_increase_ms_range"]) == 2
    assert len(xai["estimated_storage_overhead_gb_range"]) == 2
    assert 0.0 <= xai["confidence"] <= 1.0
    assert xai["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "No raw rows" in xai["privacy_status"]


def test_nested_loop_join_detection():
    plan_nl = {
        "Plan": {
            "Node Type": "Nested Loop",
            "Total Cost": 51200.0,
            "Loops": 450,
            "Plans": [
                {"Node Type": "Seq Scan", "Relation Name": "TBL_A12", "Total Cost": 15000.0},
                {"Node Type": "Index Scan", "Relation Name": "TBL_B03", "Total Cost": 25.0},
            ],
        }
    }
    recs = QueryPlanAnalyzer.analyze_plan(
        query_id="QE-TEST-02",
        anonymized_sql="SELECT * FROM TBL_A12 a JOIN TBL_B03 b ON a.COL_R01 = b.COL_R01",
        plan_data=plan_nl,
    )
    nl_rec = next((r for r in recs if "Nested-Loop" in r["xai_evidence"]["bottleneck_type"]), None)
    assert nl_rec is not None
    assert "TBL_B03" in nl_rec["recommended_action"]


def test_expensive_sort_detection():
    plan_sort = {
        "Plan": {
            "Node Type": "Sort",
            "Relation Name": "TBL_C99",
            "Total Cost": 89400.0,
            "Sort Method": "external merge Disk",
            "Sort Space Used": 48512,
        }
    }
    recs = QueryPlanAnalyzer.analyze_plan(
        query_id="QE-TEST-03",
        anonymized_sql="SELECT * FROM TBL_C99 ORDER BY COL_M05 DESC",
        plan_data=plan_sort,
    )
    sort_rec = next((r for r in recs if r["type"] == "REWRITE_QUERY"), None)
    assert sort_rec is not None
    assert "Sort" in sort_rec["xai_evidence"]["bottleneck_type"]

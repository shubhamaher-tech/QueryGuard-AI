import pytest
from app.telemetry.plan_parser import TelemetryPlanParser
from app.telemetry.collector import WorkloadTelemetryCollector, ALLOW_LISTED_TABLE_KEYWORDS


def test_plan_parser_converts_explain_to_graph():
    sample_explain = [
        {
            "Plan": {
                "Node Type": "Aggregate",
                "Total Cost": 45000.0,
                "Plan Rows": 1,
                "Plans": [
                    {
                        "Node Type": "Nested Loop",
                        "Total Cost": 42000.0,
                        "Plan Rows": 500,
                        "Plans": [
                            {
                                "Node Type": "Seq Scan",
                                "Relation Name": "transactions",
                                "Total Cost": 35000.0,
                                "Plan Rows": 15000,
                                "Filter": "(region_id = 5)"
                            },
                            {
                                "Node Type": "Index Scan",
                                "Relation Name": "customers",
                                "Total Cost": 8.5,
                                "Plan Rows": 1
                            }
                        ]
                    }
                ]
            }
        }
    ]

    result = TelemetryPlanParser.parse_plan(sample_explain)

    # 1. Graph structure checks
    nodes = result["nodes"]
    edges = result["edges"]
    assert len(nodes) == 4
    assert len(edges) == 3

    # Verify no raw table names stored in node relation tokens
    for n in nodes:
        if n["relation_token"]:
            assert "transactions" not in n["relation_token"]
            assert "customers" not in n["relation_token"]
            assert n["relation_token"].startswith("TBL_")

    # 2. Bottlenecks checks (detected sequential scan and nested loop)
    assert result["primary_bottleneck"] in ["SEQUENTIAL_SCAN", "NESTED_LOOP"]
    assert result["plan_depth"] >= 3
    assert len(result["recommendations"]) >= 1

    # 3. Honesty label
    assert "Rule-based plan graph analysis; GNN/RL-ready architecture." in result["honesty_label"]


def test_telemetry_collector_allow_list_and_metrics():
    # Verify allow-listed keywords
    assert "transactions" in ALLOW_LISTED_TABLE_KEYWORDS
    assert "customers" in ALLOW_LISTED_TABLE_KEYWORDS
    assert "order_items" in ALLOW_LISTED_TABLE_KEYWORDS

    # Verify fallback metrics structure
    fallback_data = WorkloadTelemetryCollector._generate_fallback_benchmark_telemetry()
    assert len(fallback_data) >= 3

    required_fields = [
        "queryid",
        "calls",
        "total_exec_time",
        "mean_exec_time",
        "rows",
        "shared_blks_hit",
        "shared_blks_read",
        "temp_blks_read",
        "temp_blks_written",
        "raw_sql",
        "explain_json",
    ]
    for item in fallback_data:
        for field in required_fields:
            assert field in item, f"Missing required telemetry field {field}"
        assert item["calls"] > 0
        assert "explain_json" in item

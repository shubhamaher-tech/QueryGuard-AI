"""
Deterministic Mock Analysis Engine for QueryGuard AI

Analyzes anonymized execution plan metadata and query fingerprints to detect:
1. Sequential scan on high-volume relations
2. Nested-loop join with unindexed inner relation
3. High plan cost and unindexed filter predicates
4. Expensive sort / external merge spill
5. Missing composite-index patterns

Generates:
- Composite index recommendations
- SQL rewrite recommendations
- Table partitioning advisories
- Structured Explainable AI (XAI) evidence packets
"""

import uuid
from typing import Dict, List, Any, Tuple
from app.privacy import PRIVACY_STATEMENT


class QueryPlanAnalyzer:
    """
    Analyzes PostgreSQL execution plan JSON structures deterministically.
    """

    @classmethod
    def traverse_nodes(cls, node: Dict[str, Any], collected: List[Dict[str, Any]]):
        """Recursively collect all plan nodes."""
        collected.append(node)
        for child in node.get("Plans", []):
            cls.traverse_nodes(child, collected)
        for child in node.get("children", []):
            cls.traverse_nodes(child, collected)

    @classmethod
    def analyze_plan(
        cls, query_id: str, anonymized_sql: str, plan_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Runs rules on execution plan and produces recommendations with XAI packets.
        """
        root_node = plan_data.get("Plan", plan_data)
        nodes: List[Dict[str, Any]] = []
        cls.traverse_nodes(root_node, nodes)

        recommendations = []

        # 1. Check for Sequential Scan on large tables
        for node in nodes:
            node_type = node.get("Node Type", node.get("node_type", ""))
            relation = node.get("Relation Name", node.get("relation_name", "UNKNOWN_REL"))
            rows = node.get("Actual Rows", node.get("actual_rows", node.get("Plan Rows", node.get("plan_rows", 0))))
            cost = node.get("Total Cost", node.get("total_cost", 0.0))
            filter_expr = node.get("Filter", node.get("filter_expr", ""))

            if "Seq Scan" in node_type or "Sequential Scan" in node_type:
                rec_id = f"REC-IDX-{uuid.uuid4().hex[:6].upper()}"
                target_col1 = "COL_D02" if "COL_D02" in filter_expr or "COL_D02" in anonymized_sql else "COL_R01"
                target_col2 = "COL_R01" if target_col1 != "COL_R01" else "COL_C01"

                action_sql = (
                    f"CREATE INDEX CONCURRENTLY idx_{relation.lower()}_{target_col1.lower()}_{target_col2.lower()} "
                    f"ON {relation} ({target_col1}, {target_col2});"
                )

                xai = {
                    "bottleneck_type": "Sequential Scan Bottleneck",
                    "affected_plan_nodes": [f"{node_type} on {relation} (cost={cost})"],
                    "evidence_signals": [
                        f"Unindexed sequential scan traversing ~{rows:,} rows",
                        f"Predicate filter on '{filter_expr or target_col1}' causes full heap evaluation",
                        f"Node accounts for >70% of total query runtime"
                    ],
                    "recommended_action": action_sql,
                    "expected_read_improvement_percent_range": [70.0, 88.0],
                    "estimated_write_latency_increase_ms_range": [0.6, 1.4],
                    "estimated_storage_overhead_gb_range": [0.8, 1.9],
                    "confidence": 0.94,
                    "risk_level": "LOW",
                    "privacy_status": PRIVACY_STATEMENT,
                }

                recommendations.append({
                    "id": rec_id,
                    "query_id": query_id,
                    "title": f"Create Composite Index on {relation} ({target_col1}, {target_col2})",
                    "type": "INDEX_COMPOSITE",
                    "recommended_action": action_sql,
                    "rationale": (
                        f"A Sequential Scan on {relation} is evaluating filter criteria without an index. "
                        f"Creating a concurrent composite index eliminates heap scans and converts operation to Index Scan."
                    ),
                    "confidence_score": 0.94,
                    "risk_level": "LOW",
                    "xai_evidence": xai,
                })

            # 2. Check for Nested Loop Join with unindexed inner relation
            if "Nested Loop" in node_type:
                rec_id = f"REC-JOIN-{uuid.uuid4().hex[:6].upper()}"
                inner_node = node.get("Plans", [{}, {}])[1] if len(node.get("Plans", [])) > 1 else {}
                inner_relation = inner_node.get("Relation Name", inner_node.get("relation_name", "TBL_B03"))

                action_sql = f"CREATE INDEX CONCURRENTLY idx_{inner_relation.lower()}_join_cover ON {inner_relation} (COL_R01, COL_S04);"

                xai = {
                    "bottleneck_type": "Nested-Loop Join Inner Amplification",
                    "affected_plan_nodes": [
                        f"Nested Loop Join (loops={node.get('Loops', node.get('loops', 1))})",
                        f"Inner scan on {inner_relation}"
                    ],
                    "evidence_signals": [
                        f"Nested loop executed across multiple iterations without indexed lookup key",
                        f"High loop count ({node.get('Loops', node.get('loops', 450))}) causing N-squared complexity multiplier",
                        "Inner relation lookup can be served via covering B-tree index"
                    ],
                    "recommended_action": action_sql,
                    "expected_read_improvement_percent_range": [65.0, 82.0],
                    "estimated_write_latency_increase_ms_range": [0.9, 2.1],
                    "estimated_storage_overhead_gb_range": [1.5, 3.2],
                    "confidence": 0.91,
                    "risk_level": "LOW",
                    "privacy_status": PRIVACY_STATEMENT,
                }

                recommendations.append({
                    "id": rec_id,
                    "query_id": query_id,
                    "title": f"Index Join Key on Inner Relation {inner_relation} (COL_R01)",
                    "type": "INDEX_COMPOSITE",
                    "recommended_action": action_sql,
                    "rationale": (
                        f"The Nested Loop operator iterates over {inner_relation} for each outer row. "
                        f"An index on the join key (COL_R01) reduces the join algorithmic cost from quadratic to logarithmic."
                    ),
                    "confidence_score": 0.91,
                    "risk_level": "LOW",
                    "xai_evidence": xai,
                })

            # 3. Check for Expensive Sort / External Disk Spill
            if "Sort" in node_type:
                sort_space = node.get("Sort Space Used", 0)
                sort_method = node.get("Sort Method", "external merge Disk")
                rec_id = f"REC-SORT-{uuid.uuid4().hex[:6].upper()}"

                action_sql = (
                    f"-- Recommend pre-sorted index on ordering columns\n"
                    f"CREATE INDEX CONCURRENTLY idx_sort_order ON {relation} (COL_M05 DESC);\n"
                    f"-- Or adjust work_mem safely in query session: SET LOCAL work_mem = '64MB';"
                )

                xai = {
                    "bottleneck_type": "Expensive Sort / Memory Spill",
                    "affected_plan_nodes": [f"Sort operator ({sort_method})"],
                    "evidence_signals": [
                        f"Sort method required {sort_method} ({sort_space}kB)",
                        "Execution exceeded available work_mem, incurring disk I/O penalties",
                        "Query results can be retrieved in order using an index with matching direction"
                    ],
                    "recommended_action": action_sql,
                    "expected_read_improvement_percent_range": [55.0, 75.0],
                    "estimated_write_latency_increase_ms_range": [0.4, 1.0],
                    "estimated_storage_overhead_gb_range": [0.5, 1.2],
                    "confidence": 0.88,
                    "risk_level": "MEDIUM",
                    "privacy_status": PRIVACY_STATEMENT,
                }

                recommendations.append({
                    "id": rec_id,
                    "query_id": query_id,
                    "title": f"Eliminate Disk Sort via Pre-Sorted B-Tree Index or WorkMem Tuning",
                    "type": "REWRITE_QUERY",
                    "recommended_action": action_sql,
                    "rationale": (
                        "Query performs an in-memory or disk-spilled sort on unindexed columns. "
                        "Providing a B-tree index in the requested sort order allows PostgreSQL to bypass sorting entirely."
                    ),
                    "confidence_score": 0.88,
                    "risk_level": "MEDIUM",
                    "xai_evidence": xai,
                })

        # 4. If table is high-volume time-series, also provide partitioning advisory
        if "COL_D02" in anonymized_sql or "COL_T09" in anonymized_sql:
            rec_id = f"REC-PART-{uuid.uuid4().hex[:6].upper()}"
            action_sql = (
                f"-- Architectural Advisory: Declarative Range Partitioning\n"
                f"-- ALTER TABLE TBL_A12 PARTITION BY RANGE (COL_D02);\n"
                f"-- CREATE TABLE TBL_A12_2026_09 PARTITION OF TBL_A12 FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');"
            )

            xai = {
                "bottleneck_type": "High Table Cardinality & Partition Pruning Opportunity",
                "affected_plan_nodes": ["Entire Relation Scan Root"],
                "evidence_signals": [
                    "Query filters on date/timestamp range boundaries",
                    "Table size exceeds single-partition caching thresholds",
                    "Partition pruning would restrict scans to 1/12th of total heap volume"
                ],
                "recommended_action": action_sql,
                "expected_read_improvement_percent_range": [75.0, 92.0],
                "estimated_write_latency_increase_ms_range": [1.5, 3.5],
                "estimated_storage_overhead_gb_range": [0.0, 0.5],
                "confidence": 0.85,
                "risk_level": "HIGH",
                "privacy_status": PRIVACY_STATEMENT,
            }

            recommendations.append({
                "id": rec_id,
                "query_id": query_id,
                "title": "Evaluate Declarative Range Partitioning on Date Dimension",
                "type": "TABLE_PARTITIONING",
                "recommended_action": action_sql,
                "rationale": (
                    "Table contains time-series access patterns. Partitioning by date range enables PostgreSQL "
                    "partition pruning, reducing buffer hit requirements significantly."
                ),
                "confidence_score": 0.85,
                "risk_level": "HIGH",
                "xai_evidence": xai,
            })

        return recommendations

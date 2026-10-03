"""
Deterministic Simulated Sandbox Service for QueryGuard AI

Simulates the performance, storage, and write latency impact of a database recommendation.
Guaranteed safety:
- Never executes DDL on the underlying database.
- Never mutates production or demo tables.
- Clearly flags all outputs as "Simulated estimate".
"""

import uuid
import datetime
from typing import Dict, Any
from app.models import Recommendation, Simulation, QueryEvent


class RecommendationSimulator:
    """
    Simulates database planner impact without applying any schema or DDL modifications.
    """

    @classmethod
    def run_simulation(cls, recommendation: Recommendation, query: QueryEvent) -> Dict[str, Any]:
        """
        Calculates before and after metrics based on recommendation type and query baseline.
        """
        rec_type = recommendation.type
        current_latency = query.avg_latency_ms

        # Extract root plan total cost
        plan_json = query.plan_json or {}
        root_plan = plan_json.get("Plan", plan_json)
        before_cost = float(root_plan.get("Total Cost", root_plan.get("total_cost", 18500.0)))

        if rec_type == "INDEX_COMPOSITE":
            # Composite index drastically reduces scan costs and read latency
            improvement_factor = 0.78  # 78% reduction
            after_latency = round(current_latency * (1 - improvement_factor), 2)
            after_cost = round(before_cost * 0.12, 2)  # Index scan cost
            improvement_pct = 78.0
            write_latency_impact_ms = 0.95  # Extra B-tree page write overhead on INSERT/UPDATE
            storage_overhead_gb = 1.45  # Index storage footprint estimate
            simulated_plan_nodes = [
                {
                    "node_type": "Aggregate",
                    "total_cost": after_cost,
                    "actual_time_ms": after_latency,
                    "children": [
                        {
                            "node_type": "Index Scan",
                            "relation_name": query.table_token,
                            "index_name": "idx_simulated_composite",
                            "total_cost": round(after_cost * 0.85, 2),
                            "actual_time_ms": round(after_latency * 0.85, 2),
                            "is_bottleneck": False,
                            "note": "Replaced high-cost Sequential Scan with Index Scan using b-tree lookup"
                        }
                    ]
                }
            ]

        elif rec_type == "REWRITE_QUERY":
            # Query rewrite (e.g. eliminating sort or subquery)
            improvement_factor = 0.62
            after_latency = round(current_latency * (1 - improvement_factor), 2)
            after_cost = round(before_cost * 0.35, 2)
            improvement_pct = 62.0
            write_latency_impact_ms = 0.05  # Minimal write impact for query rewrite
            storage_overhead_gb = 0.30
            simulated_plan_nodes = [
                {
                    "node_type": "Index Scan with Order",
                    "relation_name": query.table_token,
                    "total_cost": after_cost,
                    "actual_time_ms": after_latency,
                    "is_bottleneck": False,
                    "note": "Sorting eliminated via pre-ordered index traversal"
                }
            ]

        elif rec_type == "TABLE_PARTITIONING":
            # Table partitioning
            improvement_factor = 0.84
            after_latency = round(current_latency * (1 - improvement_factor), 2)
            after_cost = round(before_cost * 0.15, 2)
            improvement_pct = 84.0
            write_latency_impact_ms = 2.10  # Routing tuples to partitions overhead
            storage_overhead_gb = 0.20
            simulated_plan_nodes = [
                {
                    "node_type": "Partition Pruned Scan",
                    "relation_name": f"{query.table_token}_active_partition",
                    "total_cost": after_cost,
                    "actual_time_ms": after_latency,
                    "is_bottleneck": False,
                    "note": "PostgreSQL pruned 11 inactive partitions; only scanning target monthly slice"
                }
            ]

        else:
            improvement_factor = 0.50
            after_latency = round(current_latency * 0.5, 2)
            after_cost = round(before_cost * 0.5, 2)
            improvement_pct = 50.0
            write_latency_impact_ms = 0.5
            storage_overhead_gb = 0.5
            simulated_plan_nodes = []

        simulation_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"

        return {
            "id": simulation_id,
            "recommendation_id": recommendation.id,
            "before_cost": before_cost,
            "after_cost": after_cost,
            "before_latency_ms": current_latency,
            "after_latency_ms": after_latency,
            "improvement_pct": improvement_pct,
            "write_latency_impact_ms": write_latency_impact_ms,
            "storage_overhead_gb": storage_overhead_gb,
            "confidence": recommendation.confidence_score,
            "risk_level": recommendation.risk_level,
            "is_simulated_estimate": True,
            "notice": "Simulated estimate. No production DDL or workload changes were applied.",
            "simulated_plan_nodes": simulated_plan_nodes,
            "created_at": datetime.datetime.utcnow(),
        }

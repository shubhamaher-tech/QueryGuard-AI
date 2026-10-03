"""
Model-Based Estimator for Index Storage Overhead and Write Latency Impact

Provides realistic range estimates for:
- Storage footprint (GB range)
- Write latency overhead (ms range)
- Read latency improvement (percent range)

Estimator variables:
- Table row count bucket (<10k, 10k-100k, 100k-500k, 500k-2M, >2M)
- Indexed column count (1 to 4)
- Average column width bytes
- B-Tree page fill factor (typical default 90% for leaf pages)
- Read/Write workload ratio (default analytical: 80% read / 20% write)
"""

from typing import Dict, Any, List, Tuple


class IndexImpactEstimator:
    """
    Computes mathematical range estimates for index resource overhead.
    Clearly designated as model-based planner estimates, not measured production telemetry.
    """

    @classmethod
    def estimate_storage_overhead_gb_range(
        cls,
        estimated_rows: int,
        column_count: int,
        avg_col_bytes: int = 8,
    ) -> List[float]:
        """
        Estimates B-Tree index storage in gigabytes.
        B-tree tuple overhead = 8 bytes item pointer + 8 bytes tuple header + data bytes.
        With 10% leaf fragmentation and index page headers.
        """
        bytes_per_row = 16 + (column_count * avg_col_bytes)
        # 1.15 to account for internal branch nodes and page header overhead
        raw_bytes = estimated_rows * bytes_per_row * 1.15

        # Lower bound assumes compact packed pages (90% fill factor)
        min_gb = round(max(0.1, (raw_bytes * 0.85) / (1024 ** 3)), 2)
        # Upper bound assumes lower fill factor (70%) and page splits
        max_gb = round(max(min_gb + 0.2, (raw_bytes * 1.45) / (1024 ** 3)), 2)

        return [min_gb, max_gb]

    @classmethod
    def estimate_write_latency_increase_ms_range(
        cls,
        column_count: int,
        estimated_rows: int,
    ) -> List[float]:
        """
        Estimates additional write amplification during INSERT/UPDATE operations.
        Each secondary index requires an extra B-tree traversal and leaf page lock/write.
        """
        # Base B-Tree traversal tree height: log_100(rows) ~ 2 to 4 levels
        if estimated_rows < 50_000:
            tree_levels = 2
        elif estimated_rows < 1_000_000:
            tree_levels = 3
        else:
            tree_levels = 4

        # Additional write latency: ~0.25ms per tree level + column hashing/comparison
        base_ms = (tree_levels * 0.25) + (column_count * 0.15)
        min_ms = round(max(0.2, base_ms * 0.8), 2)
        max_ms = round(min_ms + (column_count * 0.5), 2)

        return [min_ms, max_ms]

    @classmethod
    def estimate_latency_improvement_percent_range(
        cls,
        planner_cost_reduction_pct: float,
        is_seq_scan_eliminated: bool = True,
    ) -> List[float]:
        """
        Translates planner cost reduction into an expected execution latency improvement range.
        Planner costs have high correlation with actual I/O reduction for table scans.
        """
        if planner_cost_reduction_pct <= 0:
            return [0.0, 0.0]

        if is_seq_scan_eliminated:
            # Eliminating large heap scans yields substantial I/O savings
            min_pct = round(max(10.0, planner_cost_reduction_pct * 0.85), 1)
            max_pct = round(min(98.0, planner_cost_reduction_pct * 1.08), 1)
        else:
            min_pct = round(max(5.0, planner_cost_reduction_pct * 0.70), 1)
            max_pct = round(min(95.0, planner_cost_reduction_pct * 0.95), 1)

        return [min_pct, max_pct]

    @classmethod
    def assess_decision(
        cls,
        planner_cost_reduction_pct: float,
        index_used: bool,
        is_seq_scan_eliminated: bool,
    ) -> Dict[str, Any]:
        """
        Evaluates simulation outcome against QueryGuard acceptance guardrails:
        - Accepted if cost reduction >= 10% OR scan changes Seq -> Index with meaningful reduction.
        - Rejected / No measurable benefit if cost unchanged or index not picked by planner.
        """
        reason_codes: List[str] = []

        if not index_used:
            return {
                "accepted": False,
                "reason_codes": ["INDEX_NOT_SELECTED_BY_PLANNER", "NO_MEASURABLE_BENEFIT"],
                "confidence": "LOW",
                "risk_level": "MEDIUM",
                "recommendation_status": "NO_MEASURABLE_BENEFIT",
            }

        if planner_cost_reduction_pct >= 10.0 or (is_seq_scan_eliminated and planner_cost_reduction_pct >= 5.0):
            reason_codes.append("PLANNER_COST_REDUCED_ABOVE_THRESHOLD")
            if is_seq_scan_eliminated:
                reason_codes.append("SEQUENTIAL_SCAN_CONVERTED_TO_INDEX_SCAN")

            confidence = "HIGH" if planner_cost_reduction_pct >= 40.0 else "MEDIUM"
            risk_level = "LOW"
            return {
                "accepted": True,
                "reason_codes": reason_codes,
                "confidence": confidence,
                "risk_level": risk_level,
                "recommendation_status": "SIMULATION_PASSED",
            }

        return {
            "accepted": False,
            "reason_codes": ["COST_REDUCTION_BELOW_10_PERCENT_THRESHOLD", "MARGINAL_PLANNER_BENEFIT"],
            "confidence": "LOW",
            "risk_level": "LOW",
            "recommendation_status": "NO_MEASURABLE_BENEFIT",
        }

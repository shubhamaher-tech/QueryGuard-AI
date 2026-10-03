"""
QueryGuard AI - Execution Plan to Graph Converter.

Transforms hierarchical execution plan JSON trees into directed graph structures
with node feature matrices and edge connectivity tensors.
"""

from typing import Dict, Any, List, Tuple
from app.ml.feature_encoder import extract_node_features_from_plan_dict
from app.ml.schemas import GraphFeatures

def build_graph_from_plan_dict(root_plan: Dict[str, Any]) -> Tuple[List[List[float]], List[List[int]], List[str], GraphFeatures]:
    """
    Traverse the plan dictionary tree and construct:
    1. node_features: List[List[float]] of size N x 24
    2. edge_index: [sources, targets] of size 2 x E (bidirectional edges between parent and child)
    3. node_operators: List[str] of size N
    4. graph_features: GraphFeatures summary metrics
    """
    node_features: List[List[float]] = []
    node_operators: List[str] = []
    edge_sources: List[int] = []
    edge_targets: List[int] = []

    # Graph summary counters
    join_count = 0
    seq_scan_count = 0
    nested_loop_count = 0
    sort_count = 0
    agg_count = 0
    max_depth = 0
    spill_risk = False

    def traverse(node: Dict[str, Any], depth: int = 0) -> int:
        nonlocal join_count, seq_scan_count, nested_loop_count, sort_count, agg_count, max_depth, spill_risk
        current_idx = len(node_features)
        max_depth = max(max_depth, depth)

        op_type = node.get("Node Type", "Other")
        node_operators.append(op_type)

        # Count operators
        op_lower = op_type.lower()
        if "seq scan" in op_lower:
            seq_scan_count += 1
        elif "nested loop" in op_lower:
            nested_loop_count += 1
            join_count += 1
        elif "hash join" in op_lower or "merge join" in op_lower or "join" in op_lower:
            join_count += 1
        elif "sort" in op_lower:
            sort_count += 1
            if node.get("Sort Space Used", 0) > 10000 or node.get("Sort Method", "").startswith("external"):
                spill_risk = True
        elif "aggregate" in op_lower or "group" in op_lower:
            agg_count += 1

        # Extract 24-dim feature vector
        features = extract_node_features_from_plan_dict(node, depth=depth)
        node_features.append(features)

        # Traverse children (subplans)
        child_plans = node.get("Plans", [])
        for child in child_plans:
            child_idx = traverse(child, depth=depth + 1)
            # Add bidirectional edges: child -> parent (dataflow) and parent -> child (control flow)
            edge_sources.append(child_idx)
            edge_targets.append(current_idx)
            edge_sources.append(current_idx)
            edge_targets.append(child_idx)

        return current_idx

    plan_root = root_plan.get("Plan", root_plan) if isinstance(root_plan, dict) else {}
    traverse(plan_root, depth=0)

    # Edge index tensor representation [[sources...], [targets...]]
    edge_index: List[List[int]] = [edge_sources, edge_targets]

    total_cost = float(plan_root.get("Total Cost", 1.0))
    if total_cost > 10000.0:
        cost_bucket = "HIGH"
    elif total_cost > 1000.0:
        cost_bucket = "MEDIUM"
    else:
        cost_bucket = "LOW"

    graph_features = GraphFeatures(
        plan_depth=max_depth,
        join_count=join_count,
        sequential_scan_count=seq_scan_count,
        nested_loop_count=nested_loop_count,
        sort_count=sort_count,
        aggregate_count=agg_count,
        cost_bucket=cost_bucket,
        total_cost=total_cost,
        spill_risk=spill_risk,
    )

    return node_features, edge_index, node_operators, graph_features

# Alias
build_plan_graph = build_graph_from_plan_dict


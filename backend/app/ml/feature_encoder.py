"""
QueryGuard AI - Privacy-Preserving Plan Node & Graph Feature Encoder.

Encodes execution plan operators into fixed-dimensional numeric feature vectors.
Contains strictly zero relation names, column names, raw literals, or customer data.
"""

import math
from typing import Dict, Any, List

FEATURE_ENCODER_VERSION = "v1"
NODE_FEATURE_DIM = 24

CANONICAL_OPERATORS = [
    "Seq Scan",
    "Index Scan",
    "Bitmap Heap Scan",
    "Nested Loop",
    "Hash Join",
    "Merge Join",
    "Sort",
    "Aggregate",
    "Materialize",
    "Limit",
    "Gather",
    "Other",
]

OP_TO_INDEX = {op: i for i, op in enumerate(CANONICAL_OPERATORS)}
OPERATOR_VOCAB = CANONICAL_OPERATORS

def encode_node_features(
    operator_type: str,
    total_cost: float,
    plan_rows: float,
    startup_cost: float = 0.0,
    depth: int = 0,
    child_count: int = 0,
    has_filter: bool = False,
    has_join_condition: bool = False,
    has_sort_key: bool = False,
    has_group_key: bool = False,
    loops: int = 1,
    relation_size_bucket: str = "SMALL",
    partition_pruning: bool = False,
) -> List[float]:
    """
    Encode an execution plan node into a 24-dimensional normalized float vector.
    """
    features = [0.0] * NODE_FEATURE_DIM

    # 1. Operator One-Hot (dims 0..11)
    normalized_op = "Other"
    for canon in CANONICAL_OPERATORS:
        if canon.lower() in operator_type.lower():
            normalized_op = canon
            break
    op_idx = OP_TO_INDEX.get(normalized_op, OP_TO_INDEX["Other"])
    features[op_idx] = 1.0

    # 2. Normalized log total cost (dim 12) - clipped to [0, 1] assuming max cost 1,000,000
    features[12] = min(1.0, max(0.0, math.log10(max(1.0, float(total_cost))) / 6.0))

    # 3. Normalized log estimated rows (dim 13) - clipped to [0, 1] assuming max rows 100,000,000
    features[13] = min(1.0, max(0.0, math.log10(max(1.0, float(plan_rows))) / 8.0))

    # 4. Normalized startup cost (dim 14)
    features[14] = min(1.0, max(0.0, math.log10(max(1.0, float(startup_cost))) / 6.0))

    # 5. Normalized plan depth (dim 15) - clipped to [0, 1] assuming max depth 15
    features[15] = min(1.0, max(0.0, float(depth) / 15.0))

    # 6. Child count normalized (dim 16) - clipped to [0, 1] assuming max children 5
    features[16] = min(1.0, max(0.0, float(child_count) / 5.0))

    # 7. Structural Flags (dims 17..20)
    features[17] = 1.0 if has_filter else 0.0
    features[18] = 1.0 if has_join_condition else 0.0
    features[19] = 1.0 if has_sort_key else 0.0
    features[20] = 1.0 if has_group_key else 0.0

    # 8. Execution Loops normalized (dim 21)
    features[21] = min(1.0, max(0.0, math.log10(max(1.0, float(loops))) / 5.0))

    # 9. Relation Size Bucket (dim 22): SMALL=0.0, MEDIUM=0.5, LARGE=1.0
    size_map = {"SMALL": 0.0, "MEDIUM": 0.5, "LARGE": 1.0}
    features[22] = size_map.get(relation_size_bucket.upper(), 0.0)

    # 10. Partition Pruning flag (dim 23)
    features[23] = 1.0 if partition_pruning else 0.0

    return features

def extract_node_features_from_plan_dict(node_dict: Dict[str, Any], depth: int = 0) -> List[float]:
    """Extract node features directly from a sanitized or raw EXPLAIN node dictionary."""
    op_type = node_dict.get("Node Type", "Other")
    cost = float(node_dict.get("Total Cost", 1.0))
    rows = float(node_dict.get("Plan Rows", 1.0))
    startup = float(node_dict.get("Startup Cost", 0.0))
    children = len(node_dict.get("Plans", []))

    has_filter = bool(node_dict.get("Filter"))
    has_join = bool(node_dict.get("Hash Cond") or node_dict.get("Join Filter") or node_dict.get("Index Cond"))
    has_sort = bool(node_dict.get("Sort Key"))
    has_group = bool(node_dict.get("Group Key") or "Aggregate" in op_type)
    loops = int(node_dict.get("Actual Loops", 1))

    # Estimate size bucket from rows
    if rows > 100000:
        size_bucket = "LARGE"
    elif rows > 1000:
        size_bucket = "MEDIUM"
    else:
        size_bucket = "SMALL"

    return encode_node_features(
        operator_type=op_type,
        total_cost=cost,
        plan_rows=rows,
        startup_cost=startup,
        depth=depth,
        child_count=children,
        has_filter=has_filter,
        has_join_condition=has_join,
        has_sort_key=has_sort,
        has_group_key=has_group,
        loops=loops,
        relation_size_bucket=size_bucket,
        partition_pruning=bool(node_dict.get("Subplans Removed", 0) > 0),
    )

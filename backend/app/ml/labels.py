"""
QueryGuard AI - Machine Learning Bottleneck Labels & Classification Categories.

Truthfulness Statement:
GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans.
"""

from typing import List, Dict

# Canonical bottleneck class labels
LABEL_SEQ_SCAN = "SEQ_SCAN_BOTTLENECK"
LABEL_NESTED_LOOP = "NESTED_LOOP_BOTTLENECK"
LABEL_EXPENSIVE_SORT = "EXPENSIVE_SORT"
LABEL_HASH_JOIN = "HASH_JOIN_HEAVY"
LABEL_AGGREGATION = "AGGREGATION_HEAVY"
LABEL_OPTIMIZED = "GOOD_OR_OPTIMIZED_PLAN"
LABEL_CARDINALITY_RISK = "CARDINALITY_ESTIMATION_RISK"

BOTTLENECK_CLASSES: List[str] = [
    LABEL_SEQ_SCAN,
    LABEL_NESTED_LOOP,
    LABEL_EXPENSIVE_SORT,
    LABEL_HASH_JOIN,
    LABEL_AGGREGATION,
    LABEL_OPTIMIZED,
    LABEL_CARDINALITY_RISK,
]

LABEL_TO_ID: Dict[str, int] = {label: idx for idx, label in enumerate(BOTTLENECK_CLASSES)}
ID_TO_LABEL: Dict[int, str] = {idx: label for idx, label in enumerate(BOTTLENECK_CLASSES)}

LABEL_METADATA: Dict[str, Dict[str, str]] = {
    LABEL_SEQ_SCAN: {
        "title": "Sequential Scan Bottleneck",
        "description": "High-volume sequential table scan across unindexed relation heap pages.",
        "primary_operator": "Seq Scan",
        "severity": "HIGH",
    },
    LABEL_NESTED_LOOP: {
        "title": "Nested Loop Join Multiplier",
        "description": "Inner relation repeatedly scanned per outer row with unindexed join conditions.",
        "primary_operator": "Nested Loop",
        "severity": "HIGH",
    },
    LABEL_EXPENSIVE_SORT: {
        "title": "Expensive Sort / Memory Spill",
        "description": "High sort cost or work_mem exhaustion forcing external merge sort.",
        "primary_operator": "Sort",
        "severity": "MEDIUM",
    },
    LABEL_HASH_JOIN: {
        "title": "Heavy Hash Join Pipeline",
        "description": "Multi-batch hash table construction across wide intermediate join relations.",
        "primary_operator": "Hash Join",
        "severity": "MEDIUM",
    },
    LABEL_AGGREGATION: {
        "title": "Heavy Aggregation / Grouping",
        "description": "High row count GroupBy or window aggregation dominating plan cost.",
        "primary_operator": "Aggregate",
        "severity": "MEDIUM",
    },
    LABEL_OPTIMIZED: {
        "title": "Optimized / Well-Indexed Plan",
        "description": "Execution plan efficiently uses B-tree Index Scans or Bitmap Scans with low cost.",
        "primary_operator": "Index Scan",
        "severity": "LOW",
    },
    LABEL_CARDINALITY_RISK: {
        "title": "Cardinality Estimation Risk",
        "description": "Severe estimation discrepancy leading to suboptimal join operator selection.",
        "primary_operator": "Hash Join",
        "severity": "MEDIUM",
    },
}

# Aliases for backward/forward compatibility
CLASS_TO_ID = LABEL_TO_ID
ID_TO_CLASS = ID_TO_LABEL
CLASS_METADATA = LABEL_METADATA

SEQ_SCAN_BOTTLENECK = LABEL_SEQ_SCAN
NESTED_LOOP_BOTTLENECK = LABEL_NESTED_LOOP
EXPENSIVE_SORT = LABEL_EXPENSIVE_SORT
HASH_JOIN_HEAVY = LABEL_HASH_JOIN
AGGREGATION_HEAVY = LABEL_AGGREGATION
GOOD_OR_OPTIMIZED_PLAN = LABEL_OPTIMIZED
CARDINALITY_ESTIMATION_RISK = LABEL_CARDINALITY_RISK


# GNN v2 Retraining & Benchmark Plan Expansion

## 1. Overview

QueryGuard AI's experimental Graph Neural Network (GNN) bottleneck classifier was expanded from `v1_synthetic` (140 plans) to `v2_synthetic_tpch_postgres` (245 plans).

The expanded dataset incorporates sanitized execution plans extracted from both transactional e-commerce queries and standard TPC-H decision-support query templates.

---

## 2. Dataset Expansion Summary

| Metric | `v1_synthetic` | `v2_synthetic_tpch_postgres` | Growth |
|---|---|---|---|
| **Total Plan Graphs** | 140 | 245 | +75% |
| **Samples per Class** | 20 | 35 | +75% |
| **Supported Classes** | 7 | 7 | Consistent |
| **Workload Domains** | E-Commerce OLTP | E-Commerce OLTP + TPC-H OLAP | Multi-domain |
| **Feature Dimension** | 24 | 24 | Preserved |
| **Zero Raw SQL / Data** | Verified (100%) | Verified (100%) | Strict Privacy |

### Bottleneck Classes (35 samples each in v2)
1. `SEQ_SCAN_BOTTLENECK` — Sequential scans on large tables (e.g. `lineitem`, `transactions`).
2. `NESTED_LOOP_BOTTLENECK` — Inefficient loops with high outer cardinality.
3. `EXPENSIVE_SORT` — External disk merge sorts exceeding `work_mem`.
4. `HASH_JOIN_HEAVY` — Large multi-table analytical joins.
5. `AGGREGATION_HEAVY` — Heavy multi-column grouping and aggregation.
6. `GOOD_OR_OPTIMIZED_PLAN` — Optimal index-supported lookups.
7. `CARDINALITY_ESTIMATION_RISK` — Subquery predicates with extreme cardinality underestimation.

---

## 3. Retraining Results (`gnn_bottleneck_v2`)

Retraining was executed using 40 epochs of Adam optimization (`lr=0.005`) with a 70/15/15 train/val/test split:

- **Overall Test Accuracy:** **94.6%**
- **Macro F1 Score:** **0.948**
- **Per-Class Metrics:**
  - `SEQ_SCAN_BOTTLENECK`: Precision 0.71, Recall 1.00, F1 0.83
  - `NESTED_LOOP_BOTTLENECK`: Precision 1.00, Recall 1.00, F1 1.00
  - `EXPENSIVE_SORT`: Precision 1.00, Recall 1.00, F1 1.00
  - `HASH_JOIN_HEAVY`: Precision 1.00, Recall 1.00, F1 1.00
  - `AGGREGATION_HEAVY`: Precision 1.00, Recall 0.67, F1 0.80
  - `GOOD_OR_OPTIMIZED_PLAN`: Precision 1.00, Recall 1.00, F1 1.00
  - `CARDINALITY_ESTIMATION_RISK`: Precision 1.00, Recall 1.00, F1 1.00

---

## 4. Model Versioning & Dynamic Selection

Both model checkpoints are preserved in `backend/artifacts/models/`:
- `gnn_bottleneck_v1.pt` & `gnn_bottleneck_v1.metadata.json` (Baseline)
- `gnn_bottleneck_v2.pt` & `gnn_bottleneck_v2.metadata.json` (TPC-H Expanded)

The frontend **Benchmark Datasets** view includes a model checkpoint switcher:
- Calls `GET /api/ml/gnn/models` to display available models with their accuracy and training dates.
- Calls `POST /api/ml/gnn/select-model?model_version=gnn_bottleneck_v2` to dynamically switch the active inference model without restarting containers.

---

## 5. Truthfulness Statement

> [!NOTE]
> The GNN model is an **experimental research proof-of-concept** trained on synthetic and benchmark plan graphs. 
> The deterministic rule-based analysis engine remains the authoritative source of recommendations. 
> Whenever the GNN disagrees with the rule engine or confidence is below 0.65, QueryGuard AI alerts the user and defaults to deterministic recommendations.

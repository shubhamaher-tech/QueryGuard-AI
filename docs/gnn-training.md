# Experimental Plan Graph Neural Network (GNN) for Bottleneck Classification

> [!IMPORTANT]
> **Truthfulness & Provenance Disclosure**:
> The QueryGuard AI GNN bottleneck classifier is an **experimental proof-of-concept trained exclusively on synthetic sanitized benchmark execution plans**. It is **not** trained on real customer data, production queries, or cloud datasets. The deterministic rule engine remains the primary and authoritative recommendation source; human DBA approval is required before any schema change.

---

## 1. Motivation: Graph Representations of Database Plans

PostgreSQL execution plans (`EXPLAIN (FORMAT JSON)`) are hierarchical operator trees (e.g., `Aggregate` $\to$ `Sort` $\to$ `Nested Loop` $\to$ `Seq Scan`). While traditional database copilots treat SQL as sequential text, the relational engine executes operators as directed acyclic dataflow and control graphs.

Graph Neural Networks (GNNs) provide inductive bias for:
1. **Hierarchical Topology**: Preserving parent-child dataflow relationships without flattening or sequence padding.
2. **Operator Neighborhood Context**: Allowing parent join nodes to aggregate contextual cost and row distributions from child scan nodes.
3. **Strict Privacy Boundaries**: Operating strictly over structural node features and topological connectivity, requiring zero raw SQL, literal values, or plaintext table/column names.

---

## 2. Privacy & Zero-Raw Data Guarantees

Every graph record in the synthetic training dataset and live inference pipeline adheres to strict privacy boundaries:

| Dimension | Guarantee | Verification Mechanism |
| :--- | :--- | :--- |
| **SQL Text** | Never passed to GNN | Sanitized HMAC query template or empty |
| **Relation Names** | Tokenized to HMAC tokens (`TBL_REL_9F8E`) | Checked against blacklist (`transactions`, `customers`) |
| **Column Names** | Tokenized to HMAC tokens (`COL_KEY_1`) | No customer column identifiers persisted |
| **Query Literals** | Replaced with placeholders (`:INT`, `:STR`) | Regex validation rejects unmasked quotes (`'...'`) |
| **Row Content** | Completely absent | EXPLAIN plan contains only planner metadata |
| **Compute Locality** | 100% Local / On-Premises | Zero cloud API egress (no OpenAI, Gemini, or Anthropic) |

---

## 3. Fixed 24-Dimensional Node Feature Vector

Each execution-plan operator node is converted into a normalized 24-dimensional float vector:

| Indices | Dimension | Description | Normalization |
| :--- | :--- | :--- | :--- |
| **0 - 11** | Operator Type | One-hot encoding across 12 canonical operators (`Seq Scan`, `Index Scan`, `Bitmap Heap Scan`, `Nested Loop`, `Hash Join`, `Merge Join`, `Sort`, `Aggregate`, `Materialize`, `Limit`, `Gather`, `Other`) | $\{0.0, 1.0\}$ |
| **12** | Log Total Cost | Total planner cost assigned to node | $\min(1.0, \max(0.0, \log_{10}(\text{cost}) / 6.0))$ |
| **13** | Log Plan Rows | Estimated rows produced by node | $\min(1.0, \max(0.0, \log_{10}(\text{rows}) / 8.0))$ |
| **14** | Startup Cost | Initial cost to return first row | $\min(1.0, \max(0.0, \log_{10}(\text{startup}) / 6.0))$ |
| **15** | Plan Depth | Distance from root in plan tree | $\min(1.0, \text{depth} / 15.0)$ |
| **16** | Child Count | Direct child subplans attached | $\min(1.0, \text{children} / 5.0)$ |
| **17** | Filter Flag | Node contains `Filter` predicate | $1.0$ if present else $0.0$ |
| **18** | Join Condition | Node contains `Hash Cond`, `Index Cond`, etc. | $1.0$ if present else $0.0$ |
| **19** | Sort Key Flag | Node contains `Sort Key` specification | $1.0$ if present else $0.0$ |
| **20** | Group Key Flag | Node contains `Group Key` or grouping aggregation | $1.0$ if present else $0.0$ |
| **21** | Execution Loops | Number of times node executed (`Actual Loops`) | $\min(1.0, \log_{10}(\text{loops}) / 5.0)$ |
| **22** | Relation Size | Estimated relation size bucket | $\text{SMALL}=0.0, \text{MEDIUM}=0.5, \text{LARGE}=1.0$ |
| **23** | Partition Pruning | Subplans removed via partition pruning | $1.0$ if true else $0.0$ |

---

## 4. Graph Construction & Message Passing Architecture

### 4.1 Topology
For each plan tree:
- **Nodes ($V$)**: Every operator node has a 24-dimensional feature vector $x_v \in \mathbb{R}^{24}$.
- **Edges ($E$)**: Bidirectional directed edges are added between each parent node and its child nodes ($2 \times E$). Parent-to-child edges represent control flow; child-to-parent edges represent dataflow row pipelines.

### 4.2 Pure PyTorch GraphSAGE Implementation
To eliminate compiled C++ binary dependencies (such as `torch-geometric`, `torch-scatter`, or `torch-sparse` which frequently fail on Windows or minimal Linux containers), the model implements GraphSAGE using standard PyTorch operations:

```python
class GraphSAGEConv(nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.linear_self = nn.Linear(in_dim, out_dim, bias=False)
        self.linear_neigh = nn.Linear(in_dim, out_dim, bias=False)
        self.bias = nn.Parameter(torch.zeros(out_dim))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        # edge_index: [2, E] (sources, targets)
        src, dst = edge_index[0], edge_index[1]
        
        # Mean neighborhood aggregation using torch.index_add_
        neigh_sum = torch.zeros_like(x)
        neigh_sum.index_add_(0, dst, x[src])
        degree = torch.zeros(x.size(0), 1, device=x.device)
        degree.index_add_(0, dst, torch.ones(src.size(0), 1, device=x.device))
        neigh_mean = neigh_sum / degree.clamp(min=1.0)
        
        out = self.linear_self(x) + self.linear_neigh(neigh_mean) + self.bias
        return F.relu(out)
```

### 4.3 Graph Pooling & Classification
The complete model (`PlanGNNClassifier`):
1. **Layer 1**: GraphSAGEConv ($24 \to 64$) + ReLU + Dropout ($0.2$)
2. **Layer 2**: GraphSAGEConv ($64 \to 64$) + ReLU
3. **Readout / Pooling**: Global Mean Pooling + Root Node Embedding concatenation ($64 + 64 = 128$)
4. **Classifier Head**: Linear ($128 \to 32$) + ReLU + Linear ($32 \to 7$ classes)

---

## 5. The 7 Canonical Bottleneck Classes

1. `SEQ_SCAN_BOTTLENECK`: High-volume sequential table scan across unindexed relation heap pages.
2. `NESTED_LOOP_BOTTLENECK`: Inner relation repeatedly scanned per outer row with unindexed join conditions.
3. `EXPENSIVE_SORT`: High sort cost or work_mem exhaustion forcing external merge sort.
4. `HASH_JOIN_HEAVY`: Multi-batch hash table construction across wide intermediate join relations.
5. `AGGREGATION_HEAVY`: High row count GroupBy or window aggregation dominating plan cost.
6. `GOOD_OR_OPTIMIZED_PLAN`: Execution plan efficiently uses B-tree Index Scans or Bitmap Scans with low cost.
7. `CARDINALITY_ESTIMATION_RISK`: Severe estimation discrepancy leading to suboptimal join operator selection.

---

## 6. Offline Benchmark Evaluation Results

The model was evaluated using a 70% Train / 15% Val / 15% Test stratified holdout split on 140 synthetic plan graphs generated from `workload-postgres`:

| Metric | Benchmark Result | Target / Baseline |
| :--- | :--- | :--- |
| **Test Accuracy** | **100.0%** | $\ge 75.0\%$ |
| **Macro F1-Score** | **1.000** | $\ge 0.700$ |
| **Inference Latency** | **&lt; 5 ms** (CPU) | $\le 50 \text{ ms}$ |
| **Memory Footprint** | **&lt; 85 KB** (`.pt` checkpoint) | $\le 50 \text{ MB}$ |

### Per-Class Test Holdout Metrics
| Bottleneck Class | Precision | Recall | F1-Score | Test Support |
| :--- | :---: | :---: | :---: | :---: |
| `SEQ_SCAN_BOTTLENECK` | 100.0% | 100.0% | 1.000 | 3 |
| `NESTED_LOOP_BOTTLENECK` | 100.0% | 100.0% | 1.000 | 3 |
| `EXPENSIVE_SORT` | 100.0% | 100.0% | 1.000 | 3 |
| `HASH_JOIN_HEAVY` | 100.0% | 100.0% | 1.000 | 3 |
| `AGGREGATION_HEAVY` | 100.0% | 100.0% | 1.000 | 3 |
| `GOOD_OR_OPTIMIZED_PLAN` | 100.0% | 100.0% | 1.000 | 3 |
| `CARDINALITY_ESTIMATION_RISK` | 100.0% | 100.0% | 1.000 | 3 |

---

## 7. Limitations & Production Safety Architecture

> [!CAUTION]
> **Why Synthetic Benchmark Plans Have Perfect Separation**:
> The high accuracy observed in the synthetic benchmark is a direct result of carefully generated topological signatures in the synthetic workload. Real-world database execution plans exhibit high variance, nested CTE subqueries, and non-linear cost shifts.
> 
> Therefore, QueryGuard AI implements a **Defense-in-Depth Hybrid Architecture**:
> 1. **Rule Engine as Primary Authority**: The deterministic rule engine (`app/analyzer.py` and `app/telemetry/analyzer.py`) is the authoritative source for recommendations.
> 2. **GNN as Advisory Evidence**: The GNN prediction is presented in the UI as an auxiliary evidence signal.
> 3. **Disagreement Detection**: If the GNN prediction diverges from the deterministic rule diagnosis, the divergence is explicitly flagged in the dashboard, and the rule engine takes precedence.
> 4. **Confidence Gating**: Any prediction with confidence $< 0.65$ is tagged as `Low Confidence` and suppressed from influencing optimization severity.
> 5. **Mandatory Human Sign-Off**: No optimization is ever deployed automatically.

---

## 8. CLI & Reproduction Commands

### Generate Synthetic Plan Graph Dataset
```bash
python scripts/generate_plan_dataset.py --samples-per-class 20
```

### Train GNN Model
```bash
python scripts/train_gnn_model.py --epochs 60 --lr 0.005
```

### Evaluate Checkpoint
```bash
python scripts/evaluate_gnn_model.py
```

### Isolated ML Container Profile
To run with PyTorch in an isolated container without bloating the default backend image:
```bash
docker compose --profile ml up -d --build
```

---

## 9. Required Presentation Truthfulness Language

When presenting or demoing this capability to stakeholders or hackathon judges, QueryGuard AI strictly uses the following language:

> **Official Disclosure Statement:**  
> “Experimental GNN bottleneck classifier trained only on locally generated, sanitized synthetic PostgreSQL plan graphs. It supports but does not replace rule-based diagnosis, HypoPG simulation, or DBA approval.”

Key Presentation Points:
1. **Advisory Signal**: GNN operates as a secondary classification signal inside the execution-plan diagnostic flow:
   $$\text{Sanitized EXPLAIN JSON} \to \text{Plan Graph} \to \text{Rule-Based Diagnosis} \to \text{GNN Signal} \to \text{XAI Merger} \to \text{HypoPG Simulation} \to \text{DBA Approval}$$
2. **Authority Hierarchy**: The deterministic rule engine remains the primary and authoritative recommendation source.
3. **No Autonomous Deployment**: The GNN never executes DDL, never creates physical indexes, and never approves changes.

---

## 10. Future Roadmap: Subgraph Attribution with GNNExplainer

1. **Topological Subgraph Attribution**: Integrate `PGExplainer` or `GNNExplainer` to identify the specific sub-graph paths (e.g. `Seq Scan` $\to$ `Nested Loop`) most influential in driving the bottleneck classification.
2. **Graph Edit Distance for Rewrite Suggestions**: Compare the graph structure of candidate SQL rewrites against baseline query plans to predict optimization feasibility before sandbox EXPLAIN.
3. **Multi-Task Topology & Latency Prediction**: Extend node representation vectors to jointly predict operator bottleneck categories and approximate relative execution time distributions.


# QueryGuard AI - Interactive Query Analysis Workspace

## Overview

The **Interactive Query Analysis Workspace** (`/analyze-query`) is a real-time, privacy-first SQL performance tuning sandbox built for Database Administrators (DBAs), site reliability engineers, and performance architects. It allows practitioners to safely paste and profile arbitrary `SELECT` queries against local synthetic benchmarks (such as E-Commerce or TPC-H SF 0.1), visualize the full PostgreSQL execution plan as an SVG DAG, diagnose primary bottlenecks, inspect 2-layer GraphSAGE Graph Neural Network (GNN) predictions, simulate candidate index impacts using in-memory **HypoPG**, and exercise human approval before any physical database change is made.

---

## Architecture & Data Flow

```
[ DBA Query Editor ]
       │
       ▼
[ Strict Safety Gateway ] ──(DML / Comments / Multi-stmt / Dangerous Fn)──► [ Immediate Rejection ]
       │
       ▼ (Valid Single SELECT)
[ Privacy Engine ] ───────────────────────────────────────────────────────► [ HMAC-SHA256 Tokenization ]
       │ (AstLiteralMasking)                                                 [ Literal Masking (:INT, :STR) ]
       ▼
[ Sandboxed In-Memory EXPLAIN ] (workload-postgres)
  • SET LOCAL default_transaction_read_only = on;
  • SET LOCAL statement_timeout = '5s';
  • SET LOCAL lock_timeout = '2s';
       │
       ├──► Raw SQL immediately dereferenced & deleted from RAM
       ▼
[ Execution Plan Parser & Plan Graph Builder ]
       │
       ├──► Rule-Based Bottleneck Heuristics (Seq Scan, Nested Loop, Sort Memory)
       ├──► 2-Layer GraphSAGE GNN Inference (Structural plan classification)
       └──► HypoPG What-If Index Simulation (Session RAM only — zero disk mutation)
       │
       ▼
[ QueryGuard App Database (queryguard-postgres) ]
  • ONLY masked template stored (e.g. SELECT COL_A FROM TBL_B WHERE COL_A = %(INT)s)
  • ZERO raw literals, zero customer data, zero raw table/column names
       │
       ▼
[ Progressive 7-Tab Results View & Human Approval Gateway ]
```

---

## Strict Safety & Privacy Invariants

QueryGuard AI enforces non-negotiable security boundaries before any query reaches the execution engine:

| Invariant | Implementation | Error Code |
| :--- | :--- | :--- |
| **SELECT-Only** | Strict rejection of `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, `SET`. | `SAFETY_VIOLATION_DML_DETECTED` |
| **No SQL Comments** | Blocks `--` and `/* ... */` to prevent SQL obfuscation and filter evasion. | `SAFETY_VIOLATION_COMMENTS_FORBIDDEN` |
| **Single-Statement** | Rejects queries with internal semicolons or multiple AST roots. | `SAFETY_VIOLATION_MULTI_STATEMENT` |
| **Dangerous Functions** | Blocks `pg_sleep`, `pg_read_file`, `pg_write_file`, `pg_terminate_backend`, `dblink`, `query_to_xml`, `version`, `current_user`. | `SAFETY_VIOLATION_DANGEROUS_FUNCTION` |
| **Relation Allowlists** | Enforces dataset-specific tables (`transactions`, `customers`, etc. for E-Commerce; `tpch_*` for TPC-H). Rejects catalog tables (`pg_catalog`, `information_schema`). | `SAFETY_VIOLATION_UNAPPROVED_RELATION` |
| **Resource Bounds** | Max query length: 5,000 characters; Max joins: 15; Max AST nesting depth: 10. | `SAFETY_VIOLATION_EXCESSIVE_*` |
| **Zero Raw Data** | `EXPLAIN (FORMAT JSON)` is executed; `EXPLAIN ANALYZE` is never used. No result rows or raw customer data are ever ingested. | `AstLiteralMasking + HmacIdentifierTokenization` |

---

## Progressive 7-Tab Results Layout

The workspace displays results across 7 comprehensive tabs:

### 1. Overview & Decision
- **KPI Metrics**: Baseline Planner Cost, Simulated Cost with Virtual Index, Cost Reduction Percentage, GNN Prediction & Confidence.
- **Diagnosis Summary**: Plain-English explanation of detected bottlenecks.
- **Human DBA Approval Gateway**: Form to approve or reject recommendations with custom review rationale.

### 2. Execution Plan (SVG Canvas)
- Interactive Directed Acyclic Graph (DAG) visualizing every operator node (`Seq Scan`, `Index Scan`, `Nested Loop`, `Sort`, `Aggregate`).
- Color-coded operators, cost percentages, row estimate buckets, and bottleneck highlighting.
- Zoom, pan, and inspector drawer.

### 3. Recommendations
- Actionable tuning proposals (e.g. Composite B-Tree Index, Foreign Key Index, Ordered B-Tree Index).
- Exact, syntactically verified DDL statements with one-click copy (`CREATE INDEX CONCURRENTLY idx_...`).
- Operational risk score and estimated improvement gain.

### 4. Simulation Impact (Before vs After)
- Side-by-side cost comparison: Baseline Optimizer Cost vs HypoPG Virtual Index Cost.
- Operational metrics: Estimated read latency gain, write latency overhead (ms) on `INSERT`/`UPDATE`, storage footprint estimate (MB).
- Honesty label: *"Rule-based plan graph analysis with HypoPG planner simulation; GNN/RL-ready architecture."*

### 5. Explainability (Rule + GNN Signals)
- **Rule Heuristic Signals**: Clear triggers explaining why the rule engine flagged specific operators.
- **GNN Classifier Probabilities**: Top-3 predicted bottleneck classes with probability bars from the 2-layer GraphSAGE model.
- **Agreement Status**: Confirms alignment between rule heuristics and machine learning signals.

### 6. Technical Evidence (Masked-Only)
- Full masked query template with typed placeholders (`%(INT)s`, `%(STRING)s`, `%(DATE)s`).
- Deterministic HMAC-SHA256 query fingerprint.
- Tokenized relation identifiers (`TBL_2CF5B555`, `COL_2C9A2CAB`).
- Raw EXPLAIN JSON inspector.

### 7. Audit Timeline
- Tamper-evident, chronological log of all analysis and approval events (`INTERACTIVE_QUERY_ANALYZED`, `ANALYSIS_APPROVED`).
- Recorded with actor identity (`DBA_ADMIN_01` / Lead DBA), timestamp, and non-repudiation metadata.

---

## API Reference

### `POST /api/analyze-query`
Analyzes a user-submitted SQL query in the sandbox.
```json
{
  "query": "SELECT region_id, count(*) FROM transactions WHERE region_id = 5 GROUP BY region_id;",
  "dataset": "synthetic_ecommerce",
  "options": {}
}
```

### `GET /api/analyze-query/{analysis_id}`
Retrieves existing analysis job details.

### `GET /api/analyze-query/{analysis_id}/events`
Server-Sent Events (SSE) progress stream emitting real-time stage progression (`text/event-stream`).

### `POST /api/analyze-query/{analysis_id}/approve`
Records DBA approval for an analysis recommendation.
```json
{
  "decision": "APPROVED",
  "reason": "Verified low write risk on synthetic workload replica",
  "actor": "Lead DBA"
}
```

### `POST /api/analyze-query/{analysis_id}/reject`
Records DBA rejection.

### `GET /api/benchmarks/status`
Returns metadata and availability for all registered benchmark datasets.

### `GET /api/benchmarks/sample-queries`
Returns curated, safe sample queries filtered optionally by `?dataset=tpch_sf01`.

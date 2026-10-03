# QueryGuard AI - Local PostgreSQL Workload Telemetry Pipeline

QueryGuard AI includes a dedicated, privacy-preserving telemetry collection pipeline designed to extract PostgreSQL execution metrics from a benchmark workload database, sanitize all sensitive schema identifiers and literal values locally in memory, and persist only structurally masked graph metadata into the QueryGuard governance repository.

---

## 🏗️ Architecture & Telemetry Data Flow

```mermaid
flowchart TD
    subgraph WorkloadDB["Synthetic Workload Database (workload-postgres:5433)"]
        W_PG["PostgreSQL 16 + pg_stat_statements"]
        W_Data["Synthetic Tables\n(regions, customers, products, transactions, order_items)"]
        W_User["Read-Only Collector User (workload_ro)"]
        W_Stats["pg_stat_statements View"]
        W_Explain["EXPLAIN (FORMAT JSON)\n(No ANALYZE, Zero Execution)"]
    end

    subgraph BackendPipeline["QueryGuard Telemetry Engine (FastAPI Backend)"]
        Collector["app/telemetry/collector.py\nAllow-list filter & aggregate reader"]
        Sanitizer["app/telemetry/sanitizer.py\nsqlglot AST parser + HMAC-SHA256 Tokenizer"]
        Scanner["Privacy Scanner Barrier\n(Rejects literals, comments, schema leaks)"]
        Parser["app/telemetry/plan_parser.py\nGraph extractor & Rule-based XAI analyzer"]
        Service["app/telemetry/service.py\nOrchestrator & persistence coordinator"]
    end

    subgraph AppDB["QueryGuard Application Database (postgres:5432)"]
        Runs["telemetry_collection_runs"]
        Events["telemetry_events\n(Sanitized Fingerprints & Buckets)"]
        Nodes["sanitized_plan_nodes"]
        Edges["sanitized_plan_edges"]
        Audit["audit_logs"]
    end

    subgraph FrontendUI["DBA Dashboard (Next.js 14)"]
        TelemetryPage["/telemetry (Status & Event Catalog)"]
        PlanGraph["/telemetry/[id] (React Flow Plan Graph & XAI)"]
        TriggerBtn["'Collect Workload Telemetry' Trigger"]
    end

    %% Flow Steps
    TriggerBtn -->|POST /api/telemetry/collect| Service
    Service --> Collector
    Collector -->|SELECT allow-listed stats| W_Stats
    Collector -->|EXPLAIN (FORMAT JSON)| W_Explain
    Collector -->|Raw benchmark SQL & Plan| Sanitizer
    Sanitizer -->|Masked AST & Tokens| Scanner
    Scanner -->|Validated Safe Metadata| Parser
    Parser -->|Graph Nodes/Edges + XAI Packet| Service
    Service -->|Persist Tokenized Data| Runs
    Service --> Events
    Service --> Nodes
    Service --> Edges
    Service --> Audit
    TelemetryPage -->|GET /api/telemetry/events| Service
    PlanGraph -->|GET /api/telemetry/events/:id| Service
```

---

## 🔒 Multi-Stage Privacy & Sanitization Architecture

The telemetry pipeline guarantees zero raw data ingestion through an isolated four-stage in-memory barrier:

```
Raw Query from Workload DB
          │
          ▼
┌───────────────────────────────────────────────┐
│ Stage 1: AST Parser & Literal Masking         │
│ - sqlglot parses SQL syntax tree              │
│ - Integers / Floats  ──► :INT / :NUMERIC      │
│ - String Literals    ──► :STRING              │
│ - Timestamps / Dates ──► :DATE / :TIMESTAMP   │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│ Stage 2: HMAC-SHA256 Tokenization             │
│ - Keyed with HMAC_TOKEN_SECRET                │
│ - Table names   ──► TBL_<8-char-hex>          │
│ - Column names  ──► COL_<8-char-hex>          │
│ - Aliases       ──► ALIAS_<8-char-hex>        │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│ Stage 3: Privacy Verification Barrier         │
│ - Regex scan for residual literal patterns    │
│ - Checks for single quotes, numbers, comments │
│ - Verifies no plaintext schema names exist    │
│ - Violations raise PrivacyViolationException  │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│ Stage 4: Metric Bucketing                     │
│ - Execution latency ──► '<10ms', '100-500ms'  │
│ - Calls count       ──► '10-50 calls'         │
│ - Rows affected     ──► '10k-50k rows'        │
└───────────────────────────────────────────────┘
```

### Sanitization Before & After Example

#### Raw Benchmark SQL (Read-only Synthetic Workload)
```sql
SELECT t.id, t.transaction_date, c.name, p.product_name, oi.quantity
FROM transactions t
JOIN customers c ON t.customer_id = c.id
JOIN order_items oi ON oi.transaction_id = t.id
JOIN products p ON oi.product_id = p.id
WHERE t.region_id = 5
  AND t.transaction_date >= '2026-01-01'
ORDER BY t.transaction_date DESC
LIMIT 50;
```

#### Masked & Tokenized Template Persisted in Application Database
```sql
SELECT
  ALIAS_9E85F0BC.COL_07D0E600,
  ALIAS_9E85F0BC.COL_48CF2A96,
  ALIAS_F1991F19.COL_619EB5EE,
  ALIAS_EB6FDDF1.COL_CE0912FE,
  ALIAS_300B5B33.COL_4F69B9E7
FROM TBL_B1DEB666 AS ALIAS_9E85F0BC
JOIN TBL_017C8A97 AS ALIAS_F1991F19 ON ALIAS_9E85F0BC.COL_4E87EF1E = ALIAS_F1991F19.COL_07D0E600
JOIN TBL_2574A929 AS ALIAS_300B5B33 ON ALIAS_300B5B33.COL_404C9199 = ALIAS_9E85F0BC.COL_07D0E600
JOIN TBL_A265E9AE AS ALIAS_EB6FDDF1 ON ALIAS_300B5B33.COL_3E1E0943 = ALIAS_EB6FDDF1.COL_07D0E600
WHERE ALIAS_9E85F0BC.COL_ED1DFE5F = :INT
  AND ALIAS_9E85F0BC.COL_48CF2A96 >= :DATE
ORDER BY ALIAS_9E85F0BC.COL_48CF2A96 DESC
LIMIT :INT
```

---

## 📊 Allow-Listed Metrics & Fields

QueryGuard enforces an explicit allow-list for statistics gathered from `pg_stat_statements` and plan metadata:

| Scope | Allow-Listed Field | Purpose |
| :--- | :--- | :--- |
| **Workload Aggregate** | `queryid` | Stable numerical hash identifier |
| **Workload Aggregate** | `calls` | Frequency of execution |
| **Workload Aggregate** | `total_exec_time` | Total cumulative time in milliseconds |
| **Workload Aggregate** | `mean_exec_time` | Average query execution time |
| **Workload Aggregate** | `min_exec_time` | Minimum observed query execution time |
| **Workload Aggregate** | `max_exec_time` | Maximum observed query execution time |
| **Workload Aggregate** | `rows` | Aggregate rows returned |
| **Workload Buffer I/O**| `shared_blks_hit` | Buffer pool cache hits |
| **Workload Buffer I/O**| `shared_blks_read`| Disk blocks read from tablespace |
| **Workload Buffer I/O**| `temp_blks_read` | Work memory overflow reads from disk |
| **Workload Buffer I/O**| `temp_blks_written`| Spill blocks written to disk |
| **Plan Structure** | `Node Type` | Operator classification (`Seq Scan`, `Sort`, `Nested Loop`) |
| **Plan Structure** | `Startup Cost` / `Total Cost` | Planner cost coefficients |
| **Plan Structure** | `Plan Rows` / `Plan Width` | Selectivity and tuple width |

### Strictly Forbidden / Excluded from Collection
- ❌ **No `EXPLAIN ANALYZE`**: Never executes the query during analysis, preventing side effects or server load.
- ❌ **No Result Rows**: Query results are never retrieved or stored.
- ❌ **No Unsanitized Literals**: Numeric arguments, dates, strings, and UUIDs are masked.
- ❌ **No Plaintext Identifiers**: Schema, table, and column names are tokenized with HMAC-SHA256.
- ❌ **No Untrusted User SQL**: The collector exclusively queries known synthetic benchmark fingerprints.

---

## 🧠 Explainable AI (XAI) & Plan Graph Analysis

The plan parser analyzes execution trees deterministically, mapping each planner node into a visual DAG with bottleneck signals:

### Detected Bottleneck Patterns
1. **Sequential Scan on High Volume**: Detected when a `Seq Scan` is performed on a relation with estimated rows $> 50,000$ and total cost $> 500$.
2. **Nested Loop Join Multiplier**: Detected when an unindexed inner relation is scanned repeatedly under a `Nested Loop`.
3. **Expensive Disk Sort Spill**: Detected when a `Sort` node exhibits high total cost with buffer temp block activity.
4. **Correlated Subquery Scan**: Detected when a subplan filter repeatedly scans a table per outer tuple.

### Honesty Labeling
All telemetry plan visualizers and API responses feature the explicit disclaimer:
> **"Rule-based plan graph analysis; GNN/RL-ready architecture."**

This transparently communicates that the MVP performs rule-based execution graph analysis while providing standard graph schemas (`sanitized_plan_nodes`, `sanitized_plan_edges`) ready for future Graph Neural Network (GNN) and Reinforcement Learning (RL) model ingestion.

---

## 🛡️ Security Boundaries & Database Permissions

The synthetic workload database enforces least-privilege access:

1. **Dedicated Read-Only Role (`workload_ro`)**:
   - `GRANT CONNECT ON DATABASE workload TO workload_ro;`
   - `GRANT USAGE ON SCHEMA public TO workload_ro;`
   - `GRANT SELECT ON ALL TABLES IN SCHEMA public TO workload_ro;`
   - `GRANT pg_read_all_stats TO workload_ro;`
2. **Explicit DDL Prevention**:
   - `REVOKE CREATE ON SCHEMA public FROM workload_ro;`
   - Role has zero DDL privileges, cannot execute `DROP`, `ALTER`, or `TRUNCATE`.
3. **Network Isolation**:
   - Both PostgreSQL databases run in an internal Docker bridge network (`queryguard-net`).
   - The application backend has no internet egress and sends zero telemetry outside the host machine.

---

## 🚀 Telemetry API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/telemetry/collect` | Triggers read-only telemetry extraction, sanitization, and persistence |
| `GET` | `/api/telemetry/status` | Reports collector run metadata, statements scanned, and privacy status |
| `GET` | `/api/telemetry/events` | Retrieves all sanitized telemetry query events |
| `GET` | `/api/telemetry/events/{id}` | Retrieves detailed event metadata, masked SQL, XAI packet, and plan DAG |

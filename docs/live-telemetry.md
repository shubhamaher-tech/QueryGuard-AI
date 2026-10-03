# Live PostgreSQL Telemetry & Workload Monitoring

## 1. Overview

QueryGuard AI's **Live Workload** subsystem continuously samples query execution statistics from the running `workload-postgres` container via `pg_stat_statements` and `pg_stat_database`. 

Unlike static mock dashboards, the live telemetry reflects actual database operations inside the sandbox, updating automatically as users analyze queries or run benchmark workloads.

---

## 2. Security & Privacy Guarantees

1. **Read-Only Session Enforcement:** Every telemetry harvest runs inside an isolated read-only transaction:
   ```sql
   SET TRANSACTION READ ONLY;
   SET statement_timeout = 5000;
   ```
2. **Local AST Literal Masking:** All query strings retrieved from `pg_stat_statements` are immediately processed by the QueryGuard Privacy Engine:
   - Integers, floats, dates, strings, emails, and UUIDs are masked to `:INT`, `:NUM`, `:DATE`, `:STR`.
3. **HMAC Identifier Tokenization:** Schema names (e.g. `transactions`, `lineitem`, `customers`) are substituted with pseudonymized tokens (`TBL_A12`, `TBL_L08`, `TBL_B03`) before transmission.
4. **Zero Result Row Retention:** The telemetry pipeline never selects table rows; it queries PostgreSQL system catalogs exclusively (`pg_stat_statements`, `pg_stat_database`, `pg_stat_activity`).

---

## 3. Metrics Computed in Real Time

| Metric | Source Catalog | Description |
|---|---|---|
| **Average Latency** | `pg_stat_statements.mean_exec_time` | Mean execution duration across top active statements. |
| **p95 Latency** | `pg_stat_statements` | 95th percentile estimated latency distribution. |
| **Throughput (qps)** | Delta of `calls` / delta time | Computed query execution rate per second. |
| **Slow Query Count** | Statements with mean latency > 20ms | Number of active queries exceeding performance threshold. |
| **Buffer Cache Hit %** | `pg_stat_database.blks_hit` vs `blks_read` | Efficiency ratio of shared buffer pool hits vs disk I/O. |
| **Estimated CPU %** | Heuristic from qps & latency | Workload intensity proxy for developer visibility. |
| **Bottleneck Types** | Plan & query syntactic heuristics | Distribution of `SEQ_SCAN`, `UNINDEXED_JOIN`, `EXPENSIVE_SORT`, and `HIGH_IO_SCAN`. |

---

## 4. API Endpoints

- `GET /api/realtime/status` — Reports database connectivity, active mode (`SANDBOX_WORKLOAD_POSTGRES`), and collection interval.
- `GET /api/realtime/metrics` — Returns current metric snapshot, 30-sample latency trend, bottleneck distribution, and top slow queries.
- `GET /api/realtime/slow-queries` — Returns list of sanitized slow queries with execution counts and timings.
- `GET /api/realtime/stream` — Server-Sent Events (SSE) stream broadcasting JSON updates every 3–8 seconds.
- `GET /api/realtime/connection` — Returns connection configuration mode and safety guarantees.

---

## 5. Frontend Integration

The **Live Workload** view (`frontend/src/components/LiveWorkloadView.tsx`):
- Features an active pulse indicator and connection badges.
- Displays a rolling timeline chart showing latency and query throughput.
- Visualizes bottleneck distribution bars.
- Provides a **"Simulate Traffic"** shortcut that fires approved benchmark queries to stimulate real-time telemetry.
- Includes an **"Analyze in Workspace"** button on every slow query fingerprint, allowing instant one-click inspection in the Query Analysis workspace.

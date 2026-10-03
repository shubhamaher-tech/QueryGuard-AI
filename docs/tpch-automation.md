# TPC-H Benchmark Automation Pipeline

## 1. Overview & Architectural Boundaries

QueryGuard AI includes an automated, privacy-safe benchmark generation and evaluation pipeline supporting the standard **TPC-H Decision Support Benchmark** (Scale Factor 0.1 default, optional Scale Factor 1.0 with hardware safeguards).

### Strict Architectural Boundaries
1. **Isolated Physical Persistence:** All raw `.tbl` files, raw benchmark data, and database tables (`region`, `nation`, `part`, `supplier`, `partsupp`, `customer`, `orders`, `lineitem`) reside exclusively inside the local `workload-postgres` container (`workload_db`).
2. **Zero Row Exposure:** The QueryGuard application database (`queryguard`), FastAPI backend, GNN dataset, frontend UI, and audit logs store **strictly zero customer records, query literals, or result rows**.
3. **Read-Only Telemetry:** Query analysis, workload running, and telemetry harvesting operate strictly under `SET TRANSACTION READ ONLY` with a 10-second statement timeout.

---

## 2. Directory Structure

```
database/workload/tpch/
├── schema/
│   └── tpch_ddl.sql          # Schema DDL (tpch_sf01) & compatibility views
├── queries/
│   ├── q01_pricing_summary.sql    # Heavy aggregate & date filter
│   ├── q03_shipping_priority.sql  # 3-way join & order priority
│   ├── q05_local_supplier_volume.sql # 6-way analytical join
│   ├── q06_forecasting_revenue.sql   # Missing composite index scenario
│   ├── q10_returned_item.sql      # Multi-table join & top-N sort
│   ├── q12_shipping_modes.sql     # 2-table join & CASE aggregates
│   └── q14_promotion_effect.sql   # CASE percentage aggregate
├── raw/                      # Generated raw .tbl files (gitignored)
├── processed/                # Normalized, validated .tbl files (gitignored)
└── logs/                     # Generation and validation logs (gitignored)
```

---

## 3. Scale Factors & Dataset Sizes

| Scale Factor | Lineitem Rows | Total DB Rows | Raw File Size | Memory Requirement | Target Environment |
|---|---|---|---|---|---|
| **SF 0.1 (Default)** | ~60,000 | ~87,000 | ~8 MB | < 512 MB RAM | Local Dev / CI / Docker |
| **SF 1.0 (High Spec)** | ~6,000,000 | ~8,660,000 | ~1.1 GB | ≥ 4 GB RAM | Dedicated Benchmarking |

> [!WARNING]
> Generating SF 1.0 creates 6 million lineitem rows. The UI displays an explicit hardware warning requiring at least 4 GB free RAM and 1.2 GB disk.

---

## 4. Pipeline Stages

### Stage 1: Deterministic Generation (`TPCHManager`)
- Seeded pseudo-random generator produces standard TPC-H distributions for region, nation, part, supplier, partsupp, customer, orders, and lineitem.
- Outputs raw pipe-delimited files into `database/workload/tpch/raw/`.

### Stage 2: Normalization & Preprocessing (`DatasetCleaner`)
- Standardizes line endings (LF vs CRLF).
- Strips trailing delimiter pipes (`|`) for PostgreSQL `COPY` compatibility.
- Validates expected column count per line; tracks rejected lines safely without logging record contents.
- Writes clean files to `database/workload/tpch/processed/`.

### Stage 3: Verification (`DatasetValidator`)
- Verifies that all 8 `.tbl` files exist, are non-empty, and fall within acceptable row-count tolerances for the target scale factor.

### Stage 4: Administrative Database Loading (`DatasetLoader`)
- Connects to `workload_db` using administrative credentials.
- Applies `tpch_sf01` schema DDL.
- Executes high-speed `COPY tpch_sf01.<table> FROM STDIN WITH (FORMAT csv, DELIMITER '|')`.
- Runs `ANALYZE tpch_sf01.*` to populate PostgreSQL optimizer statistics.
- Grants read-only privileges (`GRANT USAGE`, `GRANT SELECT`) to `workload_ro`.

### Stage 5: Workload Simulation (`BenchmarkRunner`)
- Connects via `workload_ro` with `SET TRANSACTION READ ONLY`.
- Executes approved query templates with a 10s statement timeout.
- Stimulates `pg_stat_statements` with real analytical queries.
- Iterates result rows to calculate exact timings and row counts, but **never persists or returns row contents**.

---

## 5. API Endpoints

- `GET /api/benchmarks/catalog` — Lists all 4 benchmark configurations (Synthetic E-Commerce, TPC-H SF 0.1, TPC-H SF 1.0, JOB/IMDb).
- `POST /api/benchmarks/tpch/setup` — Triggers background file generation and cleaning.
- `GET /api/benchmarks/tpch/status` — Polls setup progress percentage and current stage.
- `GET /api/benchmarks/tpch/summary` — Returns table row counts and disk footprint.
- `POST /api/benchmarks/tpch/load` — Loads validated files into `workload_db` via `COPY`.
- `POST /api/benchmarks/tpch/run-workload` — Fires approved query templates to refresh `pg_stat_statements`.
- `POST /api/benchmarks/tpch/reset` — Truncates `tpch_sf01` tables safely.

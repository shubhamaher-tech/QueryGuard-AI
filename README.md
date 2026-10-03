# QueryGuard AI 🛡️

> **Privacy-First PostgreSQL Performance-Tuning Copilot**  
> Analyzes strictly anonymized SQL & query-plan metadata, detects slow-query bottlenecks, recommends safe database optimizations, simulates potential impact with HypoPG in-memory virtual indexes, explains recommendations with evidence, and enforces DBA approval before any production change.

> **Honest Architectural Disclosure:**  
> **Rule-based plan graph analysis with HypoPG planner simulation; GNN/RL-ready architecture.**  
> QueryGuard AI features an **experimental GNN bottleneck classifier** trained exclusively on synthetic sanitized benchmark execution plans. It is **not** trained on production customer data. The deterministic rule engine remains the primary and authoritative recommendation source; human DBA approval is required before any schema change. All what-if performance projections are calculated via PostgreSQL's cost model using HypoPG in-memory hypothetical indexes and empirical statistical estimators.

---

## 🎯 Executive Overview

Modern database performance optimization often involves sensitive production data risks when teams send queries to cloud-based LLMs or external APMs. **QueryGuard AI** solves this with a **Zero-Raw Data Privacy Architecture**:

1. **Interactive Query Analysis Workspace**: Real-time SQL profiling sandbox (`/analyze-query`). DBAs can paste arbitrary SELECT queries, run strict safety gateway validation, execute read-only in-memory `EXPLAIN (FORMAT JSON)`, view SVG plan graphs, inspect 2-layer GraphSAGE GNN signals, and simulate virtual index impact using HypoPG.
2. **Automated Benchmark Datasets & Generators**: Full automated lifecycle for **TPC-H SF 0.1** (~87k rows, 8 tables, 7 approved templates) with background generation, schema application, `COPY` loading, and workload execution. Includes hardware-safe advisory for SF 1.0 (~6M lineitems) and scaffolded JOB/IMDb support.
3. **Live Workload Real-Time Telemetry**: Real-time continuous sampling from `workload-postgres` via `pg_stat_statements` and `pg_stat_database`. Live latency timeline, throughput (qps), cache hit ratio, and slow query fingerprints with one-click "Analyze in Workspace".
4. **GNN v2 Model & Checkpoint Selection**: Expanded 245-sample dataset (`v2_synthetic_tpch_postgres`) across 7 bottleneck classes achieving **94.6% test accuracy** and **0.948 Macro F1**, with dynamic model switching between `gnn_bottleneck_v1` and `gnn_bottleneck_v2`.
5. **Deterministic Literal Masking & Schema Tokenization**: Scalar values (`42`, `'2026-09-01'`) are masked to `:INT`, `:DATE`, and database schema identifiers (`transactions`, `lineitem`) are mapped to synthetic tokens (`TBL_A12`, `TBL_L08`) *prior* to persistence or analysis.
6. **Multi-Stage Privacy Scanner**: In-memory verification barrier rejects unmasked numeric/string literals, plaintext schema names, or SQL comments before persisting anything to the application database or sending API responses.
7. **Explainable AI (XAI) Bottleneck Isolation**: Identifies Sequential Scans on large tables, Nested Loop join row multipliers, and expensive external disk sorts.
8. **Privacy-Preserving Local Small Language Model (SLM) SQL Rewrite Copilot**: For complex query templates (joins > 2, nested/correlated subqueries, plan depth > 5), routes masked templates to a local Ollama model (`qwen2.5-coder:1.5b`). Candidates must pass strict AST gatekeeping (SELECT-only, no comments, token whitelist) and sandbox PostgreSQL `EXPLAIN` comparison ($\ge 10\%$ cost improvement) before DBA review.
9. **Human-in-the-Loop DBA Governance**: Zero automated DDL or SQL execution. Every optimization requires explicit DBA sign-off with immutable audit logging.

---

## 🏗️ Architecture & Component Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, custom design system (`qryx-adaptive-db`), Live Workload Telemetry, Benchmark Datasets Manager, Interactive Query Analysis Workspace, SVG PlanGraphCanvas, Recharts, Lucide Icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy ORM, sqlglot, psycopg2, httpx.
- **Local SLM Service**: Ollama container running `qwen2.5-coder:1.5b` (or `llama3.2:3b`) in an isolated Docker sandbox.
- **Application Database**: PostgreSQL 16 Alpine (`queryguard` database on port 5432).
- **Synthetic Workload Database**: PostgreSQL 16 (`workload-postgres` on port 5433) with `pg_stat_statements`, `hypopg` (`postgresql-16-hypopg`), and TPC-H SF 0.1 benchmark enabled.
- **Orchestration**: Docker Compose (multi-service topology with healthchecks and startup ordering).
- **Automated Verification**: Comprehensive pytest test suite (**59 passed tests**).

```
queryguard-ai/
  frontend/                  # React 19 + Vite dashboard (qryx-adaptive-db design system)
    src/
      components/            # AnalyzeQueryWorkspace, PlanGraphCanvas (SVG), SimulationModal, ApprovalDrawer
      lib/api.ts             # Typed REST API client with fallback resilience & SSE support
      types/                 # Comprehensive TypeScript contract types (AnalysisJob, Benchmarks)
      App.tsx                # Central reactive state, triage, recommendations, telemetry, analysis
  backend/                   # FastAPI service, privacy engine, analyzer & HypoPG simulator
    app/
      analysis/              # Interactive query analysis, safety validator, benchmarks catalog, service
      llm/                   # Local SLM subsystem (Ollama client, router, safety)
      safety/                # Deterministic security & gatekeeping
      hypopg/                # Real HypoPG simulation engine
      telemetry/             # Collector, sqlglot sanitizer, plan parser, service
      routers/               # REST API routers (/api/analyze-query, /api/benchmarks, etc.)
      privacy.py             # Literal masking & schema tokenization
      analyzer.py            # Plan bottleneck analyzer & XAI packets
      models.py              # SQLAlchemy ORM definitions
    tests/                   # Automated pytest suite (50 comprehensive tests)
  database/
    init/                    # Application database schemas & seed data
    workload/                # Synthetic benchmark workload database scripts
      Dockerfile             # postgres:16 + postgresql-16-hypopg Debian package
      01-init-workload.sql   # Enable pg_stat_statements & hypopg
      02-generate-synthetic-data.sql # Synthetic data (250k transactions, 500k order items)
      03-workload_queries.sql# Benchmark slow queries (Seq scan, joins, sorts)
      04-generate-tpch-data.sql # TPC-H SF 0.1 benchmark dataset generator (60k lineitems)
  docs/
    interactive-query-analysis.md # Dedicated Interactive Query Analysis guide & safety rules
    benchmark-datasets.md    # Dedicated Benchmark Datasets specification (E-Commerce, TPC-H, JOB)
    runbook.md               # End-to-end operational guide & demo verification
    frontend-backend-contract.md # Complete REST API contract specification
    frontend-analysis.md     # qryx-adaptive-db frontend UI & state analysis
    architecture.md          # System architecture and Mermaid diagrams
    gnn-training.md          # GNN dataset generation, PyTorch GraphSAGE & evaluation
    local-slm-rewrites.md    # Dedicated local SLM rewrite pipeline specification
    hypopg-simulation.md     # Detailed HypoPG session workflow & guardrails
    telemetry-pipeline.md    # Dedicated telemetry pipeline specification
  scripts/                   # Model bootstrap utilities & GNN scripts
    pull_model.sh            # Linux/macOS Ollama model pull script
    pull_model.ps1           # Windows PowerShell Ollama model pull script
  docker-compose.yml         # Container orchestration with health checks
  .env.example               # Example environment variables
  README.md                  # Complete project documentation
```

---

## 📋 Prerequisites

To run QueryGuard AI using Docker:
- **Docker Desktop** (version 24.0+) & **Docker Compose** (v2.20+)

To run locally without Docker:
- **Node.js** (v18.17+ or v20+) and **npm**
- **Python** (v3.11+)

---

## 🚀 Quick Start (Docker Compose)

The easiest way to run the complete stack is with Docker Compose:

```bash
# 1. Clone or navigate to the repository
cd queryguard-ai

# 2. Copy the environment configuration
cp .env.example .env

# 3. Build and launch all services
docker compose up --build
```

### Verified Service URLs:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Application Database**: `localhost:5432` (`queryguard` / `queryguard` / `queryguard_secret`)
- **Synthetic Workload Database**: `localhost:5433` (`workload` / `workload_user` / `workload_secret`)
- **Local Ollama SLM Service**: [http://localhost:11434](http://localhost:11434) (`qwen2.5-coder:1.5b`)

---

## 🔮 HypoPG Simulation Engine & Endpoints

QueryGuard introduces real planner what-if simulation via the `hypopg` extension:

### Available Simulation Endpoints:
- `POST /api/recommendations/{id}/simulate`: Executes safe in-memory HypoPG evaluation against `workload-postgres`.
- `GET /api/recommendations/{id}/simulation`: Retrieves the current simulation result, before/after metrics, and acceptance decision.
- `POST /api/recommendations/{id}/reset-simulation`: Resets the recommendation status back to `PENDING` and removes the simulation result.

### Sample Sanitized Simulation Response:
```json
{
  "recommendation_id": "REC_20261003_A01",
  "simulation_type": "HYPOTHETICAL_INDEX",
  "status": "COMPLETED",
  "label": "Simulated estimate",
  "baseline": {
    "planner_total_cost": 15420.5,
    "plan_summary": {
      "main_operator": "SEQ_SCAN",
      "operator_counts": { "Seq Scan": 1 },
      "plan_depth": 2
    }
  },
  "proposal": {
    "hypothetical_index_token": "HIDX_TBL_A12_COL_R01_COL_D02",
    "index_pattern": ["COL_R01", "COL_D02"],
    "planner_total_cost": 182.3,
    "plan_summary": {
      "main_operator": "INDEX_SCAN",
      "operator_counts": { "Index Scan": 1 },
      "plan_depth": 2
    }
  },
  "impact": {
    "estimated_planner_cost_reduction_percent": 98.8,
    "estimated_latency_improvement_percent_range": [70, 95],
    "estimated_write_latency_increase_ms_range": [0.4, 1.2],
    "estimated_storage_overhead_gb_range": [0.02, 0.06]
  },
  "acceptance_decision": {
    "accepted": true,
    "reason_codes": [
      "SIGNIFICANT_PLANNER_COST_REDUCTION",
      "INDEX_SELECTED_BY_PLANNER"
    ],
    "confidence": "HIGH",
    "risk_level": "LOW"
  },
  "privacy_status": "No raw row data or physical indexes created. All identifiers tokenized."
}
```

---

## 🤖 Local Small Language Model (SLM) SQL Rewrite Pipeline

QueryGuard integrates an isolated local Small Language Model (SLM) copilot designed specifically for complex query refactoring (joins > 2, correlated subqueries, plan depth > 5). The model runs inside a local Ollama container (`qwen2.5-coder:1.5b` by default) with **zero cloud data egress**.

### Key Pipeline Components:
1. **Heuristic Complexity Router**: Simple queries bypass the model entirely, receiving fast, deterministic rule-based indexing. Only complex queries trigger the SLM.
2. **Zero-Raw Sanitized Context**: The prompt contains only tokenized identifiers (`TBL_A12`, `COL_R01`), selectivity buckets, and operator hints.
3. **Deterministic AST Safety Gateway**: Every candidate must be a single `SELECT` statement with no comments, no multi-statement injection, no dangerous functions, and only authorized tokens.
4. **PostgreSQL Sandbox EXPLAIN Guardrail**: The candidate is rehydrated in-memory and compared against the baseline using `EXPLAIN (FORMAT JSON)` on `workload-postgres`. Only rewrites demonstrating $\ge 10\%$ cost improvement are accepted.
5. **Mandatory DBA Authorization**: Accepted rewrites are marked `READY_FOR_DBA_REVIEW`. Zero automated production execution.

### Available SLM Rewrite Endpoints:
- `GET /api/llm/status`: Checks Ollama connectivity, model availability, and privacy mode.
- `POST /api/queries/{id}/rewrite/analyze`: Runs end-to-end routing, SLM generation, AST safety checks, and EXPLAIN simulation.
- `GET /api/queries/{id}/rewrite`: Retrieves persisted rewrite analysis and comparison metrics.
- `POST /api/queries/{id}/rewrite/reset-cache`: Clears cached rewrite results for a query.

### Model Setup Commands:
```bash
# Linux / macOS
./scripts/pull_model.sh qwen2.5-coder:1.5b

# Windows PowerShell
.\scripts\pull_model.ps1 -Model "qwen2.5-coder:1.5b"
```

---

## 🔒 Privacy Controls & Guarantees

QueryGuard AI implements a strict **Zero-Raw Privacy Engine**:

### SQL Sanitization Example
**Raw Workload Input:**
```sql
SELECT t.id, t.transaction_date, c.name, oi.quantity
FROM transactions t
JOIN customers c ON t.customer_id = c.id
JOIN order_items oi ON oi.transaction_id = t.id
WHERE t.region_id = 5
  AND t.transaction_date >= '2026-01-01'
ORDER BY t.transaction_date DESC
LIMIT 50;
```

**QueryGuard Tokenized Template:**
```sql
SELECT
  ALIAS_9E85F0BC.COL_07D0E600,
  ALIAS_9E85F0BC.COL_48CF2A96,
  ALIAS_F1991F19.COL_619EB5EE,
  ALIAS_300B5B33.COL_4F69B9E7
FROM TBL_B1DEB666 AS ALIAS_9E85F0BC
JOIN TBL_017C8A97 AS ALIAS_F1991F19 ON ALIAS_9E85F0BC.COL_4E87EF1E = ALIAS_F1991F19.COL_07D0E600
JOIN TBL_2574A929 AS ALIAS_300B5B33 ON ALIAS_300B5B33.COL_404C9199 = ALIAS_9E85F0BC.COL_07D0E600
WHERE ALIAS_9E85F0BC.COL_ED1DFE5F = :INT
  AND ALIAS_9E85F0BC.COL_48CF2A96 >= :DATE
ORDER BY ALIAS_9E85F0BC.COL_48CF2A96 DESC
LIMIT :INT;
```

---

## 🧠 Experimental Plan Graph Neural Network (GNN)

QueryGuard AI features an **experimental GNN proof-of-concept** for execution-plan bottleneck classification:

- **Graph Formulation**: Transforms hierarchical PostgreSQL `EXPLAIN (FORMAT JSON)` plan trees into directed acyclic graphs with bidirectional message-passing edges ($2 \times E$).
- **24-Dimensional Privacy-Safe Node Vectors**: Includes one-hot operator indicators, normalized log costs, log rows, startup cost fraction, plan depth, child count, structural condition flags, and loop buckets. Contains strictly **zero** relation names, column names, or raw SQL.
- **Pure PyTorch GraphSAGE Architecture**: Avoids compiled C++ binary dependencies (`torch-geometric` ABI) by using vectorized PyTorch operations (`index_add_`, mean neighborhood pooling). Runs CPU inference in **<5ms**.
- **7 Canonical Bottleneck Classes**: `SEQ_SCAN_BOTTLENECK`, `NESTED_LOOP_BOTTLENECK`, `EXPENSIVE_SORT`, `HASH_JOIN_HEAVY`, `AGGREGATION_HEAVY`, `GOOD_OR_OPTIMIZED_PLAN`, `CARDINALITY_ESTIMATION_RISK`.
- **Offline Benchmark Results**: 100.0% holdout accuracy and 1.000 Macro F1 on 140 synthetic plan graphs generated from `workload-postgres`.
- **Honest Limitations Disclosure**: Real database production workloads exhibit higher distribution shifts and variance. Therefore, the deterministic rule engine remains the primary authoritative recommendation source, with the GNN providing an advisory evidence signal and active divergence detection in the UI.

For complete model details and mathematical formulation, see [docs/gnn-training.md](docs/gnn-training.md).

---

## 🛠️ Docker Build Troubleshooting & ML Profile

### Backend Dependency Build Issue & Solution
If you encounter a build failure at `RUN pip install --no-cache-dir -r requirements.txt` (exit code 2), this is caused by heavy ML packages attempting C++ compilation on minimal images. 

**QueryGuard AI solves this by keeping the standard backend container completely lightweight**:
- `backend/requirements.txt`: Contains only pure binary wheels (`psycopg[binary]`, `psycopg2-binary`, `fastapi`, `uvicorn[standard]`, `sqlglot`, `httpx`). Zero compiler headers or GPU packages needed.
- `backend/requirements-ml.txt`: Contains optional ML packages (`torch`, `scikit-learn`, `numpy`).
- `docker-compose.yml`: Defines `backend-ml` under `profiles: ["ml"]`.

### Commands to Rebuild & Inspect Backend
```bash
# Rebuild default backend cleanly without cache:
docker compose build backend --no-cache --progress=plain

# Start containers in background:
docker compose up -d

# Inspect backend logs (last 100 lines):
docker compose logs backend --tail 100
```

### Running with the Optional ML Profile
To launch the isolated ML container with PyTorch pre-installed:
```bash
docker compose --profile ml up -d --build
```

### CLI Dataset Generation, Training & Evaluation Commands
```bash
# Generate synthetic sanitized plan dataset (140 graphs):
python scripts/generate_plan_dataset.py --samples-per-class 20

# Train GraphSAGE model on synthetic benchmark:
python scripts/train_gnn_model.py --epochs 60 --lr 0.005

# Evaluate checkpoint and view confusion matrix:
python scripts/evaluate_gnn_model.py
```

---

## 🧪 Automated Test Suite

QueryGuard AI includes a **39-test automated suite** covering the privacy engine, AST sanitizer, plan parser, HypoPG simulator, local SLM router, SQL safety gatekeeper, in-memory rehydrator, candidate validator, collector, GNN feature encoder, and governance workflows:

```bash
cd backend
pytest -v
```

Verified test coverage (39/39 tests passing):
- `tests/test_gnn.py`: Canonical label mapping, 24D feature vector encoding, bidirectional graph construction, privacy scanner rejection of raw customer strings, model registry status, safe inference, and rule disagreement detection (7 tests).
- `tests/test_llm_rewrite.py`: Complexity router heuristic criteria, prompt privacy sanitizer, AST safety gatekeeper, in-memory token rehydration, semantic validation, status endpoints, cache reset, simulation passed flow, safety rejection flow (12 tests).
- `tests/test_hypopg_simulation.py`: Candidate generator rules, impact estimator model, full `/simulate`, `/simulation`, and `/reset-simulation` API flows, privacy barrier verification.
- `tests/test_telemetry_sanitizer.py`: AST parsing, HMAC stability, literal masking, privacy scanner enforcement.
- `tests/test_telemetry_collector_parser.py`: Collector allow-list metrics, graph node/edge transformation, bottleneck detection.
- `tests/test_telemetry_api.py`: Full API lifecycle (`/collect`, `/status`, `/events`, `/events/{id}`).
- `tests/test_privacy.py`: Literal masking, tokenization, privacy certification.
- `tests/test_analyzer.py`: Execution plan traversal, bottleneck detection, XAI evidence schema.
- `tests/test_simulator.py`: Cost-matrix simulation calculations, no-DDL guarantee.
- `tests/test_approval.py`: DBA approval/rejection persistence and audit log creation.

---

## 📄 License
MIT License. Built with privacy-first principles for mission-critical database engineering.

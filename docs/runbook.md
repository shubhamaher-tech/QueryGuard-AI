# QueryGuard AI - Operator Runbook & Verification Guide

This runbook provides step-by-step instructions for operating, verifying, and testing the full QueryGuard AI stack with the integrated enterprise React 19 frontend and FastAPI backend.

---

## 1. System Architecture Overview

QueryGuard AI operates with a strict separation of concerns and zero-raw privacy enforcement:

```
[ Workload Postgres (Port 5433) ] 
       │ (Read-only synthetic slow queries & pg_stat_statements)
       ▼
[ QueryGuard Backend (Port 8000) ]
   ├── Local Sanitizer & HMAC Tokenizer (zero raw SQL leaves)
   ├── Rule-Based Bottleneck Detector & Plan Parser
   ├── HypoPG Simulation Engine (virtual in-memory sandbox)
   ├── Local SLM Rewrite Router (Ollama qwen2.5-coder:1.5b)
   └── Human-in-the-Loop DBA Approval Gateway
       ▲
       │ REST APIs with strict privacy barrier
       ▼
[ React 19 Frontend (Port 3000 / 5173) ]
   ├── Navigation with Persistent Privacy & Environment Badges
   ├── Interactive Dashboard Triage & Latency Metrics
   ├── Visual Execution Plan SVG Canvas (PlanGraphCanvas)
   ├── Multi-Factor Ranking & XAI Evidence Review
   ├── Real HypoPG Virtual Index Simulation Modal
   ├── Human DBA Approval / Rejection Drawer
   └── Immutable Audit Trail Viewer & JSON Exporter
```

---

## 2. Quickstart Instructions

### Option A: Running with Docker Compose (Recommended for Full Stack)

1. **Start all services**:
   ```bash
   docker compose up -d --build
   ```

2. **Verify running containers**:
   ```bash
   docker compose ps
   ```
   You should see:
   - `queryguard-postgres` (port 5432 - application database)
   - `queryguard-workload-postgres` (port 5433 - synthetic workload database)
   - `queryguard-ollama` (port 11434 - local SLM service)
   - `queryguard-backend` (port 8000 - FastAPI REST API)
   - `queryguard-frontend` (port 3000 - React 19 Vite/Serve frontend)

3. **Access the application**:
   - Frontend Dashboard: [http://localhost:3000](http://localhost:3000)
   - Backend Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Backend Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Running Locally for Fast Development

#### 1. Start Databases & Backend
```bash
# In backend directory:
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start Frontend
```bash
# In frontend directory:
cd frontend
npm install
npm run dev
```
The Vite development server will start at `http://localhost:5173` (or `http://localhost:3000`).

---

## 3. End-to-End Verification Checklist

| Step | Action | Expected Result |
| :--- | :--- | :--- |
| **1. Header Badges** | Inspect top bar in browser | Persistent badges are visible:<br/>- `Synthetic local workload — no production changes`<br/>- `Privacy protected — masked metadata only`<br/>- Source status: `Connected` |
| **2. Role Switcher** | Select dropdown in top right | Switch between `Priya Sharma (DBA)`, `Arjun Patel (ENGINEER)`, and `Alex Vance (VIEWER)`. DBA permissions allow approval actions. |
| **3. Dashboard Triage** | View Dashboard tab | Hero triage banner highlights top slow query (`qry-7c91`). 4 metric cards display queries, approvals, simulations, and cost reduction. |
| **4. Slow Queries Catalog** | Click "Slow Queries" tab | View all monitored queries (`qry-7c91`, `qry-4b18`, `qry-9e02`). Filter by bottleneck or search token. |
| **5. Plan Graph Canvas** | Click `qry-7c91` in table | Inspect interactive SVG execution plan tree with color-coded nodes (`AGGREGATE`, `NESTED_LOOP`, `SEQ_SCAN`). Critical sequential scan bottleneck highlighted. |
| **6. HypoPG Simulation** | Click "Simulate Candidate" button | 5-step interactive progress modal runs virtual index what-if simulation, displaying baseline cost (182,341) vs candidate cost (30,510) with an 83.3% reduction. |
| **7. Human Approval Gate** | Click "Review & Approve" on recommendation | Opens `ApprovalDrawer`. Confirm safety check and click "Authorize Optimization". Recommendation status updates to `APPROVED`. |
| **8. Audit Trail Verification** | Click "Audit Logs" tab | New `APPROVED` event is recorded with actor ID, timestamp, and guarantee note: `No production deployment occurred`. Click "Export Sanitized Audit JSON" to download audit trail. |
| **9. Telemetry Ingestion** | Go to Settings tab, click "Ingest Telemetry Now" | Backend queries `workload-postgres`, tokenizes tables/columns, masks literals, and creates sanitized events. |
| **10. Privacy Self-Test** | Go to "Privacy & Controls" tab | Review guarantees. Click "Run Privacy Self-Test" to verify live literal masking and HMAC token stability fixtures. |

---

## 4. Running the Automated Test Suites

### Backend Pytest Suite
Run the comprehensive 39-test backend test suite covering privacy sanitizer, HypoPG simulation, approval workflow, audit logs, SLM rewrites, and telemetry ingestion:
```bash
cd backend
pytest -v
```
**Expected Result**: `39 passed` with 0 failures.

### Frontend TypeScript & Bundle Verification
Verify TypeScript typecheck and production build:
```bash
cd frontend
npm run build
```
**Expected Result**: `✓ built in ~1.1s` with 0 errors.

---

## 5. Security & Privacy Guarantees

1. **Zero Raw Rows**: Neither customer row data nor raw query literals are ever stored, logged, or exposed in APIs or the frontend.
2. **Keyed HMAC Tokenization**: Real schema identifiers (tables, columns) are deterministically hashed to tokens like `TBL_SALES` and `COL_TX_DATE`.
3. **No Automatic DDL Execution**: Approved recommendations produce version-controlled migration scripts for human DBA review. No production schema changes are automated.
4. **Virtual Sandbox Only**: HypoPG creates indexes strictly in PostgreSQL process RAM for the duration of the EXPLAIN session and immediately discards them.

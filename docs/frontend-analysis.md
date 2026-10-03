# QueryGuard AI - Frontend Analysis & Architecture Audit

> **Source Repository**: `https://github.com/Tejas-952007/qryx-adaptive-db.git`  
> **Source Directory**: `frontend/` (Vite + React 19 + TypeScript + Lucide Icons)  
> **Design Philosophy**: High-density enterprise DBA control center with dual themes (Dark/Light), interactive SVG plan graph canvas, zero-raw privacy enforcement, slide-over approval drawers, and safe in-memory simulation modals.

---

## 1. Technical Framework & Environment Pattern

- **Framework**: React 19 (`react: ^19.2.8`, `react-dom: ^19.2.8`)
- **Build Tool / Bundler**: Vite 8.3 (`vite: ^8.3.0`, `@vitejs/plugin-react: ^6.1.1`)
- **Language**: TypeScript 6.0 (`typescript: ~6.0.2`, `tsconfig.app.json`, `tsconfig.node.json`)
- **Package Manager**: npm (`package-lock.json` present)
- **Styling**: Pure CSS Variables system with design tokens (`index.css`, `App.css`), theme toggle via `data-theme="dark"` or `"light"` attribute on `<html>`. Zero Tailwind dependencies required by this UI design.
- **Icons**: Lucide React (`lucide-react: ^1.51.0`)
- **Linter**: Oxlint (`oxlint: ^1.81.0`)
- **State Management**: React state hooks (`useState`, `useEffect`) managed top-level in `App.tsx` and distributed to view components via props.
- **Environment Variable Pattern**: Vite convention: `VITE_API_BASE_URL` with fallback to `http://localhost:8000`. (Also supports `NEXT_PUBLIC_API_BASE_URL` for interoperability).

---

## 2. Discovered Navigation Structure & Route Tabs

The frontend uses single-page tab navigation managed in `Navigation.tsx` and `App.tsx` with deep-linking to sub-views via item selection:

| Tab Identifier | Component View | Sub-View / Drill-Down | Description |
| :--- | :--- | :--- | :--- |
| `dashboard` | `DashboardHome.tsx` | N/A | Executive triage alert, 4 metric cards, top slow queries table, pending DBA queue, privacy health. |
| `queries` | `SlowQueriesView.tsx` | `QueryDetailView.tsx` | Filterable catalog of slow query events. Clicking any query opens full detail with `PlanGraphCanvas` and XAI evidence. |
| `recommendations` | `RecommendationsView.tsx` | `RecommendationDetailView.tsx` | Optimization queue. Clicking any recommendation opens 3-step decision flow, baseline vs candidate plan tabs, and HypoPG impact. |
| `audit` | `AuditLogsView.tsx` | Inspect JSON Modal | Immutable governance audit trail with search, event filters, and sanitized JSON export. |
| `privacy` | `PrivacyView.tsx` | Interactive Self-Test | Tokenization mapping reference (`TBL_*`, `COL_*`), literal masking rules (`:INT`, `:DATE`), and interactive privacy self-test. |
| `settings` | `SettingsView.tsx` | N/A | Telemetry data source configuration, latency thresholds, statement timeouts, SLM rewrite toggle, and GNN classification toggle. |

---

## 3. Discovered Modals, Drawers & Interactive Canvases

1. **`SimulationModal.tsx`**:
   - In-memory HypoPG virtual index simulation modal.
   - 5-stage progress indicator: connect $\to$ baseline EXPLAIN $\to$ create virtual index $\to$ re-evaluate planner access paths $\to$ compute write/storage trade-offs.
   - Displays baseline vs candidate cost reduction, execution time estimate, write overhead, and storage penalty.
2. **`ApprovalDrawer.tsx`**:
   - Slide-over governance drawer for human DBA authorization.
   - Supports `APPROVED` (generates human review script; enforces no-auto-DDL policy) or `REJECTED` (with categorical reasons).
   - Enforces mandatory safety acknowledgement checkbox before sign-off.
3. **`PlanGraphCanvas.tsx`**:
   - Custom SVG interactive plan visualizer with tree hierarchy layout.
   - Visual nodes for `SEQ_SCAN`, `INDEX_SCAN`, `INDEX_ONLY_SCAN`, `NESTED_LOOP`, `HASH_JOIN`, `SORT`, `AGGREGATE`.
   - Displays cost bars, row buckets, critical path highlights, relation tokens, and zoom controls.
4. **`VoiceSummaryDialog.tsx`**:
   - Text-to-Speech audio briefing dialog using browser Web Speech API for sanitized executive summaries.

---

## 4. Component-by-Component Data Requirements & Actions

### 1. `Navigation.tsx` (Sidebar + Top Bar)
- **Data Required**:
  - `currentUser`: Current logged-in user (`User` object: id, name, role `DBA`/`ENGINEER`/`VIEWER`, avatar).
  - `users`: List of available users for instant role switching (`GET /api/users`).
  - `dataSource`: Telemetry source metadata (`DataSource`: id, name, mode `DEMO`/`CONNECTED_POSTGRES`, connectionStatus `CONNECTED`/`ERROR`, privacyConfigVersion, endpoint, lastSyncAt) (`GET /api/telemetry/status`).
  - Notification badges count for `queries` and `recommendations`.
- **Actions**:
  - Switch active tab.
  - Switch active user/role.
  - Toggle light/dark theme (`data-theme` attribute).
  - Reset demo data (`POST /api/demo/reset` or client state reset).
  - Open privacy details modal.

### 2. `DashboardHome.tsx` (System Health & Action Center)
- **Data Required**:
  - Top slow query for triage hero card (`GET /api/dashboard/summary`).
  - 4 Summary metric counters:
    - High-Impact Queries count
    - Pending DBA Approvals count
    - Validated Simulations count
    - Simulated Potential Gain (% reduction)
  - Top Slow Query Workload table: `id`, `title`, `queryFingerprint`, `impactScore`, `bottleneckType`, `averageDurationMs`, `analysisStatus`.
  - Pending DBA Approvals Queue: list of recommendations in `VALIDATED` status.
- **Actions**:
  - Click "Review Top Issue" $\to$ open `QueryDetailView`.
  - Click "Inspect" on any table row $\to$ open `QueryDetailView`.
  - Click "Review & Approve" on any pending recommendation $\to$ open `RecommendationDetailView`.
  - Click "Run Simulation" $\to$ open `SimulationModal`.

### 3. `SlowQueriesView.tsx` (Query Catalog)
- **Data Required**:
  - Full list of query events (`GET /api/queries`):
    - `id`, `queryFingerprint`, `title`, `maskedQueryTemplate`, `latencyMsBucket`, `averageDurationMs`, `frequencyBucket`, `callsPerMin`, `impactScore`, `bottleneckType`, `analysisStatus`, `privacyStatus`.
- **Actions**:
  - Client-side or backend search across query title, fingerprint, and template tokens.
  - Filter by `BottleneckType` (`LARGE_SEQ_SCAN`, `REPEATED_INNER_LOOP`, `EXPENSIVE_SORT`, etc.).
  - Filter by `AnalysisStatus` (`NEW`, `ANALYZED`, `SIMULATED`, `APPROVED`, `REJECTED`).
  - Click any row $\to$ open `QueryDetailView`.

### 4. `QueryDetailView.tsx` (Query Deep-Dive & Canvas)
- **Data Required**:
  - Detailed query event object (`GET /api/queries/{query_id}`):
    - Metrics: `averageDurationMs`, `callsPerMin`, `impactScore`, `bottleneckType`, `observedAt`.
    - Sanitized query template: `maskedQueryTemplate` (zero raw literals/names).
    - Plan graph hierarchy: `planGraph` (`PlanGraphData` with `nodes: PlanNodeData[]`).
    - Associated recommendations (`GET /api/queries/{query_id}/recommendations`).
    - XAI evidence packet: `reasonCodes`, `observedEvidence` (scanType, loopCountBucket, relationSizeBucket, cardinalityMismatchRatio, sortSpillDetected), `limitations`, `confidence`.
- **Actions**:
  - Copy masked SQL to clipboard.
  - Run HypoPG simulation (`POST /api/recommendations/{rec_id}/simulate`).
  - Navigate to recommendation detail.
  - Return to queries catalog.

### 5. `RecommendationsView.tsx` (Optimization Catalog)
- **Data Required**:
  - List of all recommendations (`GET /api/recommendations`):
    - `id`, `queryEventId`, `actionType` (`INDEX`, `SQL_REWRITE`, `PARTITION_ADVISORY`), `title`, `maskedChangeTemplate`, `status`, `confidence`, `riskLevel`, `rankingScore`, `simulation`.
- **Actions**:
  - Search by title or change template.
  - Filter by action type (`INDEX`, `SQL_REWRITE`, `PARTITION_ADVISORY`, `ABSTAIN`).
  - Filter by status (`VALIDATED`, `APPROVED`, `REJECTED`).
  - Open `RecommendationDetailView`.
  - Open `SimulationModal`.

### 6. `RecommendationDetailView.tsx` (3-Step Advisory Workflow)
- **Data Required**:
  - Recommendation object (`GET /api/recommendations/{id}`):
    - Evidence packet with reason codes, observed signals, alternatives considered, limitations.
    - Ranking score breakdown: formula $0.45 \times \text{read} - 0.20 \times \text{write} - 0.15 \times \text{storage} - 0.20 \times \text{risk}$.
    - Simulation result (`SimulationResult`): baseline vs candidate planner cost, estimated improvement % range, write overhead range, storage overhead range.
    - Change template: masked SQL/DDL statement.
  - Associated parent query event (`GET /api/queries/{query_id}`).
- **Actions**:
  - Copy change script to clipboard.
  - Toggle between Baseline and Candidate plan comparisons.
  - Trigger HypoPG simulation (`POST /api/recommendations/{id}/simulate`).
  - Open `ApprovalDrawer` with `decision='APPROVED'` or `decision='REJECTED'`.

### 7. `SimulationModal.tsx` (HypoPG In-Memory Simulation)
- **Data Required**:
  - Target recommendation ID and metadata.
- **Actions**:
  - Call backend simulation API: `POST /api/recommendations/{id}/simulate`.
  - Receives `SimulationResult` object with baseline cost, candidate cost, percentage improvement, write overhead ms, storage overhead GB, limitations, and engine (`HYPOPG`).
  - Notifies parent view and persists audit record.

### 8. `ApprovalDrawer.tsx` (Human-in-the-Loop Sign-Off)
- **Data Required**:
  - Recommendation metadata and target decision type.
  - Current DBA user session.
- **Actions**:
  - Call backend approval API: `POST /api/recommendations/{id}/approve` or `POST /api/recommendations/{id}/reject`.
  - Request body includes `actor_id`, `actor_name`, `actor_role`, and `reason`.
  - Updates recommendation status and appends immutable entry to `audit_logs`.

### 9. `AuditLogsView.tsx` (Immutable Governance Trail)
- **Data Required**:
  - List of audit logs (`GET /api/audit-logs`):
    - `id`, `timestamp`, `actorId`, `actorName`, `actorRole`, `eventType`, `entityType`, `entityId`, `description`, `metadataJson`, `privacyStatus`.
- **Actions**:
  - Search by description, actor, or entity ID.
  - Filter by event type (`INGESTED`, `MASKED`, `ANALYZED`, `SIMULATED`, `APPROVED`, `REJECTED`, `PRIVACY_BLOCKED`).
  - View full metadata JSON modal.
  - Export sanitized audit log as JSON file.

### 10. `PrivacyView.tsx` (Privacy Architecture & Self-Test)
- **Data Required**:
  - Transformation pipeline stages and verification status (`GET /api/privacy/status` or mock verification).
  - Self-test fixtures verifying literal masking, schema tokenization, and zero-raw compliance.
- **Actions**:
  - Trigger live privacy self-test (`POST /api/privacy/self-test`).

### 11. `SettingsView.tsx` (Telemetry & Sandbox Configuration)
- **Data Required**:
  - Current telemetry data source configuration (`GET /api/telemetry/status`).
  - Threshold parameters: slow query latency threshold, statement timeout.
  - SLM service status (`GET /api/llm/status`).
- **Actions**:
  - Update telemetry settings / trigger collection (`POST /api/telemetry/collect`).
  - Reset demo data (`POST /api/demo/reset`).
  - Open voice summary audio modal.

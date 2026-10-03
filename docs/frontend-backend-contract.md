# QueryGuard AI - Frontend-Backend Integration Contract

This contract defines the strict API specification bridging the React 19 / Vite frontend (`qryx-adaptive-db`) with the FastAPI backend and PostgreSQL database.

---

## 1. Route & Component API Mapping Table

| Frontend page/component | Backend endpoint | Method | Data required | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Navigation (`Navigation.tsx`)** | `GET /api/users`<br/>`GET /api/telemetry/status` | `GET` | User list, current user role, telemetry connection state, privacy config version | Render top bar status, role switcher, privacy badge |
| **Dashboard (`DashboardHome.tsx`)** | `GET /api/dashboard/summary`<br/>`GET /api/queries`<br/>`GET /api/recommendations` | `GET` | Triage alert query, 4 metric cards, top slow query list, pending recommendations queue | View system triage, select top slow query, review recommendations |
| **Slow Queries View (`SlowQueriesView.tsx`)** | `GET /api/queries` | `GET` | List of sanitized query events with impact score, latency, bottleneck type, calls/min | Filter and search query workload, inspect query detail |
| **Query Detail View (`QueryDetailView.tsx`)** | `GET /api/queries/{query_id}`<br/>`GET /api/queries/{query_id}/plan`<br/>`GET /api/queries/{query_id}/recommendations` | `GET` | Full query metrics, masked SQL template, plan graph nodes/edges, XAI evidence packet, associated recommendations | Inspect execution plan tree, copy masked SQL, trigger simulation |
| **Recommendations View (`RecommendationsView.tsx`)** | `GET /api/recommendations` | `GET` | All recommendations with action type, masked change template, ranking score, simulation state | Filter by status/action, select recommendation for review |
| **Recommendation Detail (`RecommendationDetailView.tsx`)** | `GET /api/recommendations/{id}`<br/>`GET /api/recommendations/{id}/simulation`<br/>`GET /api/queries/{query_id}` | `GET` | Change template, ranking formula breakdown, XAI evidence, baseline vs candidate plan comparison, simulation impact | Compare plan access paths, open approval drawer, run HypoPG simulation |
| **Simulation Modal (`SimulationModal.tsx`)** | `POST /api/recommendations/{id}/simulate` | `POST` | None (server executes HypoPG simulation in session RAM) | Runs in-memory virtual index simulation, returns baseline vs candidate cost reduction |
| **Approval Drawer (`ApprovalDrawer.tsx`)** | `POST /api/recommendations/{id}/approve`<br/>`POST /api/recommendations/{id}/reject` | `POST` | Body: `actor_id`, `actor_name`, `actor_role`, `reason` | Persists DBA decision, changes recommendation state, appends audit log |
| **Audit Logs View (`AuditLogsView.tsx`)** | `GET /api/audit-logs` | `GET` | Immutable audit trail items with actor, event type, entity ID, metadata JSON, privacy status | Search/filter audit history, inspect metadata, export sanitized JSON |
| **Privacy View (`PrivacyView.tsx`)** | `GET /api/privacy/status`<br/>`POST /api/privacy/self-test` | `GET`<br/>`POST` | Privacy gateway status, self-test verification fixtures | Verify zero-raw compliance, run live masking test |
| **Settings View (`SettingsView.tsx`)** | `GET /api/telemetry/status`<br/>`POST /api/telemetry/collect`<br/>`POST /api/demo/reset`<br/>`GET /api/llm/status` | `GET`<br/>`POST` | Telemetry configuration, statements scanned, Ollama status | Collect live telemetry, update latency thresholds, reset demo state |

---

## 2. Detailed Endpoint Specifications

### 2.1 `GET /api/dashboard/summary`
- **Purpose**: Feeds the top triage hero alert and 4 metric cards on `DashboardHome.tsx`.
- **Response Schema**:
```json
{
  "high_impact_queries_count": 3,
  "pending_approvals_count": 2,
  "validated_simulations_count": 2,
  "simulated_max_gain_pct": 85.0,
  "triage_top_query": {
    "id": "qry-7c91",
    "queryFingerprint": "FP_7C91E88B429A",
    "title": "Weekly Regional Sales Aggregation Report",
    "impactScore": 92.4,
    "bottleneckType": "LARGE_SEQ_SCAN",
    "averageDurationMs": 2450.4,
    "rowsScannedEstimate": 12400000
  },
  "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
}
```
- **Loading State**: Metric card skeletons; disabled "Review Top Issue" button.
- **Error State**: Displays non-blocking warning banner: "Telemetry service unreachable. Showing cached demo state."
- **Empty State**: Metric values display 0; triage alert shows "All monitored queries performing within latency thresholds."
- **Privacy Constraints**: No plaintext SQL or schema names. Only synthetic tokens (`TBL_SALES`, `COL_REGION_ID`).

---

### 2.2 `GET /api/queries` & `GET /api/queries/{query_id}`
- **Purpose**: Populates `SlowQueriesView.tsx` catalog and `QueryDetailView.tsx`.
- **Query Parameters**:
  - `bottleneck_type` (optional): Filter by `LARGE_SEQ_SCAN`, `REPEATED_INNER_LOOP`, `EXPENSIVE_SORT`, etc.
  - `status` (optional): Filter by `NEW`, `ANALYZED`, `SIMULATED`, `APPROVED`, `REJECTED`.
  - `search` (optional): Substring search across title, fingerprint, or masked query template.
- **Response Schema (`QueryEvent`)**:
```json
{
  "id": "qry-7c91",
  "queryFingerprint": "FP_7C91E88B429A",
  "title": "Weekly Regional Sales Aggregation Report",
  "maskedQueryTemplate": "SELECT COL_REGION_ID, DATE_TRUNC(:TEXT, COL_TX_DATE) AS tx_week, COUNT(*), SUM(COL_AMOUNT) FROM TBL_SALES JOIN TBL_STORES ON TBL_SALES.COL_STORE_ID = TBL_STORES.COL_ID WHERE COL_STATUS = :TEXT AND COL_TX_DATE >= :TIMESTAMP AND COL_TX_DATE < :TIMESTAMP GROUP BY 1, 2 ORDER BY 4 DESC;",
  "latencyMsBucket": "1S_TO_5S",
  "averageDurationMs": 2450.4,
  "frequencyBucket": "100_TO_1K_PER_HR",
  "callsPerMin": 18.2,
  "impactScore": 92.4,
  "bottleneckType": "LARGE_SEQ_SCAN",
  "analysisStatus": "SIMULATED",
  "privacyStatus": "VERIFIED_MASKED",
  "observedAt": "2 mins ago",
  "planGraph": {
    "id": "pg-7c91",
    "queryEventId": "qry-7c91",
    "planCost": 182341.2,
    "planDepth": 4,
    "nodeCount": 5,
    "nodes": [
      {
        "id": "node_1",
        "operatorType": "AGGREGATE",
        "estimatedCost": 182341.2,
        "estimatedRowsBucket": "100_TO_1K",
        "actualRowsBucket": "100_TO_1K",
        "actualTimeMsBucket": "2S_TO_3S",
        "loopsBucket": "1",
        "depth": 0,
        "isCritical": false,
        "notes": "GroupAggregate on COL_REGION_ID, date_trunc"
      },
      {
        "id": "node_2",
        "parentId": "node_1",
        "operatorType": "NESTED_LOOP",
        "joinType": "INNER",
        "estimatedCost": 178920.0,
        "estimatedRowsBucket": "1M_TO_10M",
        "actualRowsBucket": "1M_TO_10M",
        "actualTimeMsBucket": "2S_TO_3S",
        "loopsBucket": "1",
        "depth": 1,
        "isCritical": true,
        "notes": "High cost nested loop with unindexed inner sequential scan"
      }
    ]
  },
  "recommendations": [],
  "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
}
```
- **Loading State**: Table shimmer skeleton.
- **Error State**: Red banner with retry button.
- **Empty State**: "No slow queries match the current filter criteria."
- **Privacy Constraints**: All query strings must be masked templates with `:TEXT`, `:INT`, `:TIMESTAMP` and `TBL_*`, `COL_*`.

---

### 2.3 `GET /api/recommendations` & `GET /api/recommendations/{id}`
- **Purpose**: Populates `RecommendationsView.tsx` and `RecommendationDetailView.tsx`.
- **Response Schema (`Recommendation`)**:
```json
{
  "id": "rec-9182",
  "queryEventId": "qry-7c91",
  "actionType": "INDEX",
  "title": "Add Composite B-Tree Index on (COL_REGION_ID, COL_TX_DATE)",
  "maskedChangeTemplate": "CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_SALES_REGION_DATE ON TBL_SALES (COL_REGION_ID, COL_TX_DATE);",
  "status": "VALIDATED",
  "confidence": "HIGH",
  "riskLevel": "LOW",
  "rankingScore": {
    "score": 87.5,
    "readBenefit": 92.0,
    "writePenalty": 12.0,
    "storagePenalty": 8.0,
    "operationalRisk": 5.0
  },
  "evidence": {
    "version": "1.0",
    "bottleneckType": "LARGE_SEQ_SCAN",
    "affectedPlanNodes": ["node_4"],
    "reasonCodes": [
      "UNINDEXED_FILTER_PREDICATE",
      "HIGH_COST_HEAP_TRAVERSAL",
      "HIGH_FREQUENCY_AMPLIFICATION"
    ],
    "observedEvidence": {
      "scanType": "SEQ_SCAN",
      "loopCountBucket": "1",
      "relationSizeBucket": "10M_PLUS_ROWS"
    },
    "recommendedAction": "CREATE_COMPOSITE_BTREE",
    "maskedChangeTemplate": "CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_SALES_REGION_DATE ON TBL_SALES (COL_REGION_ID, COL_TX_DATE);",
    "alternativesConsidered": [
      {
        "action": "SINGLE_COLUMN_INDEX_COL_TX_DATE",
        "rank": 2,
        "reasonLowerRank": "Lower selectivity than composite index with equality column first."
      }
    ],
    "confidence": "HIGH",
    "riskLevel": "LOW",
    "limitations": [
      "Simulation measured with HypoPG in session RAM.",
      "Write penalty estimated at 1–2ms per INSERT/UPDATE on TBL_SALES."
    ],
    "privacyStatus": "VERIFIED_MASKED"
  },
  "simulation": {
    "id": "sim-8812",
    "recommendationId": "rec-9182",
    "simulationEngine": "HYPOPG",
    "status": "COMPLETED",
    "baseline": {
      "plannerCost": 182341.2,
      "dominantOperations": ["SEQ_SCAN", "NESTED_LOOP"],
      "executionTimeEstimateMs": 2450.0
    },
    "candidate": {
      "plannerCost": 30510.8,
      "dominantOperations": ["INDEX_SCAN", "HASH_JOIN"],
      "executionTimeEstimateMs": 380.0
    },
    "estimatedImprovementPercentRange": [72, 85],
    "estimatedWriteOverheadMsRange": [1, 2],
    "estimatedStorageOverheadGbRange": [1.8, 2.4],
    "confidence": "HIGH",
    "limitations": [
      "HypoPG modifies virtual planner state; no physical disk index created."
    ],
    "runAt": "Just now"
  },
  "createdAt": "10 mins ago",
  "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
}
```

---

### 2.4 `POST /api/recommendations/{id}/simulate`
- **Purpose**: Triggered from `SimulationModal.tsx` or `RecommendationDetailView.tsx` to execute a HypoPG virtual index simulation in session RAM.
- **Request**: Empty body or `{}`.
- **Response**: `SimulationResult` object matching above schema.
- **Privacy & Safety Constraints**: Strictly in-memory session virtual index; `hypopg_reset()` executed immediately after EXPLAIN evaluation.

---

### 2.5 `POST /api/recommendations/{id}/approve` & `POST /api/recommendations/{id}/reject`
- **Purpose**: Triggered from `ApprovalDrawer.tsx`.
- **Request Body**:
```json
{
  "actor_id": "usr-1",
  "actor_name": "Priya Sharma (DBA)",
  "actor_role": "DBA",
  "reason": "Approved based on HypoPG cost reduction and low write risk."
}
```
- **Response**:
```json
{
  "success": true,
  "recommendation_id": "rec-9182",
  "new_status": "APPROVED",
  "audit_log_id": "aud-1727961234",
  "message": "Recommendation approved by DBA. Generated change script for human review. No production deployment occurred.",
  "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
}
```

---

### 2.6 `GET /api/audit-logs`
- **Purpose**: Populates `AuditLogsView.tsx`.
- **Response Schema (`AuditLogItem[]`)**:
```json
[
  {
    "id": "aud-101",
    "timestamp": "2026-10-03 12:45:00 UTC",
    "actorId": "usr-1",
    "actorName": "Priya Sharma (DBA)",
    "actorRole": "DBA",
    "eventType": "APPROVED",
    "entityType": "RECOMMENDATION",
    "entityId": "rec-9182",
    "description": "Recommendation rec-9182 approved by DBA. Generated change script for human review. No production deployment occurred.",
    "metadataJson": {
      "recommendationId": "rec-9182",
      "decision": "APPROVED",
      "policy": "NO_AUTOMATIC_PRODUCTION_DDL"
    },
    "privacyStatus": "VERIFIED_MASKED"
  }
]
```

---

### 2.7 `POST /api/telemetry/collect` & `GET /api/telemetry/status`
- **Purpose**: Ingests slow query statistics and execution plan trees from `workload-postgres`.
- **Response Schema**:
```json
{
  "status": "COMPLETED",
  "statements_scanned": 12,
  "events_created": 3,
  "privacy_check_passed": true,
  "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis.",
  "message": "Telemetry collected and sanitized successfully."
}
```

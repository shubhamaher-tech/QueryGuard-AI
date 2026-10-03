-- QueryGuard AI: Telemetry Pipeline Schema
-- Application Database: queryguard

CREATE TABLE IF NOT EXISTS telemetry_collection_runs (
    id VARCHAR(64) PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(30) DEFAULT 'RUNNING',
    statements_scanned INTEGER DEFAULT 0,
    events_created INTEGER DEFAULT 0,
    events_rejected_by_privacy_check INTEGER DEFAULT 0,
    privacy_check_passed BOOLEAN DEFAULT TRUE,
    error_summary_sanitized TEXT
);

CREATE INDEX IF NOT EXISTS idx_telemetry_runs_started_at ON telemetry_collection_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_runs_status ON telemetry_collection_runs (status);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id VARCHAR(64) PRIMARY KEY,
    run_id VARCHAR(64) REFERENCES telemetry_collection_runs(id) ON DELETE CASCADE,
    query_fingerprint VARCHAR(128) NOT NULL,
    masked_query_template TEXT NOT NULL,
    mean_latency_ms DOUBLE PRECISION NOT NULL,
    calls_count BIGINT DEFAULT 1,
    total_exec_time_ms DOUBLE PRECISION DEFAULT 0.0,
    rows_processed BIGINT DEFAULT 0,
    shared_blks_read BIGINT DEFAULT 0,
    shared_blks_hit BIGINT DEFAULT 0,
    temp_blks_read BIGINT DEFAULT 0,
    temp_blks_written BIGINT DEFAULT 0,
    has_temp_spill BOOLEAN DEFAULT FALSE,
    main_bottleneck VARCHAR(100) NOT NULL,
    plan_depth INTEGER DEFAULT 1,
    planner_total_cost DOUBLE PRECISION DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    privacy_check_passed BOOLEAN DEFAULT TRUE,
    privacy_status TEXT NOT NULL,
    features_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telemetry_events_fingerprint ON telemetry_events (query_fingerprint);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_run_id ON telemetry_events (run_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_created_at ON telemetry_events (created_at DESC);

CREATE TABLE IF NOT EXISTS sanitized_plan_nodes (
    id VARCHAR(64) PRIMARY KEY,
    event_id VARCHAR(64) REFERENCES telemetry_events(id) ON DELETE CASCADE,
    node_uid VARCHAR(32) NOT NULL,
    operator_type VARCHAR(100) NOT NULL,
    relation_token VARCHAR(100),
    estimated_cost_bucket VARCHAR(50),
    estimated_rows_bucket VARCHAR(50),
    loops_bucket VARCHAR(50),
    is_bottleneck BOOLEAN DEFAULT FALSE,
    bottleneck_type VARCHAR(100),
    details_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_plan_nodes_event_id ON sanitized_plan_nodes (event_id);

CREATE TABLE IF NOT EXISTS sanitized_plan_edges (
    id VARCHAR(64) PRIMARY KEY,
    event_id VARCHAR(64) REFERENCES telemetry_events(id) ON DELETE CASCADE,
    parent_node_uid VARCHAR(32) NOT NULL,
    child_node_uid VARCHAR(32) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_plan_edges_event_id ON sanitized_plan_edges (event_id);

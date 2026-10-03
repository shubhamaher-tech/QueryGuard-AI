-- QueryGuard AI PostgreSQL 16 Schema Definition
-- Database: queryguard

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'DBA' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS query_events (
    id VARCHAR(64) PRIMARY KEY,
    fingerprint VARCHAR(64) NOT NULL,
    anonymized_sql TEXT NOT NULL,
    table_token VARCHAR(64) NOT NULL,
    avg_latency_ms DOUBLE PRECISION NOT NULL,
    calls_per_minute INTEGER DEFAULT 100,
    primary_bottleneck VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(30) DEFAULT 'NEEDS_REVIEW',
    plan_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_events_fingerprint ON query_events (fingerprint);
CREATE INDEX IF NOT EXISTS idx_query_events_risk ON query_events (risk_level);
CREATE INDEX IF NOT EXISTS idx_query_events_status ON query_events (status);

CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(64) PRIMARY KEY,
    query_id VARCHAR(64) REFERENCES query_events(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    recommended_action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING',
    confidence_score DOUBLE PRECISION DEFAULT 0.85,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    xai_evidence JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_query ON recommendations (query_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations (status);

CREATE TABLE IF NOT EXISTS simulations (
    id VARCHAR(64) PRIMARY KEY,
    recommendation_id VARCHAR(64) REFERENCES recommendations(id) ON DELETE CASCADE,
    simulation_type VARCHAR(50) DEFAULT 'HYPOTHETICAL_INDEX',
    status VARCHAR(30) DEFAULT 'COMPLETED',
    label VARCHAR(50) DEFAULT 'Simulated estimate',
    before_cost DOUBLE PRECISION NOT NULL,
    after_cost DOUBLE PRECISION NOT NULL,
    before_latency_ms DOUBLE PRECISION NOT NULL,
    after_latency_ms DOUBLE PRECISION NOT NULL,
    improvement_pct DOUBLE PRECISION NOT NULL,
    write_latency_impact_ms DOUBLE PRECISION DEFAULT 0.0,
    storage_overhead_gb DOUBLE PRECISION DEFAULT 0.0,
    confidence DOUBLE PRECISION DEFAULT 0.90,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    simulated_plan_nodes JSONB,
    baseline_data JSONB,
    proposal_data JSONB,
    impact_data JSONB,
    acceptance_decision JSONB,
    privacy_status TEXT DEFAULT 'No raw rows, literals, or plaintext schema identifiers were used.',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_simulations_rec ON simulations (recommendation_id);

CREATE TABLE IF NOT EXISTS approvals (
    id VARCHAR(64) PRIMARY KEY,
    recommendation_id VARCHAR(64) REFERENCES recommendations(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approvals_rec ON approvals (recommendation_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    query_id VARCHAR(64),
    recommendation_id VARCHAR(64),
    anonymized_target VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs (timestamp DESC);

CREATE TABLE IF NOT EXISTS sql_rewrites (
    id VARCHAR(64) PRIMARY KEY,
    query_id VARCHAR(64) REFERENCES query_events(id) ON DELETE CASCADE,
    cache_key VARCHAR(128),
    route_decision VARCHAR(50) NOT NULL,
    route_reason_codes JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    original_sql_template TEXT NOT NULL,
    rewritten_sql_template TEXT,
    rewrite_strategy TEXT,
    suggested_index_patterns JSONB,
    assumptions JSONB,
    risk_notes JSONB,
    safety_checks_passed BOOLEAN DEFAULT FALSE,
    safety_rejection_reason TEXT,
    baseline_plan_summary JSONB,
    rewritten_plan_summary JSONB,
    cost_improvement_pct DOUBLE PRECISION,
    simulation_decision JSONB,
    xai_evidence JSONB,
    privacy_status TEXT DEFAULT 'No raw rows, raw literals, or plaintext schema identifiers were used.',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sql_rewrites_query ON sql_rewrites (query_id);
CREATE INDEX IF NOT EXISTS idx_sql_rewrites_cache_key ON sql_rewrites (cache_key);

import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    employee_id = Column(String(64), unique=True, nullable=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(120), nullable=True)
    department = Column(String(100), nullable=True)
    role = Column(String(50), default="DBA", nullable=False)  # DBA, ENGINEER, VIEWER
    hierarchy_level = Column(Integer, default=1, nullable=False)  # 3: DBA (Admin), 2: ENGINEER, 1: VIEWER
    avatar = Column(String(10), default="PS")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class QueryEvent(Base):
    __tablename__ = "query_events"

    id = Column(String(64), primary_key=True, index=True)
    fingerprint = Column(String(64), index=True, nullable=False)
    anonymized_sql = Column(Text, nullable=False)
    table_token = Column(String(64), nullable=False)
    avg_latency_ms = Column(Float, nullable=False)
    calls_per_minute = Column(Integer, default=100)
    primary_bottleneck = Column(String(100), nullable=False)
    risk_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    status = Column(String(30), default="NEEDS_REVIEW")  # NEEDS_REVIEW, SIMULATED, APPROVED, REJECTED
    plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recommendations = relationship("Recommendation", back_populates="query", cascade="all, delete-orphan")
    sql_rewrites = relationship("SqlRewrite", back_populates="query", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    query_id = Column(String(64), ForeignKey("query_events.id"), nullable=False)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # INDEX_COMPOSITE, REWRITE_QUERY, TABLE_PARTITIONING
    recommended_action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    status = Column(String(30), default="PENDING")  # PENDING, SIMULATED, APPROVED, REJECTED
    confidence_score = Column(Float, default=0.85)
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    xai_evidence = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    query = relationship("QueryEvent", back_populates="recommendations")
    simulations = relationship("Simulation", back_populates="recommendation", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="recommendation", cascade="all, delete-orphan")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), ForeignKey("recommendations.id"), nullable=False)
    simulation_type = Column(String(50), default="HYPOTHETICAL_INDEX")
    status = Column(String(30), default="COMPLETED")
    label = Column(String(50), default="Simulated estimate")
    before_cost = Column(Float, nullable=False)
    after_cost = Column(Float, nullable=False)
    before_latency_ms = Column(Float, nullable=False)
    after_latency_ms = Column(Float, nullable=False)
    improvement_pct = Column(Float, nullable=False)
    write_latency_impact_ms = Column(Float, default=0.0)
    storage_overhead_gb = Column(Float, default=0.0)
    confidence = Column(Float, default=0.90)
    risk_level = Column(String(20), default="LOW")
    simulated_plan_nodes = Column(JSON, nullable=True)
    baseline_data = Column(JSON, nullable=True)
    proposal_data = Column(JSON, nullable=True)
    impact_data = Column(JSON, nullable=True)
    acceptance_decision = Column(JSON, nullable=True)
    privacy_status = Column(Text, default="No raw rows, literals, or plaintext schema identifiers were used.")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recommendation = relationship("Recommendation", back_populates="simulations")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), ForeignKey("recommendations.id"), nullable=False)
    action = Column(String(20), nullable=False)  # APPROVED, REJECTED
    actor_id = Column(String(64), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recommendation = relationship("Recommendation", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    query_id = Column(String(64), nullable=True)
    recommendation_id = Column(String(64), nullable=True)
    anonymized_target = Column(String(100), nullable=False)
    action_type = Column(String(50), nullable=False)  # QUERY_ANONYMIZED, SIMULATION_RUN, APPROVED, REJECTED
    actor_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True)


class TelemetryCollectionRun(Base):
    __tablename__ = "telemetry_collection_runs"

    id = Column(String(64), primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    statements_scanned = Column(Integer, default=0)
    events_created = Column(Integer, default=0)
    events_rejected_by_privacy_check = Column(Integer, default=0)
    privacy_check_passed = Column(Integer, default=1)  # Boolean flag (1=True, 0=False)
    error_summary_sanitized = Column(Text, nullable=True)

    events = relationship("TelemetryEvent", back_populates="run", cascade="all, delete-orphan")


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("telemetry_collection_runs.id"), nullable=True)
    query_fingerprint = Column(String(128), index=True, nullable=False)
    masked_query_template = Column(Text, nullable=False)
    mean_latency_ms = Column(Float, nullable=False)
    calls_count = Column(Integer, default=1)
    total_exec_time_ms = Column(Float, default=0.0)
    rows_processed = Column(Integer, default=0)
    shared_blks_read = Column(Integer, default=0)
    shared_blks_hit = Column(Integer, default=0)
    temp_blks_read = Column(Integer, default=0)
    temp_blks_written = Column(Integer, default=0)
    has_temp_spill = Column(Integer, default=0)  # Boolean flag (1=True, 0=False)
    main_bottleneck = Column(String(100), nullable=False)
    plan_depth = Column(Integer, default=1)
    planner_total_cost = Column(Float, default=0.0)
    risk_level = Column(String(20), default="LOW")
    privacy_check_passed = Column(Integer, default=1)
    privacy_status = Column(Text, nullable=False)
    features_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    run = relationship("TelemetryCollectionRun", back_populates="events")
    plan_nodes = relationship("SanitizedPlanNode", back_populates="event", cascade="all, delete-orphan")
    plan_edges = relationship("SanitizedPlanEdge", back_populates="event", cascade="all, delete-orphan")


class SanitizedPlanNode(Base):
    __tablename__ = "sanitized_plan_nodes"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("telemetry_events.id"), nullable=False)
    node_uid = Column(String(32), nullable=False)
    operator_type = Column(String(100), nullable=False)
    relation_token = Column(String(100), nullable=True)
    estimated_cost_bucket = Column(String(50), nullable=True)
    estimated_rows_bucket = Column(String(50), nullable=True)
    loops_bucket = Column(String(50), nullable=True)
    is_bottleneck = Column(Integer, default=0)  # Boolean flag
    bottleneck_type = Column(String(100), nullable=True)
    details_json = Column(JSON, nullable=True)

    event = relationship("TelemetryEvent", back_populates="plan_nodes")


class SanitizedPlanEdge(Base):
    __tablename__ = "sanitized_plan_edges"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), ForeignKey("telemetry_events.id"), nullable=False)
    parent_node_uid = Column(String(32), nullable=False)
    child_node_uid = Column(String(32), nullable=False)

    event = relationship("TelemetryEvent", back_populates="plan_edges")
 
 
class SqlRewrite(Base):
    __tablename__ = "sql_rewrites"

    id = Column(String(64), primary_key=True, index=True)
    query_id = Column(String(64), ForeignKey("query_events.id"), nullable=False)
    cache_key = Column(String(128), index=True, nullable=True)
    route_decision = Column(String(50), nullable=False)  # SIMPLE_QUERY_FAST_PATH, COMPLEX_QUERY_SLM_ROUTED
    route_reason_codes = Column(JSON, nullable=False)   # list of reason codes
    status = Column(String(50), nullable=False)         # NOT_ROUTED_SIMPLE_QUERY, LLM_PENDING, LLM_UNAVAILABLE, LLM_OUTPUT_INVALID, SAFETY_REJECTED, EXPLAIN_REJECTED, NO_MEASURABLE_BENEFIT, SIMULATION_PASSED, READY_FOR_DBA_REVIEW
    original_sql_template = Column(Text, nullable=False)
    rewritten_sql_template = Column(Text, nullable=True)
    rewrite_strategy = Column(Text, nullable=True)
    suggested_index_patterns = Column(JSON, nullable=True)
    assumptions = Column(JSON, nullable=True)
    risk_notes = Column(JSON, nullable=True)
    safety_checks_passed = Column(Integer, default=0)
    safety_rejection_reason = Column(Text, nullable=True)
    baseline_plan_summary = Column(JSON, nullable=True)
    rewritten_plan_summary = Column(JSON, nullable=True)
    cost_improvement_pct = Column(Float, nullable=True)
    simulation_decision = Column(JSON, nullable=True)
    xai_evidence = Column(JSON, nullable=True)
    privacy_status = Column(Text, default="No raw rows, raw literals, or plaintext schema identifiers were used.")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    query = relationship("QueryEvent", back_populates="sql_rewrites")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    analysis_id = Column(String(64), primary_key=True, index=True)
    source_type = Column(String(50), default="USER_SUBMITTED_QUERY")
    sandbox_dataset = Column(String(50), default="synthetic_ecommerce")
    status = Column(String(30), default="COMPLETED")  # PENDING, VALIDATING, MASKING, EXPLAINING, ANALYZING, COMPLETED, FAILED
    masked_query_template = Column(Text, nullable=False)
    query_fingerprint = Column(String(64), index=True, nullable=False)
    privacy_check_passed = Column(Integer, default=1)
    masked_literals_count = Column(Integer, default=0)
    tokenized_identifiers_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    safe_error_code = Column(String(50), nullable=True)
    safe_error_message = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    main_bottleneck = Column(String(100), nullable=True)
    severity = Column(String(20), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation_count = Column(Integer, default=1)
    
    # Structured metadata (strictly masked / zero raw identifiers)
    plan_json = Column(JSON, nullable=True)
    plan_graph = Column(JSON, nullable=True)
    xai_evidence = Column(JSON, nullable=True)
    gnn_prediction = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    simulation = Column(JSON, nullable=True)
    approval_status = Column(String(30), default="PENDING")  # PENDING, APPROVED, REJECTED
    approval_comment = Column(Text, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    privacy_status = Column(Text, default="No raw rows, raw literals, or plaintext schema identifiers were used.")



from __future__ import annotations
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Plan Node Schema for React Flow Visualization & Backend Analysis
class PlanNode(BaseModel):
    id: str
    node_type: str
    relation_name: Optional[str] = None
    startup_cost: float = 0.0
    total_cost: float = 0.0
    plan_rows: int = 0
    actual_rows: int = 0
    actual_time_ms: float = 0.0
    loops: int = 1
    filter_expr: Optional[str] = None
    index_name: Optional[str] = None
    sort_key: Optional[str] = None
    is_bottleneck: bool = False
    bottleneck_reason: Optional[str] = None
    children: List[PlanNode] = []


# XAI Evidence Packet matching the requirement
class XAIEvidencePacket(BaseModel):
    bottleneck_type: str
    affected_plan_nodes: List[str]
    evidence_signals: List[str] = Field(default_factory=list)
    recommended_action: str
    expected_read_improvement_percent_range: List[float] = Field(default_factory=lambda: [60.0, 85.0])
    estimated_write_latency_increase_ms_range: List[float] = Field(default_factory=lambda: [0.5, 1.8])
    estimated_storage_overhead_gb_range: List[float] = Field(default_factory=lambda: [1.0, 3.5])
    confidence: float = Field(default=0.92, ge=0.0, le=1.0)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    privacy_status: str = (
        "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    )


# Simulation Sub-Models for HypoPG
class PlanSummary(BaseModel):
    main_operator: str
    operator_counts: Dict[str, int] = Field(default_factory=dict)
    plan_depth: int = 1


class SanitizedPlanGraphData(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class BaselineSimulation(BaseModel):
    planner_total_cost: float
    plannerCost: Optional[float] = None
    dominantOperations: List[str] = Field(default_factory=lambda: ["SEQ_SCAN", "NESTED_LOOP"])
    executionTimeEstimateMs: Optional[float] = None
    plan_summary: Optional[PlanSummary] = None
    plan_graph: Optional[SanitizedPlanGraphData] = None

    model_config = ConfigDict(extra="allow")


class ProposalSimulation(BaseModel):
    hypothetical_index_token: str
    index_pattern: List[str]
    planner_total_cost: float
    plannerCost: Optional[float] = None
    dominantOperations: List[str] = Field(default_factory=lambda: ["INDEX_SCAN", "HASH_JOIN"])
    executionTimeEstimateMs: Optional[float] = None
    plan_summary: Optional[PlanSummary] = None
    plan_graph: Optional[SanitizedPlanGraphData] = None

    model_config = ConfigDict(extra="allow")


class ImpactSimulation(BaseModel):
    estimated_planner_cost_reduction_percent: float
    estimated_latency_improvement_percent_range: List[float]
    estimated_write_latency_increase_ms_range: List[float]
    estimated_storage_overhead_gb_range: List[float]


class AcceptanceDecision(BaseModel):
    accepted: bool
    reason_codes: List[str] = Field(default_factory=list)
    confidence: str = "MEDIUM"
    risk_level: str = "LOW"


class RankingScoreBreakdown(BaseModel):
    score: float = 85.0
    readBenefit: float = 90.0
    writePenalty: float = 10.0
    storagePenalty: float = 8.0
    operationalRisk: float = 5.0


# Simulation Models
class SimulationResponse(BaseModel):
    id: str
    recommendation_id: str
    recommendationId: Optional[str] = None
    simulation_type: str = "HYPOTHETICAL_INDEX"
    simulationEngine: str = "HYPOPG"
    status: str = "COMPLETED"
    label: str = "Simulated estimate"
    baseline: Optional[Any] = None
    proposal: Optional[ProposalSimulation] = None
    candidate: Optional[Any] = None
    impact: Optional[ImpactSimulation] = None
    acceptance_decision: Optional[AcceptanceDecision] = None
    estimatedImprovementPercentRange: Optional[List[float]] = None
    estimatedWriteOverheadMsRange: Optional[List[float]] = None
    estimatedStorageOverheadGbRange: Optional[List[float]] = None
    limitations: List[str] = Field(default_factory=list)
    runAt: str = "Just now"
    privacy_status: str = "No raw rows, literals, or plaintext schema identifiers were used."
    xai_explanation: Optional[str] = None

    # Backward-compatible fields
    before_cost: float = 0.0
    after_cost: float = 0.0
    before_latency_ms: float = 0.0
    after_latency_ms: float = 0.0
    improvement_pct: float = 0.0
    write_latency_impact_ms: float = 0.0
    storage_overhead_gb: float = 0.0
    confidence: Any = 0.90
    risk_level: str = "LOW"
    riskLevel: str = "LOW"
    is_simulated_estimate: bool = True
    notice: str = "Simulated estimate. No production DDL or workload changes were applied."
    simulated_plan_nodes: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Recommendation Models
class RecommendationResponse(BaseModel):
    id: str
    query_id: str
    queryEventId: Optional[str] = None
    title: str
    type: str  # INDEX_COMPOSITE, REWRITE_QUERY, TABLE_PARTITIONING
    actionType: Optional[str] = "INDEX"
    recommended_action: str
    maskedChangeTemplate: Optional[str] = None
    rationale: str
    status: str  # PENDING, SIMULATED, APPROVED, REJECTED, VALIDATED
    confidence_score: float = 0.85
    confidence: str = "HIGH"
    risk_level: str = "LOW"
    riskLevel: str = "LOW"
    rankingScore: Optional[RankingScoreBreakdown] = None
    xai_evidence: Optional[XAIEvidencePacket] = None
    evidence: Optional[Dict[str, Any]] = None
    simulations: List[SimulationResponse] = Field(default_factory=list)
    simulation: Optional[Any] = None
    created_at: Optional[datetime] = None
    createdAt: Optional[str] = "10 mins ago"
    resolvedAt: Optional[str] = None
    resolvedBy: Optional[str] = None
    rejectionReason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Query Event Models
class QueryEventResponse(BaseModel):
    id: str
    fingerprint: str = ""
    queryFingerprint: Optional[str] = None
    title: Optional[str] = None
    anonymized_sql: str = ""
    maskedQueryTemplate: Optional[str] = None
    table_token: str = ""
    avg_latency_ms: float = 0.0
    averageDurationMs: Optional[float] = None
    calls_per_minute: int = 100
    callsPerMin: Optional[float] = None
    latencyMsBucket: str = "1S_TO_5S"
    frequencyBucket: str = "100_TO_1K_PER_HR"
    impactScore: float = 85.0
    primary_bottleneck: str = "LARGE_SEQ_SCAN"
    bottleneckType: str = "LARGE_SEQ_SCAN"
    risk_level: str = "LOW"
    status: str = "NEEDS_REVIEW"
    analysisStatus: str = "ANALYZED"
    privacyStatus: str = "VERIFIED_MASKED"
    observedAt: str = "2 mins ago"
    planGraph: Optional[Dict[str, Any]] = None
    recommendations: List[Any] = Field(default_factory=list)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QueryDetailResponse(QueryEventResponse):
    plan_json: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[RecommendationResponse] = Field(default_factory=list)
    privacy_status: str = (
        "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    )


# Approval Models
class ApprovalRequest(BaseModel):
    actor_id: str = "DBA_ADMIN_01"
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    comment: Optional[str] = "Approved after reviewing simulated latency gain and safety boundaries."
    reason: Optional[str] = None


class RejectionRequest(BaseModel):
    actor_id: str = "DBA_ADMIN_01"
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    comment: Optional[str] = "Rejected due to unacceptable write latency overhead or maintenance window constraints."
    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: str
    recommendation_id: str
    recommendationId: Optional[str] = None
    action: str  # APPROVED, REJECTED
    new_status: Optional[str] = None
    actor_id: str
    comment: Optional[str] = None
    created_at: datetime
    message: str
    success: bool = True
    audit_log_id: Optional[str] = None
    privacy_status: str = (
        "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    )

    model_config = ConfigDict(from_attributes=True)


# Audit Log Model
class AuditLogResponse(BaseModel):
    id: str
    query_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    anonymized_target: str = ""
    action_type: str = ""
    actor_id: str = ""
    timestamp: Any = None
    details: Optional[Dict[str, Any]] = None

    # Cloned frontend fields
    actorId: Optional[str] = None
    actorName: Optional[str] = None
    actorRole: Optional[str] = "DBA"
    eventType: Optional[str] = None
    entityType: Optional[str] = "RECOMMENDATION"
    entityId: Optional[str] = None
    description: Optional[str] = None
    metadataJson: Optional[Dict[str, Any]] = None
    privacyStatus: str = "VERIFIED_MASKED"

    model_config = ConfigDict(from_attributes=True)


# Dashboard Summary Model
class LatencyPoint(BaseModel):
    timestamp: str
    latency_ms: float
    p95_latency_ms: float
    calls_count: int


class DashboardSummary(BaseModel):
    slow_queries_count: int
    high_risk_recommendations_count: int
    avg_estimated_gain_pct: float
    pending_approvals_count: int
    recent_slow_queries: List[QueryEventResponse]
    recent_recommendations: List[RecommendationResponse]
    latency_trend: List[LatencyPoint]
    privacy_statement: str
    slm_status: Optional[str] = "AVAILABLE"  # AVAILABLE, LOADING_MODEL, UNAVAILABLE, DISABLED
    complex_queries_analyzed_count: int = 0
    rewrite_candidates_accepted_count: int = 0
    rewrite_candidates_rejected_count: int = 0

    # Contract / Cloned Frontend fields
    high_impact_queries_count: Optional[int] = None
    pending_approvals_count: int = 0
    validated_simulations_count: Optional[int] = None
    simulated_max_gain_pct: Optional[float] = None
    triage_top_query: Optional[Dict[str, Any]] = None
    privacy_status: Optional[str] = None


# Privacy Utility API Schemas
class SanitizeSqlRequest(BaseModel):
    raw_sql: str


class SanitizeSqlResponse(BaseModel):
    raw_input_received: bool = True
    sanitized_sql: str
    literals_masked: bool = True
    schema_tokenized: bool = True
    privacy_status: str

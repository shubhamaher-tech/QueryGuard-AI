from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class LLMStatusResponse(BaseModel):
    enabled: bool
    service_reachable: bool
    selected_model: str
    model_available_locally: bool
    local_only_privacy_mode: bool = True
    message: str
    available_models: List[str] = Field(default_factory=list)

class IndexPatternSuggestion(BaseModel):
    table_token: str
    columns: List[str]
    reason: str

class SLMRewriteOutput(BaseModel):
    action_type: Literal["SQL_REWRITE", "NO_REWRITE"]
    rewritten_sql_template: Optional[str] = None
    rewrite_strategy: str
    suggested_index_patterns: List[IndexPatternSuggestion] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risk_notes: List[str] = Field(default_factory=list)
    expected_benefit_level: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]

class RewriteRouteResult(BaseModel):
    is_complex: bool
    route_decision: str  # "SIMPLE_QUERY_FAST_PATH" | "COMPLEX_QUERY_SLM_ROUTED"
    route_reason_codes: List[str]
    cache_key: str

class SanitizedPromptContext(BaseModel):
    query_fingerprint: str
    query_type: str = "SELECT"
    masked_query_template: str
    join_count: int
    plan_depth: int
    bottleneck_labels: List[str]
    sanitized_operator_sequence: List[str]
    masked_table_tokens: List[str]
    masked_column_tokens: List[str]
    column_type_categories: Dict[str, str] = Field(default_factory=dict)
    selectivity_buckets: Dict[str, str] = Field(default_factory=dict)
    table_size_buckets: Dict[str, str] = Field(default_factory=dict)
    existing_masked_index_patterns: List[str] = Field(default_factory=list)
    is_partitioned: bool = False
    baseline_planner_cost_bucket: str = "HIGH"
    rule_reason_codes: List[str] = Field(default_factory=list)
    xai_evidence_signals: List[str] = Field(default_factory=list)

class PlanSummaryMetrics(BaseModel):
    main_operator: str
    total_cost: float
    startup_cost: float
    plan_depth: int
    seq_scan_count: int
    nested_loop_count: int
    sort_count: int
    estimated_rows: float

class RewriteAnalysisResponse(BaseModel):
    id: str
    query_id: str
    route_decision: str
    route_reason_codes: List[str]
    status: str  # NOT_ROUTED_SIMPLE_QUERY, LLM_PENDING, LLM_UNAVAILABLE, LLM_OUTPUT_INVALID, SAFETY_REJECTED, EXPLAIN_REJECTED, NO_MEASURABLE_BENEFIT, SIMULATION_PASSED, READY_FOR_DBA_REVIEW
    original_sql_template: str
    rewritten_sql_template: Optional[str] = None
    rewrite_strategy: Optional[str] = None
    suggested_index_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risk_notes: List[str] = Field(default_factory=list)
    safety_checks_passed: bool = False
    safety_rejection_reason: Optional[str] = None
    baseline_plan_summary: Optional[Dict[str, Any]] = None
    rewritten_plan_summary: Optional[Dict[str, Any]] = None
    cost_improvement_pct: Optional[float] = None
    simulation_decision: Optional[Dict[str, Any]] = None
    xai_evidence: Optional[Dict[str, Any]] = None
    cached: bool = False
    privacy_status: str = "No raw rows, raw literals, or plaintext schema identifiers were used."
    notice: str = "Local SLM candidate evaluated against PostgreSQL optimizer via deterministic simulation."
    created_at: Optional[str] = None

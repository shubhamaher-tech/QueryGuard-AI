from __future__ import annotations
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SanitizedPlanNodeSchema(BaseModel):
    node_uid: str
    operator_type: str
    relation_token: Optional[str] = None
    estimated_cost_bucket: Optional[str] = None
    estimated_rows_bucket: Optional[str] = None
    loops_bucket: Optional[str] = None
    is_bottleneck: bool = False
    bottleneck_type: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SanitizedPlanEdgeSchema(BaseModel):
    parent_node_uid: str
    child_node_uid: str

    model_config = ConfigDict(from_attributes=True)


class TelemetryEventSummary(BaseModel):
    id: str
    run_id: Optional[str] = None
    query_fingerprint: str
    masked_query_template: str
    mean_latency_ms: float
    mean_latency_bucket: str
    calls_count: int
    calls_bucket: str
    total_exec_time_ms: float
    rows_processed: int
    has_temp_spill: bool
    main_bottleneck: str
    plan_depth: int
    planner_total_cost: float
    risk_level: str
    privacy_check_passed: bool
    privacy_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryEventDetail(TelemetryEventSummary):
    plan_nodes: List[SanitizedPlanNodeSchema] = []
    plan_edges: List[SanitizedPlanEdgeSchema] = []
    features_json: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    evidence_packet: Optional[Dict[str, Any]] = None
    honesty_label: str = "Rule-based plan graph analysis; GNN/RL-ready architecture."

    model_config = ConfigDict(from_attributes=True)


class TelemetryRunStatusResponse(BaseModel):
    id: Optional[str] = None
    status: str = "IDLE"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    statements_scanned: int = 0
    events_created: int = 0
    events_rejected_by_privacy_check: int = 0
    privacy_check_passed: bool = True
    privacy_status: str = "Passed"
    message: str = "No raw rows, raw literals, or plaintext schema identifiers were stored."

    model_config = ConfigDict(from_attributes=True)


class TelemetryCollectResponse(BaseModel):
    run_id: str
    status: str
    statements_scanned: int
    events_created: int
    events_rejected_by_privacy_check: int
    privacy_check_passed: bool
    privacy_status: str
    message: str
    events: List[TelemetryEventSummary] = []

    model_config = ConfigDict(from_attributes=True)

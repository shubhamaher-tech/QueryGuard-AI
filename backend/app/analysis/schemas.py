"""
Pydantic Schemas for Interactive Query Analysis Workspace
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyzeQueryRequest(BaseModel):
    query: str = Field(..., description="Raw SELECT query submitted by the DBA for sandbox analysis")
    dataset: str = Field(default="synthetic_ecommerce", description="Target sandbox benchmark dataset (synthetic_ecommerce, tpch_sf01, tpch_sf1, job_imdb)")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional flags (e.g. enable_gnn, run_hypopg)")


class AnalysisJobResponse(BaseModel):
    analysis_id: str
    source_type: str = "USER_SUBMITTED_QUERY"
    sandbox_dataset: str = "synthetic_ecommerce"
    status: str = "COMPLETED"
    masked_query_template: str
    query_fingerprint: str
    privacy_check_passed: int = 1
    masked_literals_count: int = 0
    tokenized_identifiers_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    safe_error_code: Optional[str] = None
    safe_error_message: Optional[str] = None
    diagnosis: Optional[str] = None
    main_bottleneck: Optional[str] = None
    severity: str = "MEDIUM"
    recommendation_count: int = 1
    
    plan_json: Optional[Any] = None
    plan_graph: Optional[Dict[str, Any]] = None
    xai_evidence: Optional[Dict[str, Any]] = None
    gnn_prediction: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    simulation: Optional[Dict[str, Any]] = None
    
    approval_status: str = "PENDING"
    approval_comment: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    privacy_status: str = "No raw rows, raw literals, or plaintext schema identifiers were persisted."

    class Config:
        from_attributes = True


class AnalysisProgressEvent(BaseModel):
    step: str
    progress_pct: int
    message: str
    details: Optional[Dict[str, Any]] = None


class SimulateAnalysisRequest(BaseModel):
    recommendation_index: Optional[int] = 0
    candidate_index_ddl: Optional[str] = None


class ApproveAnalysisRequest(BaseModel):
    decision: str = Field(..., description="APPROVED or REJECTED")
    reason: Optional[str] = Field(default=None, description="DBA rationale or review comment")
    actor: Optional[str] = Field(default="DBA_ADMIN_01", description="Approving DBA identity")


class SampleQueryItem(BaseModel):
    id: str
    name: str
    dataset: str
    description: str
    sql: str
    expected_bottleneck: str
    complexity: str  # SIMPLE, MODERATE, COMPLEX


class BenchmarkInfo(BaseModel):
    id: str
    name: str
    description: str
    is_available: bool
    table_count: int
    estimated_rows: int
    tables: List[str]
    sample_queries: List[SampleQueryItem]


class BenchmarkStatusResponse(BaseModel):
    benchmarks: List[BenchmarkInfo]
    active_dataset: str
    environment: str = "Local Sandbox / Synthetic Workload (Read-Only)"

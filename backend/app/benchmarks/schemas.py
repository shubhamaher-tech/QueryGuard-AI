"""
Pydantic Schemas for QueryGuard AI Benchmark Datasets & TPC-H Automation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BenchmarkSetupRequest(BaseModel):
    scale_factor: float = Field(default=0.1, description="TPC-H scale factor (0.1 for ~100MB, 1.0 for ~1GB)")
    force_rebuild: bool = Field(default=False, description="Force re-generation even if dataset already exists")


class BenchmarkSetupStatus(BaseModel):
    dataset: str = "tpch"
    scale_factor: float = 0.1
    status: str = "IDLE"  # IDLE, GENERATING, VALIDATING, CLEANING, LOADING, READY, FAILED
    progress_pct: int = 0
    current_stage: str = "Not started"
    message: str = "Benchmark is in initial state."
    error: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BenchmarkValidationSummary(BaseModel):
    is_valid: bool
    scale_factor: float
    file_summaries: Dict[str, Any]
    total_files: int
    validation_errors: List[str]
    clean_status: str = "Validated"


class BenchmarkSummaryResponse(BaseModel):
    dataset: str
    scale_factor: float
    is_installed: bool
    status: str
    table_count: int
    estimated_rows: int
    table_rows: Dict[str, int]
    approved_queries_count: int
    disk_size_estimate_mb: float
    privacy_statement: str = "Benchmark data resides strictly in local workload-postgres. QueryGuard stores only sanitized metadata."


class RunWorkloadRequest(BaseModel):
    query_ids: Optional[List[str]] = Field(default=None, description="Optional subset of approved query IDs to run")
    iterations: int = Field(default=3, ge=1, le=20, description="Repetitions for each approved query template")
    concurrency: int = Field(default=1, ge=1, le=4, description="Concurrency level for local workload execution")


class RunWorkloadResponse(BaseModel):
    job_id: str
    status: str
    queries_executed: int
    total_iterations: int
    duration_ms: float
    message: str
    telemetry_collected: bool = True


class BenchmarkQueryRegistryItem(BaseModel):
    query_id: str
    name: str
    category: str
    complexity: str
    expected_bottleneck: str
    sanitized_template: str
    description: str


class BenchmarkCatalogStatus(BaseModel):
    benchmarks: List[Dict[str, Any]]
    active_dataset: str
    environment: str = "Local Sandbox / Synthetic Benchmark (Read-Only)"

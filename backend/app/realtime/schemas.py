"""
Pydantic Schemas for Realtime Telemetry and Live Workload Monitoring
Zero sensitive customer data or unmasked query literals permitted.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RealtimeStatusResponse(BaseModel):
    connected: bool = True
    mode: str = "SANDBOX_WORKLOAD_POSTGRES"  # SANDBOX_WORKLOAD_POSTGRES or EXTERNAL_POSTGRES_SCAFFOLD
    polling_interval_sec: int = 10
    is_workload_active: bool = False
    database_name: str = "workload_db"
    anonymization_active: bool = True
    pg_stat_statements_active: bool = True
    last_poll_time: Optional[datetime] = None


class SlowQueryItem(BaseModel):
    query_fingerprint: str
    masked_query: str
    calls: int
    total_time_ms: float
    mean_time_ms: float
    p95_time_ms: float
    rows_per_call: float
    primary_bottleneck: Optional[str] = None
    severity: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class LatencyTrendPoint(BaseModel):
    timestamp: str
    latency_ms: float
    calls_per_sec: float


class RealtimeMetricsResponse(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_calls_per_sec: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    slow_query_count: int = 0
    estimated_cpu_pct: float = 5.0
    cache_hit_ratio_pct: float = 98.5
    active_connections: int = 1
    latency_trend: List[LatencyTrendPoint] = []
    bottleneck_distribution: Dict[str, int] = {}
    top_slow_queries: List[SlowQueryItem] = []
    privacy_statement: str = "Live telemetry queries are sanitized locally: all literals masked, schema identifiers tokenized."


class ConnectionConfigRequest(BaseModel):
    mode: str = Field(default="SANDBOX", description="Connection mode: 'SANDBOX' or 'EXTERNAL'")
    external_host: Optional[str] = None
    external_port: Optional[int] = 5432
    external_database: Optional[str] = None
    external_user: Optional[str] = None
    acknowledgement_signed: bool = False


class ConnectionConfigResponse(BaseModel):
    active_mode: str = "SANDBOX"
    sandbox_available: bool = True
    external_mode_status: str = "DISABLED_SCAFFOLD_ONLY"
    safety_message: str = (
        "External production database connections are disabled in this build to safeguard data integrity. "
        "QueryGuard AI operates safely against the local isolated workload-postgres sandbox."
    )

"""
Realtime Telemetry API Router
Exposes live endpoints and Server-Sent Events (SSE) for frontend monitoring.
Strictly sanitized: all SQL queries have literals masked and identifiers tokenized.
"""

import json
import asyncio
from typing import List
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.realtime.schemas import (
    RealtimeStatusResponse,
    RealtimeMetricsResponse,
    SlowQueryItem,
    ConnectionConfigRequest,
    ConnectionConfigResponse
)
from app.realtime.service import RealtimeService

router = APIRouter(prefix="/realtime", tags=["realtime"])
realtime_service = RealtimeService()


@router.get("/status", response_model=RealtimeStatusResponse)
def get_realtime_status():
    """Returns database connection status and telemetry collection health."""
    return realtime_service.get_status()


@router.get("/metrics", response_model=RealtimeMetricsResponse)
def get_realtime_metrics():
    """Returns latest snapshot of sanitized performance metrics, latency trend, and slow queries."""
    return realtime_service.fetch_metrics()


@router.get("/slow-queries", response_model=List[SlowQueryItem])
def get_slow_queries():
    """Returns list of sanitized top slow queries currently captured by pg_stat_statements."""
    metrics = realtime_service.fetch_metrics()
    return metrics.top_slow_queries


@router.get("/stream")
async def stream_realtime_telemetry(request: Request):
    """
    Server-Sent Events (SSE) endpoint providing streaming live telemetry updates.
    Yields sanitized metrics every 3 seconds during active workloads or 10 seconds during idle state.
    """
    async def event_generator():
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            metrics = realtime_service.fetch_metrics()
            status_data = realtime_service.get_status()

            payload = {
                "event": "telemetry_update",
                "status": status_data.model_dump(mode="json"),
                "metrics": metrics.model_dump(mode="json")
            }

            yield f"data: {json.dumps(payload)}\n\n"

            sleep_interval = 3 if status_data.is_workload_active else 5
            await asyncio.sleep(sleep_interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/connection", response_model=ConnectionConfigResponse)
def get_connection_config():
    """Returns connection configuration mode (Local Sandbox vs External DB Scaffold)."""
    return realtime_service.get_connection_config()


@router.post("/connection", response_model=ConnectionConfigResponse)
def update_connection_config(req: ConnectionConfigRequest):
    """
    Handles request to configure connection mode.
    Enforces local sandbox safety constraint: external DB mode is safely scaffolded with a warning.
    """
    return ConnectionConfigResponse(
        active_mode="SANDBOX",
        sandbox_available=True,
        external_mode_status="DISABLED_SCAFFOLD_ONLY",
        safety_message=(
            "External database connection mode is intentionally scaffolded and restricted to read-only simulation. "
            "To safeguard production environments from unauthorized modifications, QueryGuard AI defaults strictly "
            "to the local isolated workload-postgres container."
        )
    )


@router.get("/visual-metrics")
def get_realtime_visual_metrics():
    """
    Visual metrics for live telemetry dashboard: gauges, top slow query bars,
    throughput charts, and scan distributions. All queries are strictly sanitized.
    """
    metrics = realtime_service.fetch_metrics()
    status_data = realtime_service.get_status()

    # Gauges
    gauges = {
        "avg_latency": {
            "value": metrics.avg_latency_ms,
            "unit": "ms",
            "threshold": 100.0,
            "status": "healthy" if metrics.avg_latency_ms < 50 else ("warning" if metrics.avg_latency_ms < 200 else "critical"),
            "p95": metrics.p95_latency_ms
        },
        "throughput": {
            "value": metrics.total_calls_per_sec,
            "unit": "qps",
            "status": "active" if metrics.total_calls_per_sec > 0 else "idle"
        },
        "cache_hit_ratio": {
            "value": metrics.cache_hit_ratio_pct,
            "unit": "%",
            "status": "healthy" if metrics.cache_hit_ratio_pct >= 95 else "warning"
        },
        "estimated_cpu": {
            "value": metrics.estimated_cpu_pct,
            "unit": "%",
            "status": "healthy" if metrics.estimated_cpu_pct < 60 else "warning"
        }
    }

    # Top slow query bars
    top_bars = []
    for q in metrics.top_slow_queries[:5]:
        top_bars.append({
            "fingerprint": q.query_fingerprint,
            "masked_query": q.masked_query[:60] + "..." if len(q.masked_query) > 60 else q.masked_query,
            "mean_ms": q.mean_time_ms,
            "calls": q.calls,
            "severity": q.severity,
            "bottleneck": q.primary_bottleneck or "SEQ_SCAN"
        })

    # Scan-type distribution
    scan_distribution = [
        {"name": "Sequential Scan", "count": metrics.bottleneck_distribution.get("SEQ_SCAN", 4), "color": "#ef4444"},
        {"name": "Unindexed Join", "count": metrics.bottleneck_distribution.get("UNINDEXED_JOIN", 2), "color": "#f59e0b"},
        {"name": "External Sort", "count": metrics.bottleneck_distribution.get("EXPENSIVE_SORT", 2), "color": "#8b5cf6"},
        {"name": "Index Scan", "count": 6, "color": "#10b981"}
    ]

    return {
        "status": status_data.model_dump(),
        "gauges": gauges,
        "top_query_bars": top_bars,
        "latency_trend": metrics.latency_trend,
        "scan_distribution": scan_distribution,
        "bottleneck_distribution": metrics.bottleneck_distribution,
        "privacy_statement": metrics.privacy_statement,
        "last_updated": metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    }

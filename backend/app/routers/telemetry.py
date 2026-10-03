from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.telemetry.schemas import (
    TelemetryCollectResponse,
    TelemetryRunStatusResponse,
    TelemetryEventSummary,
    TelemetryEventDetail,
)
from app.telemetry.service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["Telemetry Pipeline"])


@router.post("/collect", response_model=TelemetryCollectResponse)
def trigger_telemetry_collection(db: Session = Depends(get_db)):
    """
    Triggers an on-demand telemetry collection run against workload-postgres.
    Collects allow-listed slow query statistics and EXPLAIN plans,
    sanitizes them locally using tenant-scoped HMAC-SHA256,
    verifies privacy compliance, and persists structural metadata.
    """
    try:
        result = TelemetryService.run_collection(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Telemetry collection failed: {str(e)}",
        )


@router.get("/status", response_model=TelemetryRunStatusResponse)
def get_telemetry_status(db: Session = Depends(get_db)):
    """
    Returns pipeline status, including last collection run, total scanned
    statements, sanitized events created, and privacy certification.
    """
    return TelemetryService.get_latest_status(db)


@router.get("/events", response_model=List[TelemetryEventSummary])
def list_telemetry_events(
    limit: int = Query(50, ge=1, le=200),
    bottleneck: Optional[str] = Query(None, description="Filter by bottleneck type"),
    db: Session = Depends(get_db),
):
    """
    Lists stored telemetry events with bucketed performance metrics.
    Strict privacy guarantee: Only masked templates, HMAC fingerprints,
    and bucketed metrics are exposed.
    """
    return TelemetryService.list_events(db, limit=limit, bottleneck=bottleneck)


@router.get("/events/{event_id}", response_model=TelemetryEventDetail)
def get_telemetry_event_detail(event_id: str, db: Session = Depends(get_db)):
    """
    Returns full telemetry event detail, including sanitized plan graph nodes
    and edges, XAI evidence packet, and AI recommendations.
    """
    detail = TelemetryService.get_event_detail(db, event_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Telemetry event {event_id} not found")
    return detail

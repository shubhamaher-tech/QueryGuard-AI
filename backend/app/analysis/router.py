"""
API Router for Interactive Query Analysis Workspace
"""

import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.analysis.schemas import (
    AnalyzeQueryRequest,
    AnalysisJobResponse,
    SimulateAnalysisRequest,
    ApproveAnalysisRequest,
    BenchmarkStatusResponse,
    SampleQueryItem,
)
from app.analysis.service import AnalysisService
from app.analysis.benchmark_catalog import (
    get_benchmark_catalog,
    get_sample_queries,
)

router = APIRouter(tags=["Interactive Query Analysis"])


@router.post(
    "/analyze-query",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze query in read-only sandbox environment",
)
async def analyze_query_endpoint(
    payload: AnalyzeQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Submits a user query for strict safety validation, privacy masking,
    sandboxed read-only EXPLAIN, GNN bottleneck diagnosis, and HypoPG simulation.
    Raw SQL is never saved to disk or logged.
    """
    try:
        job = await AnalysisService.analyze_query(payload, db=db)
        return job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query analysis failed: {str(e)}",
        )


@router.get(
    "/analyze-query/{analysis_id}",
    response_model=AnalysisJobResponse,
    summary="Get analysis results by ID",
)
def get_analysis_endpoint(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    job = AnalysisService.get_analysis(analysis_id, db=db)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found.",
        )
    return job


@router.get(
    "/analyze-query/{analysis_id}/events",
    summary="Server-Sent Events (SSE) stream for analysis progress",
)
async def stream_analysis_events_endpoint(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    Streams analysis progress events in SSE format.
    Gracefully completes with all recorded stages.
    """
    async def event_generator():
        # Check if job already exists
        job = AnalysisService.get_analysis(analysis_id, db=db)
        recorded_events = AnalysisService.get_progress_events(analysis_id)

        if recorded_events:
            for ev in recorded_events:
                data = json.dumps(ev.model_dump())
                yield f"event: progress\ndata: {data}\n\n"
                await asyncio.sleep(0.05)
        elif job:
            # Reconstruct stages from completed job
            stages = [
                {"step": "VALIDATING", "progress_pct": 20, "message": "Enforcing safety gateway and relation scope allowlists..."},
                {"step": "MASKING", "progress_pct": 40, "message": "Masking literals and tokenizing schema identifiers (HMAC-SHA256)..."},
                {"step": "EXPLAINING", "progress_pct": 60, "message": "Executing sandboxed EXPLAIN on read-only workload replica..."},
                {"step": "ANALYZING_RULES", "progress_pct": 80, "message": "Evaluating rule-based plan heuristics..."},
                {"step": "GNN_INFERENCE", "progress_pct": 90, "message": "Running Graph Neural Network structural bottleneck classifier..."},
                {"step": "COMPLETED", "progress_pct": 100, "message": "Analysis complete. Results ready for DBA review."},
            ]
            for st in stages:
                yield f"event: progress\ndata: {json.dumps(st)}\n\n"
                await asyncio.sleep(0.05)
        else:
            # Initial placeholder
            yield f"event: progress\ndata: {json.dumps({'step': 'WAITING', 'progress_pct': 5, 'message': 'Initializing sandbox analysis session...'})}\n\n"

        yield f"event: done\ndata: {json.dumps({'status': 'DONE', 'analysis_id': analysis_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/analyze-query/{analysis_id}/approve",
    response_model=AnalysisJobResponse,
    summary="Approve recommendations for an analysis job",
)
def approve_analysis_endpoint(
    analysis_id: str,
    payload: ApproveAnalysisRequest,
    db: Session = Depends(get_db),
):
    try:
        payload.decision = "APPROVED"
        return AnalysisService.approve_or_reject_analysis(analysis_id, payload, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.post(
    "/analyze-query/{analysis_id}/reject",
    response_model=AnalysisJobResponse,
    summary="Reject recommendations for an analysis job",
)
def reject_analysis_endpoint(
    analysis_id: str,
    payload: ApproveAnalysisRequest,
    db: Session = Depends(get_db),
):
    try:
        payload.decision = "REJECTED"
        return AnalysisService.approve_or_reject_analysis(analysis_id, payload, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get(
    "/benchmarks/status",
    response_model=BenchmarkStatusResponse,
    summary="Get status of sandbox benchmark workloads",
)
def get_benchmarks_status_endpoint():
    """
    Returns available benchmark workloads and their dataset status.
    """
    benchmarks = get_benchmark_catalog()
    return BenchmarkStatusResponse(
        benchmarks=benchmarks,
        active_dataset="synthetic_ecommerce",
        environment="Local Sandbox / Synthetic Workload (Read-Only)",
    )


@router.get(
    "/benchmarks/sample-queries",
    response_model=List[SampleQueryItem],
    summary="Get safe sample queries for sandbox testing",
)
def get_sample_queries_endpoint(
    dataset: Optional[str] = Query(None, description="Filter sample queries by benchmark dataset"),
):
    """
    Returns verified sample queries designed for sandbox performance analysis.
    """
    return get_sample_queries(dataset=dataset)

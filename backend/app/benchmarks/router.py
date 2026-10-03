"""
Benchmark API Router
Exposes REST endpoints for TPC-H generation, catalog status, database loading, and workload execution.
Adheres strictly to privacy controls: zero query rows or raw schema data returned.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Dict, Any

from app.benchmarks.schemas import (
    BenchmarkSetupRequest,
    BenchmarkSetupStatus,
    BenchmarkSummaryResponse,
    BenchmarkCatalogStatus,
    RunWorkloadRequest,
    RunWorkloadResponse
)
from app.benchmarks.service import BenchmarkService

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])
service = BenchmarkService()


@router.get("/catalog", response_model=BenchmarkCatalogStatus)
def get_benchmark_catalog():
    """Returns status and metadata of available benchmark workloads."""
    return service.get_catalog()


@router.get("/status")
def get_benchmarks_overview():
    """Returns overview of benchmark environments."""
    catalog = service.get_catalog()
    summary = service.get_summary()
    return {
        "catalog": catalog,
        "tpch_summary": summary,
        "environment": "Local Sandbox (workload-postgres)",
        "isolation_level": "Strictly Isolated / Read-Only Telemetry"
    }


@router.post("/tpch/setup", response_model=BenchmarkSetupStatus)
async def setup_tpch(req: BenchmarkSetupRequest):
    """
    Triggers generation and cleaning of TPC-H benchmark dataset.
    Runs asynchronously in background; poll /api/benchmarks/tpch/status for progress.
    """
    if req.scale_factor not in (0.1, 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supported scale factors are 0.1 (default) and 1.0"
        )
    return await service.start_setup(scale_factor=req.scale_factor, force_rebuild=req.force_rebuild)


@router.get("/tpch/status", response_model=BenchmarkSetupStatus)
def get_tpch_status():
    """Polls progress of TPC-H generation and validation."""
    return service.get_setup_status()


@router.get("/tpch/summary", response_model=BenchmarkSummaryResponse)
def get_tpch_summary():
    """Returns table row counts and disk metrics for TPC-H benchmark."""
    return service.get_summary()


@router.post("/tpch/load")
async def load_tpch():
    """Loads validated TPC-H data into workload-postgres database."""
    try:
        result = await service.load_into_database()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load TPC-H data into database: {str(e)}"
        )


@router.post("/tpch/run-workload", response_model=RunWorkloadResponse)
async def run_tpch_workload(req: RunWorkloadRequest):
    """
    Executes approved TPC-H queries against workload-postgres to stimulate pg_stat_statements.
    """
    try:
        return await service.run_workload(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running benchmark workload: {str(e)}"
        )


@router.post("/tpch/reset")
def reset_tpch():
    """Resets TPC-H tables in workload database."""
    try:
        return service.reset_dataset()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset TPC-H tables: {str(e)}"
        )


@router.get("/visual-summary")
def get_benchmarks_visual_summary():
    """
    Visual summary of all available benchmarks, table counts, disk footprints,
    and progress status.
    """
    cat = service.get_catalog()
    sum_resp = service.get_summary()
    st = service.get_setup_status()

    pipeline_progress = [
        {"step": "Generate", "status": "Completed" if sum_resp.is_installed else ("Active" if st.status == "GENERATING" else "Ready")},
        {"step": "Validate", "status": "Completed" if sum_resp.is_installed else ("Active" if st.status == "VALIDATING" else "Waiting")},
        {"step": "Load", "status": "Completed" if sum_resp.is_installed else ("Active" if st.status == "LOADING" else "Waiting")},
        {"step": "Analyze", "status": "Ready", "icon": "cpu"},
        {"step": "Ready", "status": "Completed" if sum_resp.is_installed else "Waiting"}
    ]

    return {
        "catalog": cat.benchmarks,
        "active_dataset": cat.active_dataset,
        "tpch_summary": sum_resp.model_dump(),
        "setup_status": st.model_dump(),
        "pipeline_progress": pipeline_progress,
        "environment": "Local Sandbox (workload-postgres)",
        "privacy_statement": "All benchmark data resides strictly in local isolated PostgreSQL container."
    }

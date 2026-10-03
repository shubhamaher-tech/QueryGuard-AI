"""
TPC-H & Benchmark Management Service
Provides business logic for setting up, validating, loading, and running benchmark workloads.
Strictly separates benchmark generation inside workload-postgres from QueryGuard application metadata.
"""

import os
import uuid
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.benchmarks.schemas import (
    BenchmarkSetupStatus,
    BenchmarkSummaryResponse,
    BenchmarkCatalogStatus,
    RunWorkloadRequest,
    RunWorkloadResponse
)
from app.benchmarks.tpch_manager import TPCHManager, get_tpch_base_dir
from app.benchmarks.dataset_loader import DatasetLoader
from app.benchmarks.dataset_validator import DatasetValidator
from app.benchmarks.benchmark_runner import BenchmarkRunner

logger = logging.getLogger("queryguard.benchmarks.service")


class BenchmarkService:
    def __init__(self):
        self.base_dir = get_tpch_base_dir()
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "processed"
        self.queries_dir = self.base_dir / "queries"
        self.schema_file = self.base_dir / "schema" / "tpch_ddl.sql"
        self.loader = DatasetLoader()
        self.runner = BenchmarkRunner()

    def get_catalog(self) -> BenchmarkCatalogStatus:
        """Returns catalog of all supported benchmark workloads and their current state."""
        counts = self.loader.verify_table_counts()
        total_tpch_rows = sum(counts.values())
        tpch_sf01_installed = total_tpch_rows > 1000

        catalog = [
            {
                "id": "ecommerce_synthetic",
                "name": "Synthetic E-Commerce (Default)",
                "category": "OLTP / Hybrid",
                "scale": "Base (10k rows)",
                "status": "ACTIVE",
                "installed": True,
                "table_count": 5,
                "disk_size_mb": 15.0,
                "description": "Transactional e-commerce schema with deliberate index omissions for bottleneck detection.",
                "hardware_warning": None
            },
            {
                "id": "tpch_sf01",
                "name": "TPC-H Decision Support (SF 0.1)",
                "category": "OLAP / Analytics",
                "scale": "SF 0.1 (~100MB)",
                "status": "READY" if tpch_sf01_installed else "AVAILABLE",
                "installed": tpch_sf01_installed,
                "table_count": 8,
                "disk_size_mb": 110.0,
                "description": "Standard TPC-H analytical workload with 8 tables and complex decision-support joins.",
                "hardware_warning": None
            },
            {
                "id": "tpch_sf1",
                "name": "TPC-H Decision Support (SF 1.0)",
                "category": "OLAP / Analytics",
                "scale": "SF 1.0 (~1GB)",
                "status": "AVAILABLE",
                "installed": False,
                "table_count": 8,
                "disk_size_mb": 1100.0,
                "description": "Full scale 1.0 TPC-H dataset with 6M line items for intensive join & scan benchmarking.",
                "hardware_warning": "Warning: SF 1.0 requires at least 4 GB RAM and ~1.2 GB disk. Recommended only on high-spec systems."
            },
            {
                "id": "job_imdb",
                "name": "Join Order Benchmark (JOB / IMDb)",
                "category": "Complex Multi-Table Joins",
                "scale": "Sample (~350MB)",
                "status": "SCAFFOLDED",
                "installed": False,
                "table_count": 21,
                "disk_size_mb": 350.0,
                "description": "Real-world IMDb movie schema designed to stress-test query optimizers and cardinalities.",
                "hardware_warning": "Scaffolded benchmark: schema definition ready for future extension."
            }
        ]

        active_id = "tpch_sf01" if tpch_sf01_installed else "ecommerce_synthetic"

        return BenchmarkCatalogStatus(
            benchmarks=catalog,
            active_dataset=active_id,
            environment="Local Sandbox / Synthetic Benchmark (Read-Only)"
        )

    async def start_setup(self, scale_factor: float = 0.1, force_rebuild: bool = False) -> BenchmarkSetupStatus:
        """Triggers background data generation and validation."""
        return await TPCHManager.start_setup(scale_factor=scale_factor, force_rebuild=force_rebuild)

    def get_setup_status(self) -> BenchmarkSetupStatus:
        """Retrieves real-time setup progress."""
        return TPCHManager.get_status()

    async def load_into_database(self) -> Dict[str, Any]:
        """Loads cleaned processed .tbl files into workload-postgres."""
        TPCHManager.set_status("LOADING", 90, "Applying schema and loading tables", "Executing COPY into workload-postgres")

        def _do_load():
            # Step 1: Apply DDL if needed
            self.loader.apply_schema(self.schema_file)
            # Step 2: Load processed files
            return self.loader.load_processed_data(self.processed_dir)

        try:
            result = await asyncio.to_thread(_do_load)
            TPCHManager.set_status("READY", 100, "Ready", "TPC-H dataset loaded and indexed in workload-postgres successfully.")
            return result
        except Exception as e:
            logger.error("Failed to load TPC-H dataset into database: %s", str(e))
            TPCHManager.set_status("FAILED", 90, "Load Error", str(e), error=str(e))
            raise

    def get_summary(self) -> BenchmarkSummaryResponse:
        """Returns comprehensive summary of TPC-H dataset state."""
        counts = self.loader.verify_table_counts()
        total_rows = sum(counts.values())
        is_installed = total_rows > 1000

        # Estimate disk size
        disk_size_mb = 0.0
        if self.processed_dir.exists():
            disk_size_mb = sum(f.stat().st_size for f in self.processed_dir.glob("*.tbl")) / (1024 * 1024)

        available_queries = self.runner.get_available_queries(self.queries_dir)

        return BenchmarkSummaryResponse(
            dataset="tpch",
            scale_factor=0.1,
            is_installed=is_installed,
            status="READY" if is_installed else "NOT_LOADED",
            table_count=len(counts),
            estimated_rows=total_rows,
            table_rows=counts,
            approved_queries_count=len(available_queries),
            disk_size_estimate_mb=round(disk_size_mb, 2),
            privacy_statement="Benchmark data resides strictly in local workload-postgres. QueryGuard stores only sanitized metadata."
        )

    async def run_workload(self, request: RunWorkloadRequest) -> RunWorkloadResponse:
        """Executes approved queries to warm up pg_stat_statements."""
        job_id = f"tpch-run-{uuid.uuid4().hex[:8]}"
        t0 = time.time()

        def _execute():
            return self.runner.run_workload(self.queries_dir, iterations=request.iterations)

        result = await asyncio.to_thread(_execute)
        elapsed_ms = round((time.time() - t0) * 1000.0, 2)

        return RunWorkloadResponse(
            job_id=job_id,
            status="COMPLETED" if result["success"] else "FAILED",
            queries_executed=result.get("total_executed", 0),
            total_iterations=request.iterations,
            duration_ms=elapsed_ms,
            message=f"Executed {result.get('successful', 0)} queries successfully. pg_stat_statements updated.",
            telemetry_collected=True
        )

    def reset_dataset(self) -> Dict[str, Any]:
        """Safely resets TPC-H tables in workload database."""
        result = self.loader.reset_schema()
        TPCHManager.set_status("IDLE", 0, "Idle", "TPC-H dataset reset.")
        return result

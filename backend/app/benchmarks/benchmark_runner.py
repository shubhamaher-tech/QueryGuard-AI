"""
TPC-H Benchmark Workload Runner
Executes approved TPC-H query templates against workload-postgres.
Runs in strictly READ-ONLY transactions with a 10s statement timeout.
Ensures zero data leakage: row data is consumed and discarded; only timings and counts are recorded.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text

from app.config import settings

logger = logging.getLogger("queryguard.benchmarks.benchmark_runner")


class BenchmarkRunner:
    def __init__(self, ro_db_url: Optional[str] = None):
        self.db_url = ro_db_url or getattr(
            settings,
            "WORKLOAD_DATABASE_URL",
            os.getenv("WORKLOAD_DATABASE_URL", "postgresql+psycopg2://workload_ro:workload_ro_pass@localhost:5433/workload_db")
        )
        self.engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            connect_args={"options": "-c default_transaction_read_only=on"}
        )

    def get_available_queries(self, queries_dir: Path) -> List[Dict[str, Any]]:
        """Scans queries directory and returns metadata about approved query templates."""
        if not queries_dir.exists():
            return []

        queries = []
        for q_file in sorted(queries_dir.glob("*.sql")):
            content = q_file.read_text(encoding="utf-8")
            # Extract header description if present
            lines = content.strip().splitlines()
            description = lines[0].replace("--", "").strip() if lines and lines[0].startswith("--") else q_file.stem
            queries.append({
                "id": q_file.stem,
                "filename": q_file.name,
                "description": description,
                "size_bytes": len(content)
            })
        return queries

    def run_query(self, query_sql: str, timeout_ms: int = 10000) -> Dict[str, Any]:
        """
        Executes a single benchmark query template within strict read-only parameters.
        Row records are iterated and counted, but NEVER returned or logged.
        """
        start_time = time.time()
        row_count = 0

        with self.engine.connect() as conn:
            # Enforce read-only and statement timeout
            conn.execute(text("SET TRANSACTION READ ONLY;"))
            conn.execute(text(f"SET statement_timeout = {timeout_ms};"))
            # Ensure search path includes tpch_sf01
            conn.execute(text("SET search_path TO tpch_sf01, public;"))

            result = conn.execute(text(query_sql))
            # Safely count rows without retaining row values
            for _ in result:
                row_count += 1

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)
        return {
            "success": True,
            "latency_ms": elapsed_ms,
            "rows_affected": row_count
        }

    def run_workload(self, queries_dir: Path, iterations: int = 1) -> Dict[str, Any]:
        """
        Executes all approved TPC-H queries sequentially for the specified number of iterations.
        Stimulates pg_stat_statements in workload-postgres.
        """
        available = self.get_available_queries(queries_dir)
        if not available:
            return {
                "success": False,
                "error": "No approved query templates found in queries directory",
                "queries_executed": 0
            }

        start_total = time.time()
        results = []
        total_queries = 0
        successful_queries = 0

        for it in range(iterations):
            for q_meta in available:
                q_file = queries_dir / q_meta["filename"]
                q_sql = q_file.read_text(encoding="utf-8")
                total_queries += 1

                try:
                    res = self.run_query(q_sql)
                    successful_queries += 1
                    results.append({
                        "query_id": q_meta["id"],
                        "iteration": it + 1,
                        "latency_ms": res["latency_ms"],
                        "rows_affected": res["rows_affected"],
                        "status": "COMPLETED"
                    })
                except Exception as e:
                    logger.warning(f"Error executing benchmark query {q_meta['id']}: {str(e)}")
                    results.append({
                        "query_id": q_meta["id"],
                        "iteration": it + 1,
                        "latency_ms": 0.0,
                        "rows_affected": 0,
                        "status": "FAILED",
                        "error_type": type(e).__name__
                    })

        total_elapsed_ms = round((time.time() - start_total) * 1000.0, 2)
        avg_latency = round(
            sum(r["latency_ms"] for r in results if r["status"] == "COMPLETED") / max(1, successful_queries), 2
        )

        return {
            "success": successful_queries > 0,
            "total_executed": total_queries,
            "successful": successful_queries,
            "failed": total_queries - successful_queries,
            "total_elapsed_ms": total_elapsed_ms,
            "average_latency_ms": avg_latency,
            "query_results": results
        }

"""
TPC-H Dataset Loader
Loads validated and cleaned TPC-H dataset files into workload-postgres.
Uses administrative connection to execute DDL, COPY data, and ANALYZE.
Ensures zero data exposure to application DB or logs.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import sqlalchemy
from sqlalchemy import create_engine, text

from app.config import settings

logger = logging.getLogger("queryguard.benchmarks.dataset_loader")

TABLE_ORDER = [
    "region",
    "nation",
    "part",
    "supplier",
    "partsupp",
    "customer",
    "orders",
    "lineitem"
]


class DatasetLoader:
    def __init__(self, admin_db_url: Optional[str] = None):
        self.db_url = admin_db_url or getattr(
            settings, 
            "WORKLOAD_ADMIN_DATABASE_URL", 
            os.getenv("WORKLOAD_ADMIN_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/workload_db")
        )
        # Ensure we have admin credentials; if default URL uses workload_ro, adapt to postgres user
        if "workload_ro" in self.db_url:
            self.db_url = self.db_url.replace("workload_ro:workload_ro_pass", "postgres:postgres")

    def _get_engine(self):
        return create_engine(self.db_url, pool_pre_ping=True)

    def apply_schema(self, ddl_path: Path) -> Dict[str, Any]:
        """Applies DDL schema file to workload database."""
        if not ddl_path.exists():
            raise FileNotFoundError(f"TPC-H DDL file not found at {ddl_path}")

        sql_content = ddl_path.read_text(encoding="utf-8")
        engine = self._get_engine()

        with engine.begin() as conn:
            # Execute statement by statement or full block
            conn.execute(text(sql_content))
            # Ensure permissions are granted to workload_ro
            conn.execute(text("GRANT USAGE ON SCHEMA tpch_sf01 TO workload_ro;"))
            conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA tpch_sf01 TO workload_ro;"))
            conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO workload_ro;"))

        return {"status": "SUCCESS", "message": "TPC-H schema applied successfully"}

    def load_processed_data(self, processed_dir: Path) -> Dict[str, Any]:
        """Loads cleaned .tbl files into tpch_sf01 schema tables using COPY."""
        if not processed_dir.exists():
            raise FileNotFoundError(f"Processed directory not found: {processed_dir}")

        engine = self._get_engine()
        results = {}
        start_time = time.time()

        raw_conn = engine.raw_connection()
        try:
            cursor = raw_conn.cursor()
            # Set search path to tpch_sf01
            cursor.execute("SET search_path TO tpch_sf01, public;")

            for table_name in TABLE_ORDER:
                tbl_file = processed_dir / f"{table_name}.tbl"
                if not tbl_file.exists():
                    logger.warning(f"File {tbl_file} missing for table {table_name}")
                    continue

                t0 = time.time()
                # Use copy_expert with CSV format and pipe delimiter
                copy_sql = f"COPY tpch_sf01.{table_name} FROM STDIN WITH (FORMAT csv, DELIMITER '|');"
                with open(tbl_file, "r", encoding="utf-8") as f:
                    cursor.copy_expert(copy_sql, f)

                t1 = time.time()
                cursor.execute(f"SELECT count(*) FROM tpch_sf01.{table_name};")
                count = cursor.fetchone()[0]
                results[table_name] = {
                    "rows_loaded": count,
                    "elapsed_sec": round(t1 - t0, 3)
                }
                logger.info(f"Loaded {count} rows into tpch_sf01.{table_name} in {round(t1 - t0, 3)}s")

            # Commit transaction
            raw_conn.commit()

            # Run ANALYZE on loaded tables
            cursor.execute("ANALYZE tpch_sf01.region, tpch_sf01.nation, tpch_sf01.part, tpch_sf01.supplier, tpch_sf01.partsupp, tpch_sf01.customer, tpch_sf01.orders, tpch_sf01.lineitem;")
            raw_conn.commit()

        finally:
            raw_conn.close()

        total_elapsed = round(time.time() - start_time, 3)
        return {
            "status": "SUCCESS",
            "tables": results,
            "total_elapsed_sec": total_elapsed
        }

    def verify_table_counts(self) -> Dict[str, int]:
        """Returns row counts of all TPC-H tables in workload database."""
        engine = self._get_engine()
        counts = {}
        with engine.connect() as conn:
            for table_name in TABLE_ORDER:
                try:
                    res = conn.execute(text(f"SELECT count(*) FROM tpch_sf01.{table_name};"))
                    counts[table_name] = res.scalar() or 0
                except Exception:
                    counts[table_name] = 0
        return counts

    def reset_schema(self) -> Dict[str, Any]:
        """Truncates all TPC-H tables in tpch_sf01 schema."""
        engine = self._get_engine()
        with engine.begin() as conn:
            for table_name in reversed(TABLE_ORDER):
                try:
                    conn.execute(text(f"TRUNCATE TABLE tpch_sf01.{table_name} CASCADE;"))
                except Exception as e:
                    logger.debug(f"Reset error on {table_name}: {e}")
        return {"status": "SUCCESS", "message": "TPC-H tables truncated successfully"}

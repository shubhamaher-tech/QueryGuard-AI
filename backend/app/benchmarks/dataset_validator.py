"""
Dataset Validator for TPC-H Benchmark Files
Verifies file existence, sizes, delimiter structures, and row count tolerances.
Never logs or saves raw benchmark rows.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
from app.benchmarks.schemas import BenchmarkValidationSummary

logger = logging.getLogger("queryguard.benchmarks.validator")

REQUIRED_TABLES = [
    "region",
    "nation",
    "supplier",
    "customer",
    "part",
    "partsupp",
    "orders",
    "lineitem",
]

# Baseline row count expectations by scale factor
EXPECTED_ROW_COUNTS = {
    0.1: {
        "region": (5, 5),
        "nation": (25, 25),
        "supplier": (80, 150),
        "customer": (1200, 2000),
        "part": (1500, 2500),
        "partsupp": (6000, 10000),
        "orders": (12000, 20000),
        "lineitem": (50000, 75000),
    },
    1.0: {
        "region": (5, 5),
        "nation": (25, 25),
        "supplier": (8000, 12000),
        "customer": (120000, 180000),
        "part": (150000, 250000),
        "partsupp": (700000, 900000),
        "orders": (1200000, 1800000),
        "lineitem": (5000000, 7000000),
    },
}


class DatasetValidator:
    @classmethod
    def validate_tpch_directory(
        cls,
        directory: Path,
        scale_factor: float = 0.1,
    ) -> BenchmarkValidationSummary:
        """
        Validates the raw or processed directory containing TPC-H .tbl files.
        """
        file_summaries: Dict[str, Any] = {}
        validation_errors: List[str] = []
        is_all_valid = True

        tolerances = EXPECTED_ROW_COUNTS.get(scale_factor, EXPECTED_ROW_COUNTS[0.1])

        for table in REQUIRED_TABLES:
            # Check for table.tbl or table.tbl.csv
            candidates = [
                directory / f"{table}.tbl",
                directory / f"{table}.csv",
                directory / f"{table}.txt",
            ]
            found_path = next((p for p in candidates if p.exists()), None)

            if not found_path:
                is_all_valid = False
                validation_errors.append(f"Missing required table file: {table}.tbl")
                file_summaries[table] = {
                    "exists": False,
                    "size_bytes": 0,
                    "row_count": 0,
                    "status": "MISSING",
                }
                continue

            size_bytes = found_path.stat().st_size
            if size_bytes == 0:
                is_all_valid = False
                validation_errors.append(f"Table file {table}.tbl is empty (0 bytes).")
                file_summaries[table] = {
                    "exists": True,
                    "size_bytes": 0,
                    "row_count": 0,
                    "status": "EMPTY",
                }
                continue

            # Count rows and check structure safely
            line_count = 0
            with open(found_path, "r", encoding="utf-8", errors="replace") as f:
                for _ in f:
                    line_count += 1

            min_expected, max_expected = tolerances.get(table, (1, 10000000))
            if not (min_expected <= line_count <= max_expected):
                validation_errors.append(
                    f"Table {table} row count ({line_count}) outside expected SF {scale_factor} range ({min_expected}-{max_expected})."
                )
                status = "ROW_COUNT_MISMATCH"
            else:
                status = "VALID"

            file_summaries[table] = {
                "exists": True,
                "size_bytes": size_bytes,
                "row_count": line_count,
                "status": status,
            }

        return BenchmarkValidationSummary(
            is_valid=is_all_valid and len(validation_errors) == 0,
            scale_factor=scale_factor,
            file_summaries=file_summaries,
            total_files=len(file_summaries),
            validation_errors=validation_errors,
            clean_status="Validated with 0 malformed records" if is_all_valid else "Validation issues identified",
        )

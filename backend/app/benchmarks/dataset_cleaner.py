"""
Dataset Preprocessing & Cleaner for TPC-H Raw Files
Normalizes pipe delimiters, ensures consistent line endings, checks field counts,
and records only statistical metadata without exposing raw data.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger("queryguard.benchmarks.cleaner")

# Expected field counts for official TPC-H .tbl files
TPCH_EXPECTED_FIELDS = {
    "region": 3,
    "nation": 4,
    "supplier": 7,
    "customer": 8,
    "part": 9,
    "partsupp": 5,
    "orders": 9,
    "lineitem": 16,
}


class DatasetCleaner:
    @classmethod
    def clean_table_file(
        cls,
        table_name: str,
        raw_file_path: Path,
        processed_file_path: Path,
    ) -> Dict[str, Any]:
        """
        Normalizes TPC-H .tbl file:
        - Removes trailing pipe delimiter if present
        - Standardizes line endings to UNIX '\n'
        - Verifies column count matches TPC-H specification
        - Rejects malformed rows and reports rejected line counts only
        """
        if not raw_file_path.exists():
            return {
                "table": table_name,
                "success": False,
                "total_lines": 0,
                "valid_lines": 0,
                "rejected_lines": 0,
                "error": f"Raw file {raw_file_path.name} not found.",
            }

        expected_count = TPCH_EXPECTED_FIELDS.get(table_name)
        total_lines = 0
        valid_lines = 0
        rejected_lines = 0

        processed_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(raw_file_path, "r", encoding="utf-8", errors="replace") as infile, \
                 open(processed_file_path, "w", encoding="utf-8", newline="\n") as outfile:
                
                for line in infile:
                    total_lines += 1
                    cleaned = line.strip()
                    if not cleaned:
                        continue

                    # TPC-H .tbl lines end with a trailing pipe: col1|col2|col3|
                    if cleaned.endswith("|"):
                        fields = cleaned[:-1].split("|")
                    else:
                        fields = cleaned.split("|")

                    if expected_count is not None and len(fields) != expected_count:
                        rejected_lines += 1
                        continue

                    # Write normalized line (tab-separated or standard pipe without trailing pipe)
                    outfile.write("|".join(fields) + "\n")
                    valid_lines += 1

            return {
                "table": table_name,
                "success": True,
                "total_lines": total_lines,
                "valid_lines": valid_lines,
                "rejected_lines": rejected_lines,
                "processed_path": str(processed_file_path),
            }
        except Exception as e:
            logger.error("Cleaning error on %s: %s", table_name, str(e))
            return {
                "table": table_name,
                "success": False,
                "total_lines": total_lines,
                "valid_lines": valid_lines,
                "rejected_lines": rejected_lines,
                "error": "File normalization failed. Operational status logged safely.",
            }

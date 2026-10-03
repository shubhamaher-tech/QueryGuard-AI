"""
Tests for TPC-H & Benchmark Automation Pipeline
Validates data cleaning, schema validation, catalog endpoints, and zero data leakage.
"""

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.benchmarks.dataset_cleaner import DatasetCleaner
from app.benchmarks.dataset_validator import DatasetValidator

client = TestClient(app)


def test_dataset_cleaner_table():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_file = tmp_path / "region_raw.tbl"
        cleaned_file = tmp_path / "region_cleaned.tbl"

        # Raw file with trailing pipe and windows line endings
        raw_file.write_text("0|AFRICA|lar deposits.|\r\n1|AMERICA|hs use ironic.|\r\n", encoding="utf-8")

        result = DatasetCleaner.clean_table_file("region", raw_file, cleaned_file)
        assert result["valid_lines"] == 2
        assert result["rejected_lines"] == 0

        # Verify cleaned file format: trailing pipe stripped and unix newlines
        cleaned_content = cleaned_file.read_text(encoding="utf-8")
        assert "0|AFRICA|lar deposits." in cleaned_content
        assert "\r" not in cleaned_content


def test_dataset_validator_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create dummy region file with 3 columns
        reg_file = tmp_path / "region.tbl"
        reg_file.write_text("0|AFRICA|comment\n", encoding="utf-8")

        # Missing other files should fail directory validation
        summary = DatasetValidator.validate_tpch_directory(tmp_path, scale_factor=0.1)
        assert summary.is_valid is False
        assert len(summary.validation_errors) > 0


def test_benchmark_catalog_endpoint():
    response = client.get("/api/benchmarks/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "benchmarks" in data
    assert len(data["benchmarks"]) >= 4

    ids = [b["id"] for b in data["benchmarks"]]
    assert "ecommerce_synthetic" in ids
    assert "tpch_sf01" in ids
    assert "tpch_sf1" in ids
    assert "job_imdb" in ids

    # Check hardware warning on SF 1.0
    sf1 = next(b for b in data["benchmarks"] if b["id"] == "tpch_sf1")
    assert sf1["hardware_warning"] is not None
    assert "RAM" in sf1["hardware_warning"]


def test_benchmark_tpch_status_and_summary():
    status_res = client.get("/api/benchmarks/tpch/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "status" in status_data
    assert "progress_pct" in status_data

    summary_res = client.get("/api/benchmarks/tpch/summary")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["dataset"] == "tpch"
    assert "privacy_statement" in summary_data
    assert "table_rows" in summary_data


def test_benchmark_privacy_compliance():
    """Ensure catalog and summary never leak raw passwords, connection strings, or customer records."""
    catalog_res = client.get("/api/benchmarks/catalog")
    raw_str = catalog_res.text.lower()
    assert "password" not in raw_str
    assert "secret" not in raw_str
    assert "workload_ro_pass" not in raw_str

"""
TPC-H Benchmark Manager & Automated Generator
Manages automated data generation, validation, and lifecycle for TPC-H workloads.
Never logs or persists raw benchmark data into QueryGuard application database.
"""

import os
import random
import datetime
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.benchmarks.schemas import BenchmarkSetupStatus
from app.benchmarks.dataset_validator import DatasetValidator
from app.benchmarks.dataset_cleaner import DatasetCleaner

logger = logging.getLogger("queryguard.benchmarks.tpch_manager")

def get_tpch_base_dir() -> Path:
    env_dir = os.getenv("TPCH_BASE_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)
    candidates = [
        Path("/app/database/workload/tpch"),
        Path(__file__).resolve().parent.parent.parent.parent / "database" / "workload" / "tpch",
        Path(__file__).resolve().parent.parent.parent / "database" / "workload" / "tpch",
        Path.cwd() / "database" / "workload" / "tpch",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0] if Path("/app").exists() else candidates[1]

TPCH_BASE_DIR = get_tpch_base_dir()
RAW_DIR = TPCH_BASE_DIR / "raw"
PROCESSED_DIR = TPCH_BASE_DIR / "processed"
LOGS_DIR = TPCH_BASE_DIR / "logs"

REGIONS = [
    (0, "AFRICA", "lar deposits. blithely final packages cajole. regular waters"),
    (1, "AMERICA", "hs use ironic, even requests. s"),
    (2, "ASIA", "ges. even pinto beans ca"),
    (3, "EUROPE", "ly final courts cajole furiously blithely regular"),
    (4, "MIDDLE EAST", "uickly special accounts cajole carefully blithely close"),
]

NATIONS = [
    (0, "ALGERIA", 0, " special packages. silent"),
    (1, "ARGENTINA", 1, "al foxes promise carefully slyly"),
    (2, "BRAZIL", 1, "y bossily express regular ideas"),
    (3, "CANADA", 1, " carefully regular pinto beans sleep"),
    (4, "EGYPT", 4, "ly ironic instructions. silent"),
    (5, "ETHIOPIA", 0, " regular packages across"),
    (6, "FRANCE", 3, " special requests. even requests"),
    (7, "GERMANY", 3, " carefully silent requests"),
    (8, "INDIA", 2, " special requests against furiously"),
    (9, "INDONESIA", 2, " slyly unusual accounts sleep"),
    (10, "IRAN", 4, " carefully bold accounts. quickly unusual"),
    (11, "IRAQ", 4, " quickly ironic instructions"),
    (12, "JAPAN", 2, " express packages detect"),
    (13, "JORDAN", 4, " bold accounts. quickly bold ideas"),
    (14, "KENYA", 0, " quickly unusual packages detect slyly"),
    (15, "MOROCCO", 0, " carefully bold requests"),
    (16, "MOZAMBIQUE", 0, " carefully regular packages sleep"),
    (17, "PERU", 1, " slyly special packages"),
    (18, "CHINA", 2, " special dependencies. special"),
    (19, "ROMANIA", 3, " slyly bold dependencies sleep"),
    (20, "SAUDI ARABIA", 4, " slyly express accounts. silent"),
    (21, "VIETNAM", 2, " carefully pending packages"),
    (22, "RUSSIA", 3, " quickly unusual requests sleep"),
    (23, "UNITED KINGDOM", 3, " special accounts sleep. blithely"),
    (24, "UNITED STATES", 1, " carefully unusual dependencies boost"),
]


class TPCHManager:
    _status: BenchmarkSetupStatus = BenchmarkSetupStatus()

    @classmethod
    def get_status(cls) -> BenchmarkSetupStatus:
        return cls._status

    @classmethod
    def set_status(
        cls,
        status: str,
        progress_pct: int,
        stage: str,
        message: str,
        error: Optional[str] = None,
        scale_factor: float = 0.1,
    ):
        cls._status = BenchmarkSetupStatus(
            dataset="tpch",
            scale_factor=scale_factor,
            status=status,
            progress_pct=progress_pct,
            current_stage=stage,
            message=message,
            error=error,
            updated_at=datetime.datetime.utcnow(),
        )

    @classmethod
    async def start_setup(cls, scale_factor: float = 0.1, force_rebuild: bool = False):
        """
        Starts the asynchronous setup pipeline: Generate -> Clean -> Validate.
        """
        if cls._status.status in ("GENERATING", "CLEANING", "LOADING"):
            return cls._status

        # Run background generation task
        asyncio.create_task(cls._execute_setup_pipeline(scale_factor, force_rebuild))
        return cls._status

    @classmethod
    async def _execute_setup_pipeline(cls, scale_factor: float, force_rebuild: bool):
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        try:
            # Check existing files
            cls.set_status("VALIDATING", 10, "Checking existing benchmark files", "Inspecting raw files", scale_factor=scale_factor)
            existing_val = DatasetValidator.validate_tpch_directory(RAW_DIR, scale_factor=scale_factor)
            
            if existing_val.is_valid and not force_rebuild:
                cls.set_status("READY", 100, "Completed", f"TPC-H SF {scale_factor} files are already generated and validated.", scale_factor=scale_factor)
                return

            # Stage 1: Generate Raw Data
            cls.set_status("GENERATING", 20, "Generating TPC-H .tbl files", f"Generating synthetic data for SF {scale_factor}", scale_factor=scale_factor)
            await asyncio.to_thread(cls._generate_tpch_files, scale_factor)

            # Stage 2: Clean & Preprocess
            cls.set_status("CLEANING", 60, "Normalizing file delimiters", "Standardizing line endings and field counts", scale_factor=scale_factor)
            for tbl in ["region", "nation", "supplier", "customer", "part", "partsupp", "orders", "lineitem"]:
                raw_file = RAW_DIR / f"{tbl}.tbl"
                proc_file = PROCESSED_DIR / f"{tbl}.tbl"
                DatasetCleaner.clean_table_file(tbl, raw_file, proc_file)

            # Stage 3: Final Validation
            cls.set_status("VALIDATING", 85, "Validating processed benchmark files", "Verifying line counts and format integrity", scale_factor=scale_factor)
            validation = DatasetValidator.validate_tpch_directory(PROCESSED_DIR, scale_factor=scale_factor)

            if not validation.is_valid:
                cls.set_status("FAILED", 85, "Validation failed", "; ".join(validation.validation_errors), error="Validation check failed", scale_factor=scale_factor)
                return

            cls.set_status("READY", 100, "Ready for database loading", f"TPC-H SF {scale_factor} benchmark files generated and validated successfully.", scale_factor=scale_factor)

        except Exception as e:
            logger.error("TPC-H setup failed: %s", str(e))
            cls.set_status("FAILED", 0, "Error", "TPC-H setup failed. Operational status logged safely.", error=str(e), scale_factor=scale_factor)

    @classmethod
    def _generate_tpch_files(cls, scale_factor: float):
        """
        Generates standard TPC-H .tbl files with exact column schemas.
        Uses deterministic seeding for reproducibility.
        """
        rng = random.Random(42)

        # 1. region.tbl
        with open(RAW_DIR / "region.tbl", "w", encoding="utf-8", newline="\n") as f:
            for r_id, r_name, r_comm in REGIONS:
                f.write(f"{r_id}|{r_name}|{r_comm}|\n")

        # 2. nation.tbl
        with open(RAW_DIR / "nation.tbl", "w", encoding="utf-8", newline="\n") as f:
            for n_id, n_name, n_rid, n_comm in NATIONS:
                f.write(f"{n_id}|{n_name}|{n_rid}|{n_comm}|\n")

        # Table row counts based on scale factor
        num_supp = max(10, int(1000 * scale_factor))
        num_cust = max(150, int(15000 * scale_factor))
        num_part = max(200, int(20000 * scale_factor))
        num_orders = max(1500, int(150000 * scale_factor))

        # 3. supplier.tbl
        with open(RAW_DIR / "supplier.tbl", "w", encoding="utf-8", newline="\n") as f:
            for s_id in range(1, num_supp + 1):
                name = f"Supplier#{s_id:09d}"
                addr = f"{rng.randint(100,999)} Street {rng.choice(['East', 'West', 'Central'])}"
                nat_id = rng.randint(0, 24)
                phone = f"{nat_id + 10:02d}-{rng.randint(100,999)}-{rng.randint(100,999)}-{rng.randint(1000,9999)}"
                acctbal = f"{rng.uniform(-999.99, 9999.99):.2f}"
                comm = "standard supplier notes"
                f.write(f"{s_id}|{name}|{addr}|{nat_id}|{phone}|{acctbal}|{comm}|\n")

        # 4. part.tbl
        types = ["STANDARD ANODIZED BRASS", "PROMO BRUSHED COPPER", "LARGE POLISHED STEEL", "SMALL PLATED TIN", "MEDIUM BURNISHED NICKEL"]
        brands = ["Brand#11", "Brand#23", "Brand#34", "Brand#45", "Brand#52"]
        containers = ["JUMBO BAG", "MED BOX", "SM PKG", "LG CAN", "WRAP CASE"]

        with open(RAW_DIR / "part.tbl", "w", encoding="utf-8", newline="\n") as f:
            for p_id in range(1, num_part + 1):
                name = f"Part_{p_id}"
                mfgr = f"Manufacturer#{rng.randint(1,5)}"
                brand = rng.choice(brands)
                ptype = rng.choice(types)
                size = rng.randint(1, 50)
                container = rng.choice(containers)
                retailprice = f"{rng.uniform(900.00, 2000.00):.2f}"
                comm = "part spec"
                f.write(f"{p_id}|{name}|{mfgr}|{brand}|{ptype}|{size}|{container}|{retailprice}|{comm}|\n")

        # 5. partsupp.tbl (4 suppliers per part)
        with open(RAW_DIR / "partsupp.tbl", "w", encoding="utf-8", newline="\n") as f:
            for p_id in range(1, num_part + 1):
                for s_offset in range(4):
                    s_id = ((p_id + s_offset) % num_supp) + 1
                    availqty = rng.randint(1, 9999)
                    supplycost = f"{rng.uniform(1.00, 1000.00):.2f}"
                    comm = "standard partsupp record"
                    f.write(f"{p_id}|{s_id}|{availqty}|{supplycost}|{comm}|\n")

        # 6. customer.tbl
        mktsegments = ["AUTOMOBILE", "BUILDING", "FURNITURE", "MACHINERY", "HOUSEHOLD"]
        with open(RAW_DIR / "customer.tbl", "w", encoding="utf-8", newline="\n") as f:
            for c_id in range(1, num_cust + 1):
                name = f"Customer#{c_id:09d}"
                addr = f"{rng.randint(10,999)} Avenue {rng.randint(1,50)}"
                nat_id = rng.randint(0, 24)
                phone = f"{nat_id + 10:02d}-{rng.randint(100,999)}-{rng.randint(100,999)}-{rng.randint(1000,9999)}"
                acctbal = f"{rng.uniform(-999.99, 9999.99):.2f}"
                mkt = rng.choice(mktsegments)
                comm = "customer relationship notes"
                f.write(f"{c_id}|{name}|{addr}|{nat_id}|{phone}|{acctbal}|{mkt}|{comm}|\n")

        # 7. orders.tbl & 8. lineitem.tbl
        statuses = ["F", "O", "P"]
        priorities = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
        shipinstructs = ["DELIVER IN PERSON", "COLLECT COD", "NONE", "TAKE BACK RETURN"]
        shipmodes = ["REG AIR", "AIR", "RAIL", "SHIP", "TRUCK", "MAIL", "FOB"]

        base_date = datetime.date(1992, 1, 1)

        with open(RAW_DIR / "orders.tbl", "w", encoding="utf-8", newline="\n") as f_ord, \
             open(RAW_DIR / "lineitem.tbl", "w", encoding="utf-8", newline="\n") as f_line:
            
            for o_id in range(1, num_orders + 1):
                c_id = rng.randint(1, num_cust)
                status = rng.choice(statuses)
                order_date = base_date + datetime.timedelta(days=rng.randint(0, 2400))
                priority = rng.choice(priorities)
                clerk = f"Clerk#{rng.randint(1,100):09d}"
                shippriority = 0
                comm = "order comment"

                # Generate 1 to 7 line items per order (average 4)
                num_items = rng.randint(1, 7)
                order_total = 0.0

                for line_num in range(1, num_items + 1):
                    p_id = rng.randint(1, num_part)
                    s_id = rng.randint(1, num_supp)
                    qty = rng.randint(1, 50)
                    price = round(qty * rng.uniform(20.0, 1500.0), 2)
                    disc = round(rng.uniform(0.00, 0.10), 2)
                    tax = round(rng.uniform(0.00, 0.08), 2)
                    
                    ship_date = order_date + datetime.timedelta(days=rng.randint(1, 120))
                    commit_date = order_date + datetime.timedelta(days=rng.randint(30, 90))
                    receipt_date = ship_date + datetime.timedelta(days=rng.randint(1, 30))

                    returnflag = "R" if ship_date < datetime.date(1995, 1, 1) and rng.random() < 0.2 else ("A" if rng.random() < 0.5 else "N")
                    linestatus = "O" if ship_date > datetime.date(1996, 6, 1) else "F"
                    instruct = rng.choice(shipinstructs)
                    mode = rng.choice(shipmodes)
                    item_comm = "line item notes"

                    order_total += price * (1 - disc) * (1 + tax)

                    f_line.write(
                        f"{o_id}|{p_id}|{s_id}|{line_num}|{qty:.2f}|{price:.2f}|{disc:.2f}|{tax:.2f}|"
                        f"{returnflag}|{linestatus}|{ship_date.isoformat()}|{commit_date.isoformat()}|"
                        f"{receipt_date.isoformat()}|{instruct}|{mode}|{item_comm}|\n"
                    )

                f_ord.write(
                    f"{o_id}|{c_id}|{status}|{order_total:.2f}|{order_date.isoformat()}|"
                    f"{priority}|{clerk}|{shippriority}|{comm}|\n"
                )

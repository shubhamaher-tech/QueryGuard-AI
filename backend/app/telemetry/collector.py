"""
Telemetry Collector for QueryGuard AI

Connects strictly to the workload PostgreSQL database using read-only credentials,
reads allow-listed aggregate statistics from pg_stat_statements, and collects
safe EXPLAIN (FORMAT JSON) execution plans.

Security Boundaries:
- Read-only user connection (workload_ro).
- Only executes EXPLAIN (FORMAT JSON) on allow-listed SELECT benchmark queries.
- Never executes EXPLAIN ANALYZE.
- Never collects raw query result rows.
- Never sends raw telemetry outside local network.
- Never logs raw SQL statements.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text

from app.config import settings

logger = logging.getLogger("queryguard.telemetry.collector")

# Allow-list criteria: Must be a read-only SELECT targeting synthetic benchmark tables
ALLOW_LISTED_TABLE_KEYWORDS = [
    "transactions", "customers", "products", "regions", "order_items",
    "tpch_lineitem", "tpch_orders", "tpch_customer", "tpch_part", "tpch_partsupp",
    "tpch_supplier", "tpch_nation", "tpch_region",
]
DISALLOWED_PATTERNS = [
    "pg_stat_statements",
    "pg_catalog",
    "information_schema",
    "hypopg",
    "explain",
    "pg_class",
    "pg_extension",
    "insert ",
    "update ",
    "delete ",
    "drop ",
    "alter ",
    "create ",
    "truncate ",
    "grant ",
    "revoke ",
    "set ",
    "do $$",
]


class WorkloadTelemetryCollector:
    """
    Safely extracts execution plan metadata and aggregate metrics from workload-postgres.
    """

    @classmethod
    def get_workload_engine(cls):
        url = settings.WORKLOAD_DATABASE_URL
        try:
            engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            return engine
        except Exception as e:
            logger.info("Workload PostgreSQL not reachable directly (%s). Using fallback benchmark generator.", str(e))
            return None

    @classmethod
    def collect_raw_metrics(cls) -> List[Dict[str, Any]]:
        """
        Queries pg_stat_statements on workload-postgres for allow-listed benchmark queries
        and runs EXPLAIN (FORMAT JSON).

        When the workload database is reachable, ONLY live statistics are returned.
        If no benchmark statements have been recorded yet, a short burst of real
        synthetic workload traffic is executed first so pg_stat_statements has data.
        The hardcoded fallback is used only when the workload database is unreachable.
        """
        engine = cls.get_workload_engine()

        if engine is not None:
            live_results = cls._collect_from_live_postgres(engine)
            if live_results:
                return live_results
            logger.info("No benchmark statements in pg_stat_statements yet. Generating live workload traffic.")
            try:
                from app.live.traffic import WorkloadTrafficGenerator
                WorkloadTrafficGenerator.run_burst(engine=engine)
            except Exception as ex:
                logger.warning("Workload traffic generation failed: %s", str(ex))
            return cls._collect_from_live_postgres(engine)
        return cls._generate_fallback_benchmark_telemetry()

    @classmethod
    def _collect_from_live_postgres(cls, engine) -> List[Dict[str, Any]]:
        """
        Reads from live pg_stat_statements on workload-postgres.
        """
        results: List[Dict[str, Any]] = []

        query_sql = text("""
            SELECT 
                queryid,
                calls,
                total_exec_time,
                mean_exec_time,
                min_exec_time,
                max_exec_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                temp_blks_read,
                temp_blks_written,
                query
            FROM pg_stat_statements
            WHERE query IS NOT NULL
              AND calls > 0
            ORDER BY mean_exec_time DESC
            LIMIT 200;
        """)

        with engine.connect() as conn:
            rows = conn.execute(query_sql).fetchall()
            conn.commit()

            for row in rows:
                r_dict = dict(row._mapping)
                raw_sql = (r_dict.get("query") or "").strip()
                sql_lower = raw_sql.lower()

                # Safety Verification: Must be SELECT, must not contain disallowed terms
                if not sql_lower.startswith("select"):
                    continue
                if any(bad in sql_lower for bad in DISALLOWED_PATTERNS):
                    continue
                if not any(tbl in sql_lower for tbl in ALLOW_LISTED_TABLE_KEYWORDS):
                    continue

                # Collect EXPLAIN (FORMAT JSON) safely without ANALYZE.
                # pg_stat_statements normalizes literals to $1, $2 ... -> GENERIC_PLAN (PG16+)
                explain_json = None
                options = "FORMAT JSON, GENERIC_PLAN" if "$" in raw_sql else "FORMAT JSON"
                try:
                    with conn.begin():
                        conn.execute(text("SET TRANSACTION READ ONLY"))
                        conn.execute(text("SET LOCAL statement_timeout = '5000ms'"))
                        explain_json = conn.execute(
                            text(f"EXPLAIN ({options}) {raw_sql}".replace(":", "\\:"))
                        ).scalar()
                except Exception as ex:
                    logger.debug("Explain collection failed for queryid %s: %s", r_dict.get("queryid"), str(ex))
                    continue

                if explain_json:
                    results.append({
                        "queryid": str(r_dict.get("queryid")),
                        "calls": int(r_dict.get("calls", 1)),
                        "total_exec_time": float(r_dict.get("total_exec_time", 0.0)),
                        "mean_exec_time": float(r_dict.get("mean_exec_time", 0.0)),
                        "min_exec_time": float(r_dict.get("min_exec_time", 0.0)),
                        "max_exec_time": float(r_dict.get("max_exec_time", 0.0)),
                        "rows": int(r_dict.get("rows", 0)),
                        "shared_blks_hit": int(r_dict.get("shared_blks_hit", 0)),
                        "shared_blks_read": int(r_dict.get("shared_blks_read", 0)),
                        "temp_blks_read": int(r_dict.get("temp_blks_read", 0)),
                        "temp_blks_written": int(r_dict.get("temp_blks_written", 0)),
                        "raw_sql": raw_sql,
                        "explain_json": explain_json,
                    })
                if len(results) >= 25:
                    break

        return results

    @classmethod
    def _generate_fallback_benchmark_telemetry(cls) -> List[Dict[str, Any]]:
        """
        Fallback generator providing realistic synthetic benchmark query telemetry
        when running outside Docker network (e.g. local unit tests or disconnected mode).
        Ensures local unit tests and development are 100% runnable.
        """
        return [
            {
                "queryid": "948201847192841",
                "calls": 12,
                "total_exec_time": 18240.0,
                "mean_exec_time": 1520.0,
                "min_exec_time": 1410.0,
                "max_exec_time": 1780.0,
                "rows": 1,
                "shared_blks_hit": 450,
                "shared_blks_read": 14200,
                "temp_blks_read": 0,
                "temp_blks_written": 0,
                "raw_sql": (
                    "SELECT region_id, COUNT(*) AS total_tx_count, SUM(amount) AS total_amount "
                    "FROM transactions WHERE region_id = 5 AND transaction_date >= '2025-06-01' "
                    "GROUP BY region_id;"
                ),
                "explain_json": [
                    {
                        "Plan": {
                            "Node Type": "Aggregate",
                            "Strategy": "Hashed",
                            "Total Cost": 34500.0,
                            "Plan Rows": 1,
                            "Plans": [
                                {
                                    "Node Type": "Seq Scan",
                                    "Relation Name": "transactions",
                                    "Total Cost": 34200.0,
                                    "Plan Rows": 12500,
                                    "Filter": "(region_id = 5 AND transaction_date >= '2025-06-01')"
                                }
                            ]
                        }
                    }
                ],
            },
            {
                "queryid": "782019481029384",
                "calls": 8,
                "total_exec_time": 22800.0,
                "mean_exec_time": 2850.0,
                "min_exec_time": 2600.0,
                "max_exec_time": 3100.0,
                "rows": 50,
                "shared_blks_hit": 1820,
                "shared_blks_read": 29400,
                "temp_blks_read": 0,
                "temp_blks_written": 0,
                "raw_sql": (
                    "SELECT c.customer_code, r.region_code, p.product_code, SUM(oi.quantity * oi.unit_price) AS line_total "
                    "FROM transactions t JOIN regions r ON t.region_id = r.id "
                    "JOIN customers c ON t.customer_id = c.id "
                    "JOIN order_items oi ON oi.transaction_id = t.id "
                    "JOIN products p ON oi.product_id = p.id "
                    "WHERE r.id = 3 AND t.transaction_date >= '2025-03-01' "
                    "GROUP BY c.customer_code, r.region_code, p.product_code "
                    "ORDER BY line_total DESC LIMIT 50;"
                ),
                "explain_json": [
                    {
                        "Plan": {
                            "Node Type": "Limit",
                            "Total Cost": 78200.0,
                            "Plan Rows": 50,
                            "Plans": [
                                {
                                    "Node Type": "Sort",
                                    "Total Cost": 78200.0,
                                    "Plan Rows": 5000,
                                    "Plans": [
                                        {
                                            "Node Type": "Nested Loop",
                                            "Total Cost": 74500.0,
                                            "Plan Rows": 5000,
                                            "Plans": [
                                                {
                                                    "Node Type": "Seq Scan",
                                                    "Relation Name": "transactions",
                                                    "Total Cost": 34200.0,
                                                    "Plan Rows": 12500
                                                },
                                                {
                                                    "Node Type": "Index Scan",
                                                    "Relation Name": "order_items",
                                                    "Total Cost": 12.5,
                                                    "Plan Rows": 2
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ],
            },
            {
                "queryid": "591029482019485",
                "calls": 10,
                "total_exec_time": 36500.0,
                "mean_exec_time": 3650.0,
                "min_exec_time": 3400.0,
                "max_exec_time": 3950.0,
                "rows": 100,
                "shared_blks_hit": 1400,
                "shared_blks_read": 38200,
                "temp_blks_read": 4850,
                "temp_blks_written": 4850,
                "raw_sql": (
                    "SELECT customer_id, COUNT(id) AS tx_count, SUM(amount) AS total_spent "
                    "FROM transactions WHERE status = 'COMPLETED' "
                    "GROUP BY customer_id ORDER BY total_spent DESC LIMIT 100;"
                ),
                "explain_json": [
                    {
                        "Plan": {
                            "Node Type": "Limit",
                            "Total Cost": 89400.0,
                            "Plan Rows": 100,
                            "Plans": [
                                {
                                    "Node Type": "Sort",
                                    "Total Cost": 89400.0,
                                    "Plan Rows": 10000,
                                    "Sort Method": "external merge Disk",
                                    "Plans": [
                                        {
                                            "Node Type": "Seq Scan",
                                            "Relation Name": "transactions",
                                            "Total Cost": 41200.0,
                                            "Plan Rows": 200000
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ],
            },
        ]

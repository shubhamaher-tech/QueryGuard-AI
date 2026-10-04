"""
Seed data generator for QueryGuard AI

Populates initial database records with strictly anonymized query metadata:
- Tokenized identifiers: TBL_A12, TBL_B03, TBL_C99, COL_R01, COL_D02, etc.
- Masked literals: :INT, :DATE, :STR
- Realistic execution plans matching the three target slow-query scenarios.
- Pre-generated recommendations and XAI evidence packets.
- Initial audit logs.
"""

import datetime
from sqlalchemy.orm import Session
from app.models import User, QueryEvent, Recommendation, Simulation, Approval, AuditLog
from app.privacy import PRIVACY_STATEMENT


def seed_database(db: Session):
    # Always ensure employee login accounts are seeded and updated in PostgreSQL
    _seed_frontend_entities(db)
    
    # Check if general benchmark queries already seeded
    if db.query(QueryEvent).first():
        return

    now = datetime.datetime.utcnow()

    # 1. Users
    users = [
        User(
            id="DBA_ADMIN_01",
            username="lead_dba_alex",
            role="DBA",
            created_at=now - datetime.timedelta(days=30),
        ),
        User(
            id="ANALYST_02",
            username="perf_analyst_sarah",
            role="ANALYST",
            created_at=now - datetime.timedelta(days=20),
        ),
    ]
    db.add_all(users)

    # 2. Query Events
    # Scenario 2: Nested-loop join with sequential scan (Matches exact prompt plan structure)
    plan_qe_join = {
        "Plan": {
            "id": "node-agg-1",
            "node_type": "Aggregate",
            "Node Type": "Aggregate",
            "relation_name": None,
            "Relation Name": None,
            "startup_cost": 42100.0,
            "total_cost": 54200.0,
            "Total Cost": 54200.0,
            "plan_rows": 850,
            "actual_rows": 850,
            "actual_time_ms": 2850.0,
            "loops": 1,
            "Loops": 1,
            "is_bottleneck": False,
            "children": [
                {
                    "id": "node-nl-join-2",
                    "node_type": "Nested Loop Join",
                    "Node Type": "Nested Loop",
                    "relation_name": None,
                    "Relation Name": None,
                    "startup_cost": 210.0,
                    "total_cost": 51200.0,
                    "Total Cost": 51200.0,
                    "plan_rows": 125000,
                    "actual_rows": 98400,
                    "actual_time_ms": 2740.0,
                    "loops": 1,
                    "Loops": 1,
                    "is_bottleneck": True,
                    "bottleneck_reason": "High iteration multiplier without indexed inner join key",
                    "children": [
                        {
                            "id": "node-seq-scan-3",
                            "node_type": "Sequential Scan",
                            "Node Type": "Seq Scan",
                            "relation_name": "TBL_A12",
                            "Relation Name": "TBL_A12",
                            "startup_cost": 0.0,
                            "total_cost": 31500.0,
                            "Total Cost": 31500.0,
                            "plan_rows": 1450000,
                            "actual_rows": 1450000,
                            "actual_time_ms": 1920.0,
                            "loops": 1,
                            "Loops": 1,
                            "filter_expr": "(COL_D02 >= :DATE AND COL_R01 = :INT)",
                            "is_bottleneck": True,
                            "bottleneck_reason": "Full table heap scan across 1.45M tuples without composite index",
                            "children": []
                        },
                        {
                            "id": "node-idx-scan-4",
                            "node_type": "Index Scan",
                            "Node Type": "Index Scan",
                            "relation_name": "TBL_B03",
                            "Relation Name": "TBL_B03",
                            "index_name": "pk_tbl_b03",
                            "startup_cost": 0.42,
                            "total_cost": 12.5,
                            "Total Cost": 12.5,
                            "plan_rows": 1,
                            "actual_rows": 1,
                            "actual_time_ms": 0.82,
                            "loops": 98400,
                            "Loops": 98400,
                            "is_bottleneck": False,
                            "bottleneck_reason": "Repeated 98,400 times inside loop",
                            "children": []
                        }
                    ]
                }
            ]
        }
    }

    # Scenario 1: Sequential scan on high-volume anonymized table
    plan_qe_seq = {
        "Plan": {
            "id": "node-root-agg",
            "node_type": "Aggregate",
            "Node Type": "Aggregate",
            "relation_name": None,
            "startup_cost": 38400.0,
            "total_cost": 41200.0,
            "Total Cost": 41200.0,
            "plan_rows": 42,
            "actual_rows": 42,
            "actual_time_ms": 1420.5,
            "loops": 1,
            "Loops": 1,
            "is_bottleneck": False,
            "children": [
                {
                    "id": "node-seq-scan-root",
                    "node_type": "Sequential Scan",
                    "Node Type": "Seq Scan",
                    "relation_name": "TBL_A12",
                    "Relation Name": "TBL_A12",
                    "startup_cost": 0.0,
                    "total_cost": 39800.0,
                    "Total Cost": 39800.0,
                    "plan_rows": 1450000,
                    "actual_rows": 1450000,
                    "actual_time_ms": 1390.2,
                    "loops": 1,
                    "Loops": 1,
                    "filter_expr": "(COL_D02 >= :DATE AND COL_R01 = :INT)",
                    "is_bottleneck": True,
                    "bottleneck_reason": "Unindexed sequential scan traversing 1.45M tuples (98% of query execution time)",
                    "children": []
                }
            ]
        }
    }

    # Scenario 3: Expensive sort / external merge spill
    plan_qe_sort = {
        "Plan": {
            "id": "node-sort-root",
            "node_type": "Sort",
            "Node Type": "Sort",
            "relation_name": "TBL_C99",
            "Relation Name": "TBL_C99",
            "startup_cost": 84200.0,
            "total_cost": 89400.0,
            "Total Cost": 89400.0,
            "plan_rows": 500000,
            "actual_rows": 500000,
            "actual_time_ms": 3650.0,
            "loops": 1,
            "Loops": 1,
            "sort_key": "COL_M05 DESC",
            "is_bottleneck": True,
            "bottleneck_reason": "External merge Disk: 48,512kB spilled to disk due to insufficient work_mem",
            "children": [
                {
                    "id": "node-sort-child-scan",
                    "node_type": "Sequential Scan",
                    "Node Type": "Seq Scan",
                    "relation_name": "TBL_C99",
                    "Relation Name": "TBL_C99",
                    "startup_cost": 0.0,
                    "total_cost": 41200.0,
                    "Total Cost": 41200.0,
                    "plan_rows": 500000,
                    "actual_rows": 500000,
                    "actual_time_ms": 1150.0,
                    "loops": 1,
                    "Loops": 1,
                    "filter_expr": "COL_S04 = :STR",
                    "is_bottleneck": False,
                    "children": []
                }
            ]
        }
    }

    # Additional queries for realistic dashboard
    plan_qe_part = {
        "Plan": {
            "id": "node-part-agg",
            "node_type": "Aggregate",
            "relation_name": "TBL_D44",
            "startup_cost": 28000.0,
            "total_cost": 31200.0,
            "Total Cost": 31200.0,
            "plan_rows": 120,
            "actual_rows": 120,
            "actual_time_ms": 1180.0,
            "loops": 1,
            "is_bottleneck": False,
            "children": [
                {
                    "id": "node-part-scan",
                    "node_type": "Sequential Scan",
                    "relation_name": "TBL_D44",
                    "startup_cost": 0.0,
                    "total_cost": 29800.0,
                    "Total Cost": 29800.0,
                    "plan_rows": 850000,
                    "actual_rows": 850000,
                    "actual_time_ms": 1120.0,
                    "loops": 1,
                    "filter_expr": "COL_T09 BETWEEN :DATE AND :DATE",
                    "is_bottleneck": True,
                    "bottleneck_reason": "Historical time-series table lacking partition pruning",
                    "children": []
                }
            ]
        }
    }

    query_events = [
        QueryEvent(
            id="QE-84920",
            fingerprint="fp_7a9c8f12",
            anonymized_sql=(
                "SELECT COL_R01, COUNT(COL_C01), SUM(COL_M05)\n"
                "FROM TBL_A12\n"
                "WHERE COL_D02 >= :DATE AND COL_R01 = :INT\n"
                "GROUP BY COL_R01;"
            ),
            table_token="TBL_A12",
            avg_latency_ms=1420.5,
            calls_per_minute=450,
            primary_bottleneck="Sequential Scan on TBL_A12",
            risk_level="LOW",
            status="NEEDS_REVIEW",
            plan_json=plan_qe_seq,
            created_at=now - datetime.timedelta(hours=4),
        ),
        QueryEvent(
            id="QE-19402",
            fingerprint="fp_3b81ea09",
            anonymized_sql=(
                "SELECT a.COL_C01, a.COL_R01, b.COL_S04, SUM(a.COL_M05)\n"
                "FROM TBL_A12 a\n"
                "JOIN TBL_B03 b ON a.COL_R01 = b.COL_R01\n"
                "WHERE b.COL_S04 = :STR\n"
                "GROUP BY a.COL_C01, a.COL_R01, b.COL_S04;"
            ),
            table_token="TBL_A12 / TBL_B03",
            avg_latency_ms=2850.0,
            calls_per_minute=210,
            primary_bottleneck="Nested Loop Join & Unindexed Scan",
            risk_level="LOW",
            status="SIMULATED",
            plan_json=plan_qe_join,
            created_at=now - datetime.timedelta(hours=6),
        ),
        QueryEvent(
            id="QE-55109",
            fingerprint="fp_e29c0174",
            anonymized_sql=(
                "SELECT COL_C01, COL_M05, COL_T09\n"
                "FROM TBL_C99\n"
                "WHERE COL_S04 = :STR\n"
                "ORDER BY COL_M05 DESC\n"
                "LIMIT :INT;"
            ),
            table_token="TBL_C99",
            avg_latency_ms=3650.0,
            calls_per_minute=95,
            primary_bottleneck="Expensive Sort / Disk Spill (48MB external merge)",
            risk_level="MEDIUM",
            status="NEEDS_REVIEW",
            plan_json=plan_qe_sort,
            created_at=now - datetime.timedelta(hours=8),
        ),
        QueryEvent(
            id="QE-33012",
            fingerprint="fp_91bb0a38",
            anonymized_sql=(
                "SELECT DATE_TRUNC('day', COL_T09), SUM(COL_M05)\n"
                "FROM TBL_D44\n"
                "WHERE COL_T09 BETWEEN :DATE AND :DATE\n"
                "GROUP BY 1;"
            ),
            table_token="TBL_D44",
            avg_latency_ms=1180.0,
            calls_per_minute=320,
            primary_bottleneck="Missing Declarative Partitioning",
            risk_level="HIGH",
            status="NEEDS_REVIEW",
            plan_json=plan_qe_part,
            created_at=now - datetime.timedelta(hours=12),
        ),
    ]
    db.add_all(query_events)

    # 3. Recommendations & XAI Evidence
    rec_seq = Recommendation(
        id="REC-301",
        query_id="QE-84920",
        title="Create Composite Index on TBL_A12 (COL_D02, COL_R01)",
        type="INDEX_COMPOSITE",
        recommended_action="CREATE INDEX CONCURRENTLY idx_tbl_a12_d02_r01 ON TBL_A12 (COL_D02, COL_R01);",
        rationale=(
            "The query performs a full sequential scan across 1,450,000 rows in TBL_A12 to filter on COL_D02 and COL_R01. "
            "A composite B-tree index eliminates heap traversal and allows direct index range scan."
        ),
        status="PENDING",
        confidence_score=0.94,
        risk_level="LOW",
        xai_evidence={
            "bottleneck_type": "Sequential Scan on High-Volume Table",
            "affected_plan_nodes": ["Seq Scan on TBL_A12 (cost=39800.0, rows=1450000)"],
            "evidence_signals": [
                "1.45M heap tuples fetched to filter 42 matching rows",
                "Predicate filter (COL_D02 >= :DATE AND COL_R01 = :INT) has high selectivity",
                "Sequential Scan accounts for 97.8% of total query execution time"
            ],
            "recommended_action": "CREATE INDEX CONCURRENTLY idx_tbl_a12_d02_r01 ON TBL_A12 (COL_D02, COL_R01);",
            "expected_read_improvement_percent_range": [75.0, 88.0],
            "estimated_write_latency_increase_ms_range": [0.6, 1.2],
            "estimated_storage_overhead_gb_range": [0.9, 1.6],
            "confidence": 0.94,
            "risk_level": "LOW",
            "privacy_status": PRIVACY_STATEMENT,
        },
        created_at=now - datetime.timedelta(hours=4),
    )

    rec_join = Recommendation(
        id="REC-302",
        query_id="QE-19402",
        title="Create Composite Covering Index on Inner Join Relation TBL_B03 (COL_R01, COL_S04)",
        type="INDEX_COMPOSITE",
        recommended_action="CREATE INDEX CONCURRENTLY idx_tbl_b03_r01_s04 ON TBL_B03 (COL_R01, COL_S04);",
        rationale=(
            "The execution plan executes a Nested Loop join with 98,400 inner iterations. "
            "Adding a composite index on TBL_B03(COL_R01, COL_S04) transforms the inner join lookup from repeated index page scans into a fast covering index lookup."
        ),
        status="SIMULATED",
        confidence_score=0.92,
        risk_level="LOW",
        xai_evidence={
            "bottleneck_type": "Nested-Loop Join Amplification",
            "affected_plan_nodes": [
                "Nested Loop Join (total_cost=51200.0)",
                "Inner Index Scan on TBL_B03 (loops=98400)"
            ],
            "evidence_signals": [
                "Outer relation produces 98,400 rows driving repeated inner lookups",
                "Missing composite index on join column + filter predicate (COL_R01, COL_S04)",
                "Loop multiplier causes 2,740ms of latency inside the nested loop node"
            ],
            "recommended_action": "CREATE INDEX CONCURRENTLY idx_tbl_b03_r01_s04 ON TBL_B03 (COL_R01, COL_S04);",
            "expected_read_improvement_percent_range": [72.0, 85.0],
            "estimated_write_latency_increase_ms_range": [0.8, 1.5],
            "estimated_storage_overhead_gb_range": [1.1, 2.3],
            "confidence": 0.92,
            "risk_level": "LOW",
            "privacy_status": PRIVACY_STATEMENT,
        },
        created_at=now - datetime.timedelta(hours=6),
    )

    rec_sort = Recommendation(
        id="REC-303",
        query_id="QE-55109",
        title="Pre-Sorted B-Tree Index on TBL_C99 (COL_M05 DESC) to Prevent Disk Spill",
        type="REWRITE_QUERY",
        recommended_action=(
            "CREATE INDEX CONCURRENTLY idx_tbl_c99_m05_desc ON TBL_C99 (COL_S04, COL_M05 DESC);\n"
            "-- Optional session tuning: SET LOCAL work_mem = '64MB';"
        ),
        rationale=(
            "The sort operation spilled 48,512kB to disk via external merge. "
            "A composite index on (COL_S04, COL_M05 DESC) allows PostgreSQL to read rows directly in order, removing the sort node completely."
        ),
        status="PENDING",
        confidence_score=0.89,
        risk_level="MEDIUM",
        xai_evidence={
            "bottleneck_type": "Expensive Sort Disk Spill",
            "affected_plan_nodes": ["Sort operator (external merge Disk: 48512kB)"],
            "evidence_signals": [
                "Sort memory exceeded work_mem allocation, triggering temp file disk I/O",
                "Sort node consumes 3,650ms (82% of query runtime)",
                "Composite index on (COL_S04, COL_M05 DESC) satisfies ORDER BY and LIMIT without sorting"
            ],
            "recommended_action": "CREATE INDEX CONCURRENTLY idx_tbl_c99_m05_desc ON TBL_C99 (COL_S04, COL_M05 DESC);",
            "expected_read_improvement_percent_range": [60.0, 78.0],
            "estimated_write_latency_increase_ms_range": [0.5, 1.1],
            "estimated_storage_overhead_gb_range": [0.6, 1.4],
            "confidence": 0.89,
            "risk_level": "MEDIUM",
            "privacy_status": PRIVACY_STATEMENT,
        },
        created_at=now - datetime.timedelta(hours=8),
    )

    rec_part = Recommendation(
        id="REC-304",
        query_id="QE-33012",
        title="Implement Declarative Range Partitioning on TBL_D44 by COL_T09",
        type="TABLE_PARTITIONING",
        recommended_action=(
            "-- Range Partitioning Architecture Advisory\n"
            "ALTER TABLE TBL_D44 PARTITION BY RANGE (COL_T09);\n"
            "CREATE TABLE TBL_D44_Y2026_M09 PARTITION OF TBL_D44 FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');"
        ),
        rationale=(
            "Table TBL_D44 is an append-only time series table with 850k+ rows per month. "
            "Partitioning by date allows PostgreSQL partition pruning to only scan relevant monthly slices."
        ),
        status="PENDING",
        confidence_score=0.85,
        risk_level="HIGH",
        xai_evidence={
            "bottleneck_type": "High Table Volume Partitioning Opportunity",
            "affected_plan_nodes": ["Sequential Scan on entire TBL_D44 heap"],
            "evidence_signals": [
                "Queries consistently query 30-day time windows",
                "Unpartitioned table scan wastes buffer pool space with old historical data",
                "Partition pruning would reduce scanned blocks by ~88%"
            ],
            "recommended_action": "ALTER TABLE TBL_D44 PARTITION BY RANGE (COL_T09);",
            "expected_read_improvement_percent_range": [75.0, 90.0],
            "estimated_write_latency_increase_ms_range": [1.2, 2.8],
            "estimated_storage_overhead_gb_range": [0.1, 0.4],
            "confidence": 0.85,
            "risk_level": "HIGH",
            "privacy_status": PRIVACY_STATEMENT,
        },
        created_at=now - datetime.timedelta(hours=12),
    )

    db.add_all([rec_seq, rec_join, rec_sort, rec_part])

    # 4. Initial Simulation for REC-302
    sim_join = Simulation(
        id="SIM-1002",
        recommendation_id="REC-302",
        before_cost=54200.0,
        after_cost=8450.0,
        before_latency_ms=2850.0,
        after_latency_ms=480.0,
        improvement_pct=83.1,
        write_latency_impact_ms=0.92,
        storage_overhead_gb=1.65,
        confidence=0.92,
        risk_level="LOW",
        simulated_plan_nodes=[
            {
                "node_type": "Aggregate",
                "total_cost": 8450.0,
                "actual_time_ms": 480.0,
                "children": [
                    {
                        "node_type": "Hash Join",
                        "total_cost": 7200.0,
                        "actual_time_ms": 410.0,
                        "children": [
                            {
                                "node_type": "Index Scan",
                                "relation_name": "TBL_A12",
                                "index_name": "idx_tbl_a12_d02_r01",
                                "actual_time_ms": 190.0,
                                "is_bottleneck": False
                            },
                            {
                                "node_type": "Index Only Scan",
                                "relation_name": "TBL_B03",
                                "index_name": "idx_tbl_b03_r01_s04",
                                "actual_time_ms": 95.0,
                                "is_bottleneck": False
                            }
                        ]
                    }
                ]
            }
        ],
        created_at=now - datetime.timedelta(hours=5),
    )
    db.add(sim_join)

    # 5. Audit Logs
    audit_logs = [
        AuditLog(
            id="AUD-001",
            query_id="QE-84920",
            recommendation_id=None,
            anonymized_target="TBL_A12",
            action_type="QUERY_ANONYMIZED",
            actor_id="SYSTEM_INGEST",
            timestamp=now - datetime.timedelta(hours=4),
            details={"masked_literals_count": 2, "privacy_check": "PASSED"},
        ),
        AuditLog(
            id="AUD-002",
            query_id="QE-84920",
            recommendation_id="REC-301",
            anonymized_target="TBL_A12 (COL_D02, COL_R01)",
            action_type="RECOMMENDATION_GENERATED",
            actor_id="QUERYGUARD_ENGINE",
            timestamp=now - datetime.timedelta(hours=4),
            details={"type": "INDEX_COMPOSITE", "confidence": 0.94},
        ),
        AuditLog(
            id="AUD-003",
            query_id="QE-19402",
            recommendation_id="REC-302",
            anonymized_target="TBL_B03 (COL_R01, COL_S04)",
            action_type="SIMULATION_EXECUTED",
            actor_id="DBA_ADMIN_01",
            timestamp=now - datetime.timedelta(hours=5),
            details={"simulated_improvement": "83.1%", "cost_reduction": "84.4%"},
        ),
    ]
    db.add_all(audit_logs)

    db.commit()
    _seed_frontend_entities(db)


def _seed_frontend_entities(db: Session):
    now = datetime.datetime.utcnow()

    # Employees & Role Hierarchy (Stored in PostgreSQL Database)
    import hashlib

    employees = [
        {
            "id": "usr-1",
            "employee_id": "EMP-DBA-01",
            "username": "priya.sharma",
            "full_name": "Priya Sharma",
            "email": "priya.sharma@queryguard.io",
            "password_hash": hashlib.sha256(b"Dba@Guard2026!").hexdigest(),
            "role": "DBA",
            "hierarchy_level": 3,
            "department": "Database Reliability & Architecture",
            "avatar": "PS",
            "is_active": True,
        },
        {
            "id": "usr-2",
            "employee_id": "EMP-ENG-02",
            "username": "arjun.patel",
            "full_name": "Arjun Patel",
            "email": "arjun.patel@queryguard.io",
            "password_hash": hashlib.sha256(b"Eng@Guard2026!").hexdigest(),
            "role": "ENGINEER",
            "hierarchy_level": 2,
            "department": "Data Platform & Infrastructure",
            "avatar": "AP",
            "is_active": True,
        },
        {
            "id": "usr-3",
            "employee_id": "EMP-AUD-03",
            "username": "alex.vance",
            "full_name": "Alex Vance",
            "email": "alex.vance@queryguard.io",
            "password_hash": hashlib.sha256(b"Auditor@Guard2026!").hexdigest(),
            "role": "VIEWER",
            "hierarchy_level": 1,
            "department": "Security & Compliance Governance",
            "avatar": "AV",
            "is_active": True,
        },
    ]
    for emp_data in employees:
        existing = db.query(User).filter((User.id == emp_data["id"]) | (User.employee_id == emp_data["employee_id"])).first()
        if existing:
            for k, v in emp_data.items():
                setattr(existing, k, v)
        else:
            db.add(User(**emp_data))
    db.commit()

    # 1. qry-7c91
    if not db.query(QueryEvent).filter(QueryEvent.id == "qry-7c91").first():
        plan_7c91 = {
            "id": "pg-7c91",
            "queryEventId": "qry-7c91",
            "planCost": 182341.2,
            "planDepth": 4,
            "nodeCount": 5,
            "nodes": [
                {
                    "id": "node_1",
                    "operatorType": "AGGREGATE",
                    "estimatedCost": 182341.2,
                    "estimatedRowsBucket": "100_TO_1K",
                    "actualRowsBucket": "100_TO_1K",
                    "actualTimeMsBucket": "2S_TO_3S",
                    "loopsBucket": "1",
                    "depth": 0,
                    "isCritical": False,
                    "notes": "GroupAggregate on COL_REGION_ID, date_trunc"
                },
                {
                    "id": "node_2",
                    "parentId": "node_1",
                    "operatorType": "NESTED_LOOP",
                    "joinType": "INNER",
                    "estimatedCost": 178920.0,
                    "estimatedRowsBucket": "1M_TO_10M",
                    "actualRowsBucket": "1M_TO_10M",
                    "actualTimeMsBucket": "2S_TO_3S",
                    "loopsBucket": "1",
                    "depth": 1,
                    "isCritical": True,
                    "notes": "High cost nested loop with unindexed inner sequential scan"
                },
                {
                    "id": "node_3",
                    "parentId": "node_2",
                    "operatorType": "INDEX_SCAN",
                    "relationToken": "TBL_STORES",
                    "indexToken": "IDX_STORES_PKEY",
                    "estimatedCost": 8.4,
                    "estimatedRowsBucket": "100_TO_1K",
                    "actualRowsBucket": "100_TO_1K",
                    "actualTimeMsBucket": "1MS_TO_10MS",
                    "loopsBucket": "1",
                    "depth": 2,
                    "isCritical": False,
                    "notes": "Index scan using primary key"
                },
                {
                    "id": "node_4",
                    "parentId": "node_2",
                    "operatorType": "SEQ_SCAN",
                    "relationToken": "TBL_SALES",
                    "estimatedCost": 178911.6,
                    "estimatedRowsBucket": "10M_PLUS",
                    "actualRowsBucket": "10M_PLUS",
                    "actualTimeMsBucket": "2S_TO_3S",
                    "loopsBucket": "1",
                    "depth": 2,
                    "isCritical": True,
                    "filterColumns": ["COL_STATUS", "COL_TX_DATE"],
                    "notes": "Unindexed sequential scan on 12.4M rows. Primary performance bottleneck."
                },
                {
                    "id": "node_5",
                    "parentId": "node_1",
                    "operatorType": "SORT",
                    "sortColumns": ["SUM(COL_AMOUNT) DESC"],
                    "estimatedCost": 182341.2,
                    "estimatedRowsBucket": "100_TO_1K",
                    "actualRowsBucket": "100_TO_1K",
                    "actualTimeMsBucket": "10MS_TO_100MS",
                    "loopsBucket": "1",
                    "depth": 1,
                    "isCritical": False,
                    "notes": "QuickSort on aggregated sum"
                }
            ]
        }
        q_7c91 = QueryEvent(
            id="qry-7c91",
            fingerprint="FP_7C91E88B429A",
            anonymized_sql="SELECT COL_REGION_ID, DATE_TRUNC(:TEXT, COL_TX_DATE) AS tx_week, COUNT(*), SUM(COL_AMOUNT) FROM TBL_SALES JOIN TBL_STORES ON TBL_SALES.COL_STORE_ID = TBL_STORES.COL_ID WHERE COL_STATUS = :TEXT AND COL_TX_DATE >= :TIMESTAMP AND COL_TX_DATE < :TIMESTAMP GROUP BY 1, 2 ORDER BY 4 DESC;",
            table_token="TBL_SALES",
            avg_latency_ms=2450.4,
            calls_per_minute=18,
            primary_bottleneck="LARGE_SEQ_SCAN",
            risk_level="HIGH",
            status="SIMULATED",
            plan_json=plan_7c91,
            created_at=now - datetime.timedelta(minutes=15)
        )
        db.add(q_7c91)

    # 2. qry-4b18
    if not db.query(QueryEvent).filter(QueryEvent.id == "qry-4b18").first():
        plan_4b18 = {
            "id": "pg-4b18",
            "queryEventId": "qry-4b18",
            "planCost": 98450.0,
            "planDepth": 3,
            "nodeCount": 3,
            "nodes": [
                {
                    "id": "node_201",
                    "operatorType": "NESTED_LOOP",
                    "joinType": "INNER",
                    "estimatedCost": 98450.0,
                    "estimatedRowsBucket": "100K_TO_1M",
                    "actualRowsBucket": "100K_TO_1M",
                    "actualTimeMsBucket": "1S_TO_2S",
                    "loopsBucket": "1",
                    "depth": 0,
                    "isCritical": True,
                    "notes": "Nested loop iterating over unindexed line items"
                },
                {
                    "id": "node_202",
                    "parentId": "node_201",
                    "operatorType": "INDEX_SCAN",
                    "relationToken": "TBL_ORDERS",
                    "indexToken": "IDX_ORDERS_STATUS",
                    "estimatedCost": 450.0,
                    "estimatedRowsBucket": "10K_TO_100K",
                    "actualRowsBucket": "10K_TO_100K",
                    "actualTimeMsBucket": "10MS_TO_100MS",
                    "loopsBucket": "1",
                    "depth": 1,
                    "isCritical": False,
                    "notes": "Fast index scan on orders"
                },
                {
                    "id": "node_203",
                    "parentId": "node_201",
                    "operatorType": "SEQ_SCAN",
                    "relationToken": "TBL_LINE_ITEMS",
                    "estimatedCost": 98000.0,
                    "estimatedRowsBucket": "1M_TO_10M",
                    "actualRowsBucket": "1M_TO_10M",
                    "actualTimeMsBucket": "1S_TO_2S",
                    "loopsBucket": "1420",
                    "depth": 1,
                    "isCritical": True,
                    "filterColumns": ["COL_ORDER_ID", "COL_BILLED_FLAG"],
                    "notes": "Repeated inner sequential scan executed 1,420 times"
                }
            ]
        }
        q_4b18 = QueryEvent(
            id="qry-4b18",
            fingerprint="FP_4B18D3391AA0",
            anonymized_sql="SELECT COL_ITEM_ID, COL_PRICE, COL_QTY FROM TBL_LINE_ITEMS WHERE COL_ORDER_ID = :INT AND COL_BILLED_FLAG = :BOOL;",
            table_token="TBL_LINE_ITEMS",
            avg_latency_ms=1820.0,
            calls_per_minute=145,
            primary_bottleneck="REPEATED_INNER_LOOP",
            risk_level="MEDIUM",
            status="SIMULATED",
            plan_json=plan_4b18,
            created_at=now - datetime.timedelta(minutes=30)
        )
        db.add(q_4b18)

    # 3. qry-9e02
    if not db.query(QueryEvent).filter(QueryEvent.id == "qry-9e02").first():
        plan_9e02 = {
            "id": "pg-9e02",
            "queryEventId": "qry-9e02",
            "planCost": 64200.0,
            "planDepth": 2,
            "nodeCount": 2,
            "nodes": [
                {
                    "id": "node_301",
                    "operatorType": "SORT",
                    "sortColumns": ["COL_STOCK_QTY ASC", "COL_LAST_AUDIT DESC"],
                    "estimatedCost": 64200.0,
                    "estimatedRowsBucket": "500K_TO_1M",
                    "actualRowsBucket": "500K_TO_1M",
                    "actualTimeMsBucket": "1S_TO_2S",
                    "loopsBucket": "1",
                    "depth": 0,
                    "isCritical": True,
                    "notes": "External Disk Spill Sort (work_mem exhaustion)"
                },
                {
                    "id": "node_302",
                    "parentId": "node_301",
                    "operatorType": "SEQ_SCAN",
                    "relationToken": "TBL_INVENTORY",
                    "estimatedCost": 41200.0,
                    "estimatedRowsBucket": "1M_TO_5M",
                    "actualRowsBucket": "1M_TO_5M",
                    "actualTimeMsBucket": "500MS_TO_1S",
                    "loopsBucket": "1",
                    "depth": 1,
                    "isCritical": False,
                    "notes": "Full inventory table scan"
                }
            ]
        }
        q_9e02 = QueryEvent(
            id="qry-9e02",
            fingerprint="FP_9E02F810CC44",
            anonymized_sql="SELECT COL_SKU, COL_WAREHOUSE_ID, COL_STOCK_QTY FROM TBL_INVENTORY WHERE COL_STOCK_QTY < :INT ORDER BY COL_STOCK_QTY ASC, COL_LAST_AUDIT DESC LIMIT :INT;",
            table_token="TBL_INVENTORY",
            avg_latency_ms=1410.2,
            calls_per_minute=62,
            primary_bottleneck="EXPENSIVE_SORT",
            risk_level="LOW",
            status="ANALYZED",
            plan_json=plan_9e02,
            created_at=now - datetime.timedelta(hours=1)
        )
        db.add(q_9e02)
    db.commit()

    # Recommendations
    # rec-9182
    if not db.query(Recommendation).filter(Recommendation.id == "rec-9182").first():
        evidence_9182 = {
            "version": "1.0",
            "bottleneckType": "LARGE_SEQ_SCAN",
            "affectedPlanNodes": ["node_4"],
            "reasonCodes": [
                "UNINDEXED_FILTER_PREDICATE",
                "HIGH_COST_HEAP_TRAVERSAL",
                "HIGH_FREQUENCY_AMPLIFICATION"
            ],
            "observedEvidence": {
                "scanType": "SEQ_SCAN",
                "loopCountBucket": "1",
                "relationSizeBucket": "10M_PLUS_ROWS"
            },
            "recommendedAction": "CREATE_COMPOSITE_BTREE",
            "maskedChangeTemplate": "CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_SALES_REGION_DATE ON TBL_SALES (COL_REGION_ID, COL_TX_DATE);",
            "alternativesConsidered": [
                {
                    "action": "SINGLE_COLUMN_INDEX_COL_TX_DATE",
                    "rank": 2,
                    "reasonLowerRank": "Lower selectivity than composite index with equality column first."
                }
            ],
            "confidence": "HIGH",
            "riskLevel": "LOW",
            "limitations": [
                "Simulation measured with HypoPG in session RAM.",
                "Write penalty estimated at 1–2ms per INSERT/UPDATE on TBL_SALES."
            ],
            "privacyStatus": "VERIFIED_MASKED"
        }
        rec_9182 = Recommendation(
            id="rec-9182",
            query_id="qry-7c91",
            title="Add Composite B-Tree Index on (COL_REGION_ID, COL_TX_DATE)",
            type="INDEX_COMPOSITE",
            recommended_action="CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_SALES_REGION_DATE ON TBL_SALES (COL_REGION_ID, COL_TX_DATE);",
            rationale="Eliminates 178,911 cost sequential scan on TBL_SALES by creating an index matching the equality and range predicates.",
            status="VALIDATED",
            confidence_score=0.94,
            risk_level="LOW",
            xai_evidence=evidence_9182,
            created_at=now - datetime.timedelta(minutes=10)
        )
        db.add(rec_9182)

    # rec-4410
    if not db.query(Recommendation).filter(Recommendation.id == "rec-4410").first():
        evidence_4410 = {
            "version": "1.0",
            "bottleneckType": "REPEATED_INNER_LOOP",
            "affectedPlanNodes": ["node_203"],
            "reasonCodes": ["REPEATED_NESTED_LOOP_SEQ_SCAN", "HIGH_CARDINALITY_INNER_RELATION"],
            "observedEvidence": {"scanType": "SEQ_SCAN", "loopCountBucket": "1420"},
            "recommendedAction": "CREATE_PARTIAL_INDEX",
            "maskedChangeTemplate": "CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_LINE_ITEMS_UNBILLED ON TBL_LINE_ITEMS (COL_ORDER_ID) WHERE COL_BILLED_FLAG = false;",
            "alternativesConsidered": [
                {"action": "FULL_INDEX_ON_ORDER_ID", "rank": 2, "reasonLowerRank": "Higher storage overhead than partial index filter."}
            ],
            "confidence": "HIGH",
            "riskLevel": "LOW",
            "limitations": ["HypoPG virtual index simulation in session RAM."],
            "privacyStatus": "VERIFIED_MASKED"
        }
        rec_4410 = Recommendation(
            id="rec-4410",
            query_id="qry-4b18",
            title="Add Partial B-Tree Index for Unbilled Line Items",
            type="INDEX_PARTIAL",
            recommended_action="CREATE INDEX CONCURRENTLY IF NOT EXISTS IDX_LINE_ITEMS_UNBILLED ON TBL_LINE_ITEMS (COL_ORDER_ID) WHERE COL_BILLED_FLAG = false;",
            rationale="Converts repeated inner sequential loop into fast index point lookups, reducing query iteration latency by 88%.",
            status="VALIDATED",
            confidence_score=0.91,
            risk_level="LOW",
            xai_evidence=evidence_4410,
            created_at=now - datetime.timedelta(minutes=25)
        )
        db.add(rec_4410)

    # rec-3209
    if not db.query(Recommendation).filter(Recommendation.id == "rec-3209").first():
        evidence_3209 = {
            "version": "1.0",
            "bottleneckType": "EXPENSIVE_SORT",
            "affectedPlanNodes": ["node_301"],
            "reasonCodes": ["WORK_MEM_SPILL_TO_DISK", "UNINDEXED_SORT_COLUMNS"],
            "observedEvidence": {"sortSpillDetected": True},
            "recommendedAction": "SET_WORK_MEM_OR_INDEX",
            "maskedChangeTemplate": "SET LOCAL work_mem = '64MB'; -- Or rewrite sort key",
            "alternativesConsidered": [],
            "confidence": "MEDIUM",
            "riskLevel": "LOW",
            "limitations": ["Session-scoped configuration advisory."],
            "privacyStatus": "VERIFIED_MASKED"
        }
        rec_3209 = Recommendation(
            id="rec-3209",
            query_id="qry-9e02",
            title="Increase work_mem for Inventory Multi-Column Sort",
            type="SESSION_PARAM_ADVISORY",
            recommended_action="SET LOCAL work_mem = '64MB'; -- Or rewrite sort key",
            rationale="Prevents temporary disk files by providing sufficient memory for in-memory quicksort.",
            status="DRAFT",
            confidence_score=0.78,
            risk_level="LOW",
            xai_evidence=evidence_3209,
            created_at=now - datetime.timedelta(minutes=45)
        )
        db.add(rec_3209)
    db.commit()

    # Simulations
    if not db.query(Simulation).filter(Simulation.id == "sim-8812").first():
        sim_8812 = Simulation(
            id="sim-8812",
            recommendation_id="rec-9182",
            simulation_type="HYPOPG",
            status="COMPLETED",
            label="Simulated estimate",
            before_cost=182341.2,
            after_cost=30510.8,
            before_latency_ms=2450.0,
            after_latency_ms=380.0,
            improvement_pct=83.3,
            write_latency_impact_ms=1.5,
            storage_overhead_gb=2.1,
            confidence=0.94,
            risk_level="LOW",
            created_at=now - datetime.timedelta(minutes=8)
        )
        db.add(sim_8812)

    if not db.query(Simulation).filter(Simulation.id == "sim-4421").first():
        sim_4421 = Simulation(
            id="sim-4421",
            recommendation_id="rec-4410",
            simulation_type="HYPOPG",
            status="COMPLETED",
            label="Simulated estimate",
            before_cost=98450.0,
            after_cost=11800.0,
            before_latency_ms=1820.0,
            after_latency_ms=210.0,
            improvement_pct=88.0,
            write_latency_impact_ms=0.8,
            storage_overhead_gb=0.4,
            confidence=0.91,
            risk_level="LOW",
            created_at=now - datetime.timedelta(minutes=20)
        )
        db.add(sim_4421)
    db.commit()

    # Audit Logs
    initial_audits = [
        ("aud-101", "usr-1", "Priya Sharma (DBA)", "DBA", "APPROVED", "RECOMMENDATION", "rec-9182", "Recommendation rec-9182 approved by DBA. Generated change script for human review. No production deployment occurred."),
        ("aud-102", "usr-1", "Priya Sharma (DBA)", "DBA", "SIMULATED", "SIMULATION", "sim-8812", "HypoPG virtual index simulation completed. Cost: 182,341 -> 30,510 (-83.3%). Zero physical disk mutation."),
        ("aud-103", "usr-2", "Arjun Patel (Engineer)", "ENGINEER", "ANALYZED", "QUERY", "qry-7c91", "Automated plan parser detected LARGE_SEQ_SCAN bottleneck on TBL_SALES with 12.4M estimated rows.")
    ]
    for aud_id, act_id, act_name, act_role, ev_type, ent_type, ent_id, desc in initial_audits:
        if not db.query(AuditLog).filter(AuditLog.id == aud_id).first():
            db.add(
                AuditLog(
                    id=aud_id,
                    query_id="qry-7c91",
                    recommendation_id="rec-9182" if "rec" in ent_id else None,
                    anonymized_target="TBL_SALES",
                    action_type=ev_type,
                    actor_id=act_id,
                    timestamp=now - datetime.timedelta(minutes=12),
                    details={
                        "actor_name": act_name,
                        "actor_role": act_role,
                        "recommendationId": ent_id if "rec" in ent_id else None,
                        "description": desc,
                        "policy": "NO_AUTOMATIC_PRODUCTION_DDL"
                    }
                )
            )
    db.commit()


def seed_database_force(db: Session):
    # Reset recommendation statuses
    recs = db.query(Recommendation).all()
    for r in recs:
        if r.id == "rec-9182":
            r.status = "VALIDATED"
        elif r.id == "rec-4410":
            r.status = "VALIDATED"
        elif r.id == "rec-3209":
            r.status = "DRAFT"
        else:
            r.status = "PENDING"

    # Remove approvals created during interactive sessions
    db.query(Approval).delete()
    db.commit()

    _seed_frontend_entities(db)


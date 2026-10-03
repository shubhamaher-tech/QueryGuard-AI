-- QueryGuard AI PostgreSQL 16 Seed Data
-- Strictly anonymized workload metadata records

INSERT INTO users (id, username, role, created_at) VALUES
('DBA_ADMIN_01', 'lead_dba_alex', 'DBA', NOW() - INTERVAL '30 days'),
('ANALYST_02', 'perf_analyst_sarah', 'ANALYST', NOW() - INTERVAL '20 days')
ON CONFLICT (id) DO NOTHING;

-- Scenario 1: Sequential scan on high-volume anonymized table
-- Scenario 2: Nested-loop join with unindexed inner relation
-- Scenario 3: Expensive sort / aggregate query with disk spill

INSERT INTO query_events (id, fingerprint, anonymized_sql, table_token, avg_latency_ms, calls_per_minute, primary_bottleneck, risk_level, status, plan_json, created_at)
VALUES
(
    'QE-84920',
    'fp_7a9c8f12',
    'SELECT COL_R01, COUNT(COL_C01), SUM(COL_M05)
FROM TBL_A12
WHERE COL_D02 >= :DATE AND COL_R01 = :INT
GROUP BY COL_R01;',
    'TBL_A12',
    1420.5,
    450,
    'Sequential Scan on TBL_A12',
    'LOW',
    'NEEDS_REVIEW',
    '{
        "Plan": {
            "id": "node-root-agg",
            "Node Type": "Aggregate",
            "startup_cost": 38400.0,
            "total_cost": 41200.0,
            "plan_rows": 42,
            "actual_rows": 42,
            "actual_time_ms": 1420.5,
            "loops": 1,
            "is_bottleneck": false,
            "children": [
                {
                    "id": "node-seq-scan-root",
                    "Node Type": "Seq Scan",
                    "Relation Name": "TBL_A12",
                    "startup_cost": 0.0,
                    "total_cost": 39800.0,
                    "plan_rows": 1450000,
                    "actual_rows": 1450000,
                    "actual_time_ms": 1390.2,
                    "loops": 1,
                    "filter_expr": "(COL_D02 >= :DATE AND COL_R01 = :INT)",
                    "is_bottleneck": true,
                    "bottleneck_reason": "Unindexed sequential scan traversing 1.45M tuples (98% of query execution time)",
                    "children": []
                }
            ]
        }
    }'::jsonb,
    NOW() - INTERVAL '4 hours'
),
(
    'QE-19402',
    'fp_3b81ea09',
    'SELECT a.COL_C01, a.COL_R01, b.COL_S04, SUM(a.COL_M05)
FROM TBL_A12 a
JOIN TBL_B03 b ON a.COL_R01 = b.COL_R01
WHERE b.COL_S04 = :STR
GROUP BY a.COL_C01, a.COL_R01, b.COL_S04;',
    'TBL_A12 / TBL_B03',
    2850.0,
    210,
    'Nested Loop Join & Unindexed Scan',
    'LOW',
    'SIMULATED',
    '{
        "Plan": {
            "id": "node-agg-1",
            "Node Type": "Aggregate",
            "startup_cost": 42100.0,
            "total_cost": 54200.0,
            "plan_rows": 850,
            "actual_rows": 850,
            "actual_time_ms": 2850.0,
            "loops": 1,
            "is_bottleneck": false,
            "children": [
                {
                    "id": "node-nl-join-2",
                    "Node Type": "Nested Loop",
                    "startup_cost": 210.0,
                    "total_cost": 51200.0,
                    "plan_rows": 125000,
                    "actual_rows": 98400,
                    "actual_time_ms": 2740.0,
                    "loops": 1,
                    "is_bottleneck": true,
                    "bottleneck_reason": "High iteration multiplier without indexed inner join key",
                    "children": [
                        {
                            "id": "node-seq-scan-3",
                            "Node Type": "Seq Scan",
                            "Relation Name": "TBL_A12",
                            "startup_cost": 0.0,
                            "total_cost": 31500.0,
                            "plan_rows": 1450000,
                            "actual_rows": 1450000,
                            "actual_time_ms": 1920.0,
                            "loops": 1,
                            "filter_expr": "(COL_D02 >= :DATE AND COL_R01 = :INT)",
                            "is_bottleneck": true,
                            "bottleneck_reason": "Full table heap scan across 1.45M tuples without composite index",
                            "children": []
                        },
                        {
                            "id": "node-idx-scan-4",
                            "Node Type": "Index Scan",
                            "Relation Name": "TBL_B03",
                            "index_name": "pk_tbl_b03",
                            "startup_cost": 0.42,
                            "total_cost": 12.5,
                            "plan_rows": 1,
                            "actual_rows": 1,
                            "actual_time_ms": 0.82,
                            "loops": 98400,
                            "is_bottleneck": false,
                            "bottleneck_reason": "Repeated 98,400 times inside loop",
                            "children": []
                        }
                    ]
                }
            ]
        }
    }'::jsonb,
    NOW() - INTERVAL '6 hours'
),
(
    'QE-55109',
    'fp_e29c0174',
    'SELECT COL_C01, COL_M05, COL_T09
FROM TBL_C99
WHERE COL_S04 = :STR
ORDER BY COL_M05 DESC
LIMIT :INT;',
    'TBL_C99',
    3650.0,
    95,
    'Expensive Sort / Disk Spill (48MB external merge)',
    'MEDIUM',
    'NEEDS_REVIEW',
    '{
        "Plan": {
            "id": "node-sort-root",
            "Node Type": "Sort",
            "Relation Name": "TBL_C99",
            "startup_cost": 84200.0,
            "total_cost": 89400.0,
            "plan_rows": 500000,
            "actual_rows": 500000,
            "actual_time_ms": 3650.0,
            "loops": 1,
            "sort_key": "COL_M05 DESC",
            "is_bottleneck": true,
            "bottleneck_reason": "External merge Disk: 48,512kB spilled to disk due to insufficient work_mem",
            "children": [
                {
                    "id": "node-sort-child-scan",
                    "Node Type": "Seq Scan",
                    "Relation Name": "TBL_C99",
                    "startup_cost": 0.0,
                    "total_cost": 41200.0,
                    "plan_rows": 500000,
                    "actual_rows": 500000,
                    "actual_time_ms": 1150.0,
                    "loops": 1,
                    "filter_expr": "COL_S04 = :STR",
                    "is_bottleneck": false,
                    "children": []
                }
            ]
        }
    }'::jsonb,
    NOW() - INTERVAL '8 hours'
),
(
    'QE-33012',
    'fp_91bb0a38',
    'SELECT DATE_TRUNC(''day'', COL_T09), SUM(COL_M05)
FROM TBL_D44
WHERE COL_T09 BETWEEN :DATE AND :DATE
GROUP BY 1;',
    'TBL_D44',
    1180.0,
    320,
    'Missing Declarative Partitioning',
    'HIGH',
    'NEEDS_REVIEW',
    '{
        "Plan": {
            "id": "node-part-agg",
            "Node Type": "Aggregate",
            "startup_cost": 28000.0,
            "total_cost": 31200.0,
            "plan_rows": 120,
            "actual_rows": 120,
            "actual_time_ms": 1180.0,
            "loops": 1,
            "is_bottleneck": false,
            "children": [
                {
                    "id": "node-part-scan",
                    "Node Type": "Seq Scan",
                    "Relation Name": "TBL_D44",
                    "startup_cost": 0.0,
                    "total_cost": 29800.0,
                    "plan_rows": 850000,
                    "actual_rows": 850000,
                    "actual_time_ms": 1120.0,
                    "loops": 1,
                    "filter_expr": "COL_T09 BETWEEN :DATE AND :DATE",
                    "is_bottleneck": true,
                    "bottleneck_reason": "Historical time-series table lacking partition pruning",
                    "children": []
                }
            ]
        }
    }'::jsonb,
    NOW() - INTERVAL '12 hours'
)
ON CONFLICT (id) DO NOTHING;

-- Seed Recommendations
INSERT INTO recommendations (id, query_id, title, type, recommended_action, rationale, status, confidence_score, risk_level, xai_evidence, created_at)
VALUES
(
    'REC-301',
    'QE-84920',
    'Create Composite Index on TBL_A12 (COL_D02, COL_R01)',
    'INDEX_COMPOSITE',
    'CREATE INDEX CONCURRENTLY idx_tbl_a12_d02_r01 ON TBL_A12 (COL_D02, COL_R01);',
    'A composite B-tree index eliminates heap traversal and allows direct index range scan for filtered queries.',
    'PENDING',
    0.94,
    'LOW',
    '{
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
        "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    }'::jsonb,
    NOW() - INTERVAL '4 hours'
),
(
    'REC-302',
    'QE-19402',
    'Create Composite Covering Index on Inner Join Relation TBL_B03 (COL_R01, COL_S04)',
    'INDEX_COMPOSITE',
    'CREATE INDEX CONCURRENTLY idx_tbl_b03_r01_s04 ON TBL_B03 (COL_R01, COL_S04);',
    'The execution plan executes a Nested Loop join with 98,400 inner iterations. A covering index transforms repeated inner lookups to logarithmic cost.',
    'SIMULATED',
    0.92,
    'LOW',
    '{
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
        "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    }'::jsonb,
    NOW() - INTERVAL '6 hours'
),
(
    'REC-303',
    'QE-55109',
    'Pre-Sorted B-Tree Index on TBL_C99 (COL_M05 DESC) to Prevent Disk Spill',
    'REWRITE_QUERY',
    'CREATE INDEX CONCURRENTLY idx_tbl_c99_m05_desc ON TBL_C99 (COL_S04, COL_M05 DESC);',
    'The sort operation spilled 48MB to disk via external merge. Pre-ordered B-tree indexing bypasses sorting completely.',
    'PENDING',
    0.89,
    'MEDIUM',
    '{
        "bottleneck_type": "Expensive Sort Disk Spill",
        "affected_plan_nodes": ["Sort operator (external merge Disk: 48512kB)"],
        "evidence_signals": [
            "Sort memory exceeded work_mem allocation, triggering temp file disk I/O",
            "Sort node consumes 3,650ms (82% of query runtime)",
            "Composite index satisfies ORDER BY and LIMIT without sorting"
        ],
        "recommended_action": "CREATE INDEX CONCURRENTLY idx_tbl_c99_m05_desc ON TBL_C99 (COL_S04, COL_M05 DESC);",
        "expected_read_improvement_percent_range": [60.0, 78.0],
        "estimated_write_latency_increase_ms_range": [0.5, 1.1],
        "estimated_storage_overhead_gb_range": [0.6, 1.4],
        "confidence": 0.89,
        "risk_level": "MEDIUM",
        "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    }'::jsonb,
    NOW() - INTERVAL '8 hours'
),
(
    'REC-304',
    'QE-33012',
    'Implement Declarative Range Partitioning on TBL_D44 by COL_T09',
    'TABLE_PARTITIONING',
    'ALTER TABLE TBL_D44 PARTITION BY RANGE (COL_T09);',
    'Table TBL_D44 is an append-only time series table. Range partitioning enables partition pruning to reduce scanned blocks by ~88%.',
    'PENDING',
    0.85,
    'HIGH',
    '{
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
        "privacy_status": "No raw rows, raw literals, or plaintext schema identifiers were used in this analysis."
    }'::jsonb,
    NOW() - INTERVAL '12 hours'
)
ON CONFLICT (id) DO NOTHING;

-- Seed Simulation
INSERT INTO simulations (id, recommendation_id, before_cost, after_cost, before_latency_ms, after_latency_ms, improvement_pct, write_latency_impact_ms, storage_overhead_gb, confidence, risk_level, created_at)
VALUES
(
    'SIM-1002',
    'REC-302',
    54200.0,
    8450.0,
    2850.0,
    480.0,
    83.1,
    0.92,
    1.65,
    0.92,
    'LOW',
    NOW() - INTERVAL '5 hours'
)
ON CONFLICT (id) DO NOTHING;

-- Seed Audit Logs
INSERT INTO audit_logs (id, query_id, recommendation_id, anonymized_target, action_type, actor_id, timestamp, details)
VALUES
('AUD-001', 'QE-84920', NULL, 'TBL_A12', 'QUERY_ANONYMIZED', 'SYSTEM_INGEST', NOW() - INTERVAL '4 hours', '{"masked_literals_count": 2, "privacy_check": "PASSED"}'::jsonb),
('AUD-002', 'QE-84920', 'REC-301', 'TBL_A12 (COL_D02, COL_R01)', 'RECOMMENDATION_GENERATED', 'QUERYGUARD_ENGINE', NOW() - INTERVAL '4 hours', '{"type": "INDEX_COMPOSITE", "confidence": 0.94}'::jsonb),
('AUD-003', 'QE-19402', 'REC-302', 'TBL_B03 (COL_R01, COL_S04)', 'SIMULATION_EXECUTED', 'DBA_ADMIN_01', NOW() - INTERVAL '5 hours', '{"simulated_improvement": "83.1%", "cost_reduction": "84.4%"}'::jsonb)
ON CONFLICT (id) DO NOTHING;

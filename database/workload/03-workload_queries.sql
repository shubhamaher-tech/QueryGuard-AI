-- Benchmark Workload Queries
-- Safe, read-only analytical queries designed to stress test PostgreSQL planner
-- and produce realistic slow-query statistics in pg_stat_statements.
-- NOTE: Local seed file only; raw query text is never stored in QueryGuard application DB.

-- 1. Benchmark Query 1: High-Volume Sequential Scan (region_id + transaction_date filter)
-- Expected Bottleneck: Sequential Scan on transactions (~250,000 rows evaluated without index)
SELECT 
    region_id, 
    COUNT(*) AS total_tx_count, 
    SUM(amount) AS total_amount, 
    AVG(amount) AS avg_amount
FROM transactions
WHERE region_id = 5 
  AND transaction_date >= '2025-06-01'
GROUP BY region_id;

-- 2. Benchmark Query 2: Join-Heavy Reporting Query (transactions + regions + customers + order_items + products)
-- Expected Bottleneck: Nested-loop / Hash join amplification with unindexed inner relations
SELECT 
    c.customer_code, 
    r.region_code, 
    p.product_code, 
    SUM(oi.quantity * oi.unit_price) AS line_total,
    COUNT(oi.id) AS item_count
FROM transactions t
JOIN regions r ON t.region_id = r.id
JOIN customers c ON t.customer_id = c.id
JOIN order_items oi ON oi.transaction_id = t.id
JOIN products p ON oi.product_id = p.id
WHERE r.id = 3 
  AND t.transaction_date >= '2025-03-01'
GROUP BY c.customer_code, r.region_code, p.product_code
ORDER BY line_total DESC
LIMIT 50;

-- 3. Benchmark Query 3: Expensive Sort & Aggregation (work_mem pressure)
-- Expected Bottleneck: Expensive Sort on large result set (external merge disk spill)
SELECT 
    customer_id, 
    COUNT(id) AS tx_count, 
    SUM(amount) AS total_spent, 
    AVG(amount) AS avg_spent
FROM transactions
WHERE status = 'COMPLETED'
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 100;

-- 4. Benchmark Query 4: Correlated Subquery
-- Expected Bottleneck: Repeated subquery evaluation per outer row (SQL rewrite candidate)
SELECT 
    t.id, 
    t.amount, 
    t.transaction_date, 
    t.region_id
FROM transactions t
WHERE t.amount > (
    SELECT AVG(t2.amount) 
    FROM transactions t2 
    WHERE t2.region_id = t.region_id
)
  AND t.region_id = 4
LIMIT 100;

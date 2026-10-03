-- Workload Runner Script for pg_stat_statements population
-- Executes each benchmark query repeatedly so pg_stat_statements records execution statistics.

DO $$
DECLARE
    i INT;
    temp_count BIGINT;
BEGIN
    RAISE NOTICE 'Executing benchmark queries to populate pg_stat_statements...';

    -- Run Query 1 (Sequential Scan) 12 times
    FOR i IN 1..12 LOOP
        PERFORM 
            region_id, 
            COUNT(*), 
            SUM(amount), 
            AVG(amount)
        FROM transactions
        WHERE region_id = 5 
          AND transaction_date >= '2025-06-01'
        GROUP BY region_id;
    END LOOP;

    -- Run Query 2 (Join-Heavy) 8 times
    FOR i IN 1..8 LOOP
        PERFORM 
            c.customer_code, 
            r.region_code, 
            p.product_code, 
            SUM(oi.quantity * oi.unit_price) AS line_total
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
    END LOOP;

    -- Run Query 3 (Sort & Aggregation) 10 times
    FOR i IN 1..10 LOOP
        PERFORM 
            customer_id, 
            COUNT(id), 
            SUM(amount), 
            AVG(amount)
        FROM transactions
        WHERE status = 'COMPLETED'
        GROUP BY customer_id
        ORDER BY SUM(amount) DESC
        LIMIT 100;
    END LOOP;

    -- Run Query 4 (Correlated Subquery) 6 times
    FOR i IN 1..6 LOOP
        PERFORM 
            t.id, 
            t.amount, 
            t.transaction_date
        FROM transactions t
        WHERE t.amount > (
            SELECT AVG(t2.amount) 
            FROM transactions t2 
            WHERE t2.region_id = t.region_id
        )
          AND t.region_id = 4
        LIMIT 100;
    END LOOP;

    RAISE NOTICE 'Benchmark execution completed. pg_stat_statements statistics populated.';
END
$$;

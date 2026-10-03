-- Synthetic Data Generator for workload_db
-- Populates benchmark tables using PostgreSQL generate_series()
-- Strictly synthetic: No PII, no real company/people names, no credentials.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM regions LIMIT 1) THEN
        RAISE NOTICE 'Synthetic benchmark data already populated. Skipping generation.';
        RETURN;
    END IF;

    RAISE NOTICE 'Generating synthetic benchmark dataset...';

    -- 1. Regions (~20 rows)
    INSERT INTO regions (region_code, description)
    SELECT 
        'REG_' || LPAD(i::text, 3, '0'),
        'Synthetic Geographic Partition Region ' || i::text
    FROM generate_series(1, 20) AS i;

    -- 2. Customers (~10,000 rows)
    INSERT INTO customers (customer_code, region_id, tier, credit_limit, created_at)
    SELECT
        'CUST_' || LPAD(i::text, 6, '0'),
        1 + (i % 20),
        CASE (i % 4)
            WHEN 0 THEN 'PLATINUM'
            WHEN 1 THEN 'GOLD'
            WHEN 2 THEN 'SILVER'
            ELSE 'STANDARD'
        END,
        ROUND((500.00 + (i % 50) * 100.00)::numeric, 2),
        DATE '2024-01-01' + ((i % 700) * INTERVAL '1 day')
    FROM generate_series(1, 10000) AS i;

    -- 3. Products (~2,000 rows)
    INSERT INTO products (product_code, category_code, base_price, stock_level, created_at)
    SELECT
        'PROD_' || LPAD(i::text, 5, '0'),
        'CAT_' || LPAD((1 + (i % 25))::text, 2, '0'),
        ROUND((10.00 + (i % 490) * 1.50)::numeric, 2),
        50 + (i % 950),
        DATE '2024-01-01' + ((i % 500) * INTERVAL '1 day')
    FROM generate_series(1, 2000) AS i;

    -- 4. Transactions (~250,000 rows)
    INSERT INTO transactions (transaction_ref, customer_id, region_id, amount, status, transaction_date, created_at)
    SELECT
        'TX_' || LPAD(i::text, 8, '0'),
        1 + (i % 10000),
        1 + (i % 20),
        ROUND((15.00 + ((i * 17) % 980) + ((i % 100) * 0.25))::numeric, 2),
        CASE (i % 5)
            WHEN 0 THEN 'PENDING'
            WHEN 1 THEN 'CANCELLED'
            ELSE 'COMPLETED'
        END,
        DATE '2025-01-01' + ((i % 450) * INTERVAL '1 day'),
        CURRENT_TIMESTAMP - ((i % 10000) * INTERVAL '1 minute')
    FROM generate_series(1, 250000) AS i;

    -- 5. Order Items (~500,000 rows)
    INSERT INTO order_items (transaction_id, product_id, quantity, unit_price, created_at)
    SELECT
        1 + (i % 250000),
        1 + (i % 2000),
        1 + (i % 8),
        ROUND((12.50 + (i % 85) * 2.25)::numeric, 2),
        CURRENT_TIMESTAMP - ((i % 10000) * INTERVAL '1 minute')
    FROM generate_series(1, 500000) AS i;

    -- Analyze tables to generate realistic statistics for PostgreSQL query planner
    ANALYZE regions;
    ANALYZE customers;
    ANALYZE products;
    ANALYZE transactions;
    ANALYZE order_items;

    RAISE NOTICE 'Synthetic benchmark data generation completed successfully.';
END
$$;

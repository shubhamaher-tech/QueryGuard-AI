-- Synthetic Workload Database Initialization
-- Database: workload_db

-- 1. Enable pg_stat_statements and HypoPG
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS hypopg;

-- 2. Create Read-Only User for QueryGuard Telemetry Collector
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'workload_ro') THEN
        CREATE ROLE workload_ro WITH LOGIN PASSWORD 'workload_ro_pass';
    END IF;
END
$$;

-- 3. Define Synthetic Schema Tables
CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    region_code VARCHAR(32) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(64) UNIQUE NOT NULL,
    region_id INT REFERENCES regions(id),
    tier VARCHAR(32) NOT NULL,
    credit_limit NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_code VARCHAR(64) UNIQUE NOT NULL,
    category_code VARCHAR(32) NOT NULL,
    base_price NUMERIC(10,2) NOT NULL,
    stock_level INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_ref VARCHAR(64) UNIQUE NOT NULL,
    customer_id INT REFERENCES customers(id),
    region_id INT REFERENCES regions(id),
    amount NUMERIC(12,2) NOT NULL,
    status VARCHAR(32) NOT NULL,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT REFERENCES transactions(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: Intentionally omitting secondary indexes on (region_id, transaction_date),
-- (status), (customer_id), and order_items(product_id) to induce realistic query bottlenecks.

-- 4. Grant read-only permissions and hypopg execution to workload_ro
GRANT CONNECT ON DATABASE workload_db TO workload_ro;
GRANT USAGE ON SCHEMA public TO workload_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workload_ro;
GRANT SELECT ON pg_stat_statements TO workload_ro;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO workload_ro;
GRANT pg_read_all_stats TO workload_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO workload_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO workload_ro;

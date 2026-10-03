-- QueryGuard AI - TPC-H SF 0.1 Synthetic Benchmark Workload
-- Target: workload_db on workload-postgres
-- Read-only benchmark dataset for complex query analysis

CREATE TABLE IF NOT EXISTS tpch_region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name VARCHAR(25) NOT NULL,
    r_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS tpch_nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name VARCHAR(25) NOT NULL,
    n_regionkey INTEGER REFERENCES tpch_region(r_regionkey),
    n_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS tpch_supplier (
    s_suppkey INTEGER PRIMARY KEY,
    s_name VARCHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER REFERENCES tpch_nation(n_nationkey),
    s_phone VARCHAR(15) NOT NULL,
    s_acctbal NUMERIC(15,2) NOT NULL,
    s_comment VARCHAR(101)
);

CREATE TABLE IF NOT EXISTS tpch_part (
    p_partkey INTEGER PRIMARY KEY,
    p_name VARCHAR(55) NOT NULL,
    p_mfgr VARCHAR(25) NOT NULL,
    p_brand VARCHAR(10) NOT NULL,
    p_type VARCHAR(25) NOT NULL,
    p_size INTEGER NOT NULL,
    p_container VARCHAR(10) NOT NULL,
    p_retailprice NUMERIC(15,2) NOT NULL,
    p_comment VARCHAR(23)
);

CREATE TABLE IF NOT EXISTS tpch_partsupp (
    ps_partkey INTEGER REFERENCES tpch_part(p_partkey),
    ps_suppkey INTEGER REFERENCES tpch_supplier(s_suppkey),
    ps_availqty INTEGER NOT NULL,
    ps_supplycost NUMERIC(15,2) NOT NULL,
    ps_comment VARCHAR(199),
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE IF NOT EXISTS tpch_customer (
    c_custkey INTEGER PRIMARY KEY,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER REFERENCES tpch_nation(n_nationkey),
    c_phone VARCHAR(15) NOT NULL,
    c_acctbal NUMERIC(15,2) NOT NULL,
    c_mktsegment VARCHAR(10) NOT NULL,
    c_comment VARCHAR(117)
);

CREATE TABLE IF NOT EXISTS tpch_orders (
    o_orderkey INTEGER PRIMARY KEY,
    o_custkey INTEGER REFERENCES tpch_customer(c_custkey),
    o_orderstatus CHAR(1) NOT NULL,
    o_totalprice NUMERIC(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority VARCHAR(15) NOT NULL,
    o_clerk VARCHAR(15) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(79)
);

CREATE TABLE IF NOT EXISTS tpch_lineitem (
    l_orderkey INTEGER REFERENCES tpch_orders(o_orderkey),
    l_partkey INTEGER REFERENCES tpch_part(p_partkey),
    l_suppkey INTEGER REFERENCES tpch_supplier(s_suppkey),
    l_linenumber INTEGER NOT NULL,
    l_quantity NUMERIC(15,2) NOT NULL,
    l_extendedprice NUMERIC(15,2) NOT NULL,
    l_discount NUMERIC(15,2) NOT NULL,
    l_tax NUMERIC(15,2) NOT NULL,
    l_returnflag CHAR(1) NOT NULL,
    l_linestatus CHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct VARCHAR(25) NOT NULL,
    l_shipmode VARCHAR(10) NOT NULL,
    l_comment VARCHAR(44),
    PRIMARY KEY (l_orderkey, l_linenumber)
);

-- Seed Regions (5 rows)
INSERT INTO tpch_region (r_regionkey, r_name, r_comment) VALUES
(0, 'AFRICA', 'Standard TPC-H benchmark region'),
(1, 'AMERICA', 'Standard TPC-H benchmark region'),
(2, 'ASIA', 'Standard TPC-H benchmark region'),
(3, 'EUROPE', 'Standard TPC-H benchmark region'),
(4, 'MIDDLE EAST', 'Standard TPC-H benchmark region')
ON CONFLICT (r_regionkey) DO NOTHING;

-- Seed Nations (25 rows)
INSERT INTO tpch_nation (n_nationkey, n_name, n_regionkey, n_comment) VALUES
(0, 'ALGERIA', 0, 'Nation'), (1, 'ARGENTINA', 1, 'Nation'), (2, 'BRAZIL', 1, 'Nation'),
(3, 'CANADA', 1, 'Nation'), (4, 'EGYPT', 4, 'Nation'), (5, 'ETHIOPIA', 0, 'Nation'),
(6, 'FRANCE', 3, 'Nation'), (7, 'GERMANY', 3, 'Nation'), (8, 'INDIA', 2, 'Nation'),
(9, 'INDONESIA', 2, 'Nation'), (10, 'IRAN', 4, 'Nation'), (11, 'IRAQ', 4, 'Nation'),
(12, 'JAPAN', 2, 'Nation'), (13, 'JORDAN', 4, 'Nation'), (14, 'KENYA', 0, 'Nation'),
(15, 'MOROCCO', 0, 'Nation'), (16, 'MOZAMBIQUE', 0, 'Nation'), (17, 'PERU', 1, 'Nation'),
(18, 'CHINA', 2, 'Nation'), (19, 'ROMANIA', 3, 'Nation'), (20, 'SAUDI ARABIA', 4, 'Nation'),
(21, 'VIETNAM', 2, 'Nation'), (22, 'RUSSIA', 3, 'Nation'), (23, 'UNITED KINGDOM', 3, 'Nation'),
(24, 'UNITED STATES', 1, 'Nation')
ON CONFLICT (n_nationkey) DO NOTHING;

-- Seed Suppliers (100 rows)
INSERT INTO tpch_supplier (s_suppkey, s_name, s_address, s_nationkey, s_phone, s_acctbal, s_comment)
SELECT 
    i, 
    'Supplier#' || LPAD(i::text, 9, '0'),
    'Address line ' || i::text,
    (i % 25),
    '15-' || LPAD((i % 1000)::text, 3, '0') || '-1234',
    ((i * 137 % 10000) - 2000)::numeric(15,2),
    'Synthetic supplier comment'
FROM generate_series(1, 100) AS i
ON CONFLICT (s_suppkey) DO NOTHING;

-- Seed Parts (2,000 rows)
INSERT INTO tpch_part (p_partkey, p_name, p_mfgr, p_brand, p_type, p_size, p_container, p_retailprice, p_comment)
SELECT 
    i, 
    'Part item ' || i::text,
    'Manufacturer#' || ((i % 5) + 1)::text,
    'Brand#' || ((i % 5) + 1)::text || ((i % 10) + 1)::text,
    CASE (i % 3) WHEN 0 THEN 'STANDARD BRUSHED' WHEN 1 THEN 'POLISHED NICKEL' ELSE 'ECONOMY BRASS' END,
    ((i % 50) + 1),
    CASE (i % 4) WHEN 0 THEN 'SM BOX' WHEN 1 THEN 'MED BOX' WHEN 2 THEN 'LG PKG' ELSE 'JUMBO CAN' END,
    ((i * 17 % 1500) + 50)::numeric(15,2),
    'Synthetic part'
FROM generate_series(1, 2000) AS i
ON CONFLICT (p_partkey) DO NOTHING;

-- Seed PartSupp (8,000 rows)
INSERT INTO tpch_partsupp (ps_partkey, ps_suppkey, ps_availqty, ps_supplycost, ps_comment)
SELECT 
    p, 
    s,
    ((p + s) * 7 % 9999 + 1),
    ((p * s) % 800 + 10)::numeric(15,2),
    'PartSupp relationship'
FROM (
    SELECT p, ((p * 3 + j) % 100 + 1) AS s
    FROM generate_series(1, 2000) AS p
    CROSS JOIN generate_series(0, 3) AS j
) sub
ON CONFLICT (ps_partkey, ps_suppkey) DO NOTHING;

-- Seed Customers (1,500 rows)
INSERT INTO tpch_customer (c_custkey, c_name, c_address, c_nationkey, c_phone, c_acctbal, c_mktsegment, c_comment)
SELECT 
    i,
    'Customer#' || LPAD(i::text, 9, '0'),
    'Customer address ' || i::text,
    (i % 25),
    '23-' || LPAD((i % 999)::text, 3, '0') || '-5678',
    ((i * 73 % 10000) - 1000)::numeric(15,2),
    CASE (i % 5) WHEN 0 THEN 'BUILDING' WHEN 1 THEN 'AUTOMOBILE' WHEN 2 THEN 'MACHINERY' WHEN 3 THEN 'HOUSEHOLD' ELSE 'FURNITURE' END,
    'Synthetic customer profile'
FROM generate_series(1, 1500) AS i
ON CONFLICT (c_custkey) DO NOTHING;

-- Seed Orders (15,000 rows)
INSERT INTO tpch_orders (o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment)
SELECT 
    i,
    ((i * 13) % 1500 + 1),
    CASE (i % 3) WHEN 0 THEN 'O' WHEN 1 THEN 'F' ELSE 'P' END,
    ((i * 107) % 50000 + 100)::numeric(15,2),
    '2024-01-01'::date + (i % 900) * interval '1 day',
    CASE (i % 5) WHEN 0 THEN '1-URGENT' WHEN 1 THEN '2-HIGH' WHEN 2 THEN '3-MEDIUM' WHEN 3 THEN '4-NOT SPECIFIED' ELSE '5-LOW' END,
    'Clerk#' || LPAD(((i % 100) + 1)::text, 9, '0'),
    0,
    'TPC-H synthetic order'
FROM generate_series(1, 15000) AS i
ON CONFLICT (o_orderkey) DO NOTHING;

-- Seed Lineitems (60,000 rows)
INSERT INTO tpch_lineitem (
    l_orderkey, l_partkey, l_suppkey, l_linenumber, l_quantity, l_extendedprice, 
    l_discount, l_tax, l_returnflag, l_linestatus, l_shipdate, l_commitdate, 
    l_receiptdate, l_shipinstruct, l_shipmode, l_comment
)
SELECT 
    o,
    ((o * 7 + line) % 2000 + 1),
    ((o * 11 + line) % 100 + 1),
    line,
    ((o + line) % 50 + 1)::numeric(15,2),
    (((o + line) % 50 + 1) * ((o * 17 % 100) + 20))::numeric(15,2),
    (((o + line) % 10)::numeric(15,2) / 100.0),
    0.05,
    CASE (o % 3) WHEN 0 THEN 'R' WHEN 1 THEN 'A' ELSE 'N' END,
    CASE (o % 2) WHEN 0 THEN 'O' ELSE 'F' END,
    '2024-01-05'::date + (o % 900) * interval '1 day',
    '2024-01-10'::date + (o % 900) * interval '1 day',
    '2024-01-15'::date + (o % 900) * interval '1 day',
    'DELIVER IN PERSON',
    CASE (o % 4) WHEN 0 THEN 'AIR' WHEN 1 THEN 'SHIP' WHEN 2 THEN 'TRUCK' ELSE 'MAIL' END,
    'Regular lineitem record'
FROM (
    SELECT o, line
    FROM generate_series(1, 15000) AS o
    CROSS JOIN generate_series(1, 4) AS line
) sub
ON CONFLICT (l_orderkey, l_linenumber) DO NOTHING;

-- Grant read-only permissions to workload_ro user
GRANT USAGE ON SCHEMA public TO workload_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workload_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO workload_ro;

ANALYZE tpch_region;
ANALYZE tpch_nation;
ANALYZE tpch_supplier;
ANALYZE tpch_part;
ANALYZE tpch_partsupp;
ANALYZE tpch_customer;
ANALYZE tpch_orders;
ANALYZE tpch_lineitem;

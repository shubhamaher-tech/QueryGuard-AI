-- QueryGuard AI - TPC-H Benchmark Schema Definition
-- Target: workload_db (workload-postgres)
-- Isolated from QueryGuard Application Database

CREATE SCHEMA IF NOT EXISTS tpch_sf01;

CREATE TABLE IF NOT EXISTS tpch_sf01.region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name VARCHAR(25) NOT NULL,
    r_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name VARCHAR(25) NOT NULL,
    n_regionkey INTEGER REFERENCES tpch_sf01.region(r_regionkey),
    n_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.part (
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

CREATE TABLE IF NOT EXISTS tpch_sf01.supplier (
    s_suppkey INTEGER PRIMARY KEY,
    s_name VARCHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER REFERENCES tpch_sf01.nation(n_nationkey),
    s_phone VARCHAR(15) NOT NULL,
    s_acctbal NUMERIC(15,2) NOT NULL,
    s_comment VARCHAR(101)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.partsupp (
    ps_partkey INTEGER REFERENCES tpch_sf01.part(p_partkey),
    ps_suppkey INTEGER REFERENCES tpch_sf01.supplier(s_suppkey),
    ps_availqty INTEGER NOT NULL,
    ps_supplycost NUMERIC(15,2) NOT NULL,
    ps_comment VARCHAR(199),
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.customer (
    c_custkey INTEGER PRIMARY KEY,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER REFERENCES tpch_sf01.nation(n_nationkey),
    c_phone VARCHAR(15) NOT NULL,
    c_acctbal NUMERIC(15,2) NOT NULL,
    c_mktsegment VARCHAR(10) NOT NULL,
    c_comment VARCHAR(117)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.orders (
    o_orderkey INTEGER PRIMARY KEY,
    o_custkey INTEGER REFERENCES tpch_sf01.customer(c_custkey),
    o_orderstatus VARCHAR(1) NOT NULL,
    o_totalprice NUMERIC(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority VARCHAR(15) NOT NULL,
    o_clerk VARCHAR(15) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(79)
);

CREATE TABLE IF NOT EXISTS tpch_sf01.lineitem (
    l_orderkey INTEGER REFERENCES tpch_sf01.orders(o_orderkey),
    l_partkey INTEGER REFERENCES tpch_sf01.part(p_partkey),
    l_suppkey INTEGER REFERENCES tpch_sf01.supplier(s_suppkey),
    l_linenumber INTEGER NOT NULL,
    l_quantity NUMERIC(15,2) NOT NULL,
    l_extendedprice NUMERIC(15,2) NOT NULL,
    l_discount NUMERIC(15,2) NOT NULL,
    l_tax NUMERIC(15,2) NOT NULL,
    l_returnflag VARCHAR(1) NOT NULL,
    l_linestatus VARCHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct VARCHAR(25) NOT NULL,
    l_shipmode VARCHAR(10) NOT NULL,
    l_comment VARCHAR(44),
    PRIMARY KEY (l_orderkey, l_linenumber)
);

-- Public synonyms / views for seamless cross-tool compatibility
DROP TABLE IF EXISTS public.tpch_lineitem, public.tpch_orders, public.tpch_partsupp, public.tpch_customer, public.tpch_part, public.tpch_supplier, public.tpch_nation, public.tpch_region CASCADE;
CREATE OR REPLACE VIEW public.tpch_region AS SELECT * FROM tpch_sf01.region;
CREATE OR REPLACE VIEW public.tpch_nation AS SELECT * FROM tpch_sf01.nation;
CREATE OR REPLACE VIEW public.tpch_part AS SELECT * FROM tpch_sf01.part;
CREATE OR REPLACE VIEW public.tpch_supplier AS SELECT * FROM tpch_sf01.supplier;
CREATE OR REPLACE VIEW public.tpch_partsupp AS SELECT * FROM tpch_sf01.partsupp;
CREATE OR REPLACE VIEW public.tpch_customer AS SELECT * FROM tpch_sf01.customer;
CREATE OR REPLACE VIEW public.tpch_orders AS SELECT * FROM tpch_sf01.orders;
CREATE OR REPLACE VIEW public.tpch_lineitem AS SELECT * FROM tpch_sf01.lineitem;

-- Grants for workload_ro user
GRANT USAGE ON SCHEMA tpch_sf01 TO workload_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA tpch_sf01 TO workload_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workload_ro;

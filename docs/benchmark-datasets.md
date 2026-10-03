# QueryGuard AI - Benchmark Datasets & Workload Catalog

## Overview

QueryGuard AI includes native support for realistic, local synthetic benchmark workloads in the `workload-postgres` container (`workload_db`). These datasets allow DBAs, developers, and hackathon evaluators to test real query performance, observe PostgreSQL 16 optimizer behaviors, trigger diverse bottlenecks, and simulate hypothetical index optimizations using **HypoPG**—without exposing real production or customer data.

---

## Supported Benchmark Workloads

| Benchmark | Scale / Size | Table Count | Row Count | Status | Target Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic E-Commerce** | ~810,000 rows | 5 | ~810,000 | **Active & Seeded** | High-volume OLTP & transactional reporting |
| **TPC-H SF 0.1** | ~100 MB | 8 | 86,630 | **Active & Seeded** | Standardized decision support & aggregations |
| **TPC-H SF 1.0** | ~1 GB | 8 | 6,000,000+ | **On-Demand** | Large-scale analytical joins & group-by |
| **Join Order Benchmark (JOB)** | IMDB Schema | 21 | Cataloged | **Schema Indexed** | Highly skewed multi-way join topologies |

---

## 1. Synthetic E-Commerce Workload

The primary OLTP simulation schema mimics modern distributed e-commerce data:

### Schema Tables:
- `transactions` (250,000 rows): Financial transactions with dates, status, amount, region_id, customer_id.
- `customers` (50,000 rows): Customer profiles with account balances, credit limits, tiers.
- `order_items` (500,000 rows): Line items linking transactions to products.
- `products` (10,000 rows): Product catalog with base prices, stock levels, categories.
- `regions` (10 rows): Geographic distribution.

### Typical Bottlenecks Triggered:
- **Sequential Scans**: Queries filtering on unindexed `region_id` or date ranges over 250k rows.
- **Nested Loop Joins**: Multi-table queries joining `order_items` without foreign key indexing.
- **Expensive Sorts**: `ORDER BY total_spent DESC` causing sort memory pressure.

---

## 2. TPC-H SF 0.1 Benchmark (100MB)

TPC-H is the industry-standard decision support benchmark. QueryGuard AI includes a synthetic, fully compliant generator seeded directly into `workload-postgres`.

### Schema Tables:
```sql
tpch_lineitem (60,000 rows)
tpch_orders   (15,000 rows)
tpch_customer (1,500 rows)
tpch_partsupp (8,000 rows)
tpch_part     (2,000 rows)
tpch_supplier (100 rows)
tpch_nation   (25 rows)
tpch_region   (5 rows)
```

### Verified Sample Queries:
1. **TPC-H Q1 (Pricing Summary Report)**:
   ```sql
   SELECT l_returnflag, l_linestatus, SUM(l_quantity) AS sum_qty,
          SUM(l_extendedprice) AS sum_base_price,
          SUM(l_extendedprice * (1 - l_discount)) AS sum_disc_price,
          AVG(l_quantity) AS avg_qty, AVG(l_extendedprice) AS avg_price, COUNT(*) AS count_order
   FROM tpch_lineitem WHERE l_shipdate <= '1998-09-01'
   GROUP BY l_returnflag, l_linestatus
   ORDER BY l_returnflag, l_linestatus;
   ```
   - **Detected Bottleneck**: `SEQUENTIAL_SCAN` on `tpch_lineitem`.
   - **HypoPG Optimization**: Creates virtual index on `(l_shipdate)` reducing planner cost significantly.

2. **TPC-H Q3 (Shipping Priority Query)**:
   ```sql
   SELECT l.l_orderkey, SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue,
          o.o_orderdate, o.o_shippriority
   FROM tpch_customer c JOIN tpch_orders o ON c.c_custkey = o.o_custkey
   JOIN tpch_lineitem l ON l.l_orderkey = o.o_orderkey
   WHERE c.c_mktsegment = 'BUILDING' AND o.o_orderdate < '1995-03-15' AND l.l_shipdate > '1995-03-15'
   GROUP BY l.l_orderkey, o.o_orderdate, o.o_shippriority
   ORDER BY revenue DESC, o.o_orderdate LIMIT 10;
   ```
   - **Detected Bottleneck**: `HASH_JOIN_SPILL` / `NESTED_LOOP` join amplification across 3 relations.

3. **TPC-H Q6 (Forecasting Revenue Change)**:
   ```sql
   SELECT SUM(l_extendedprice * l_discount) AS revenue FROM tpch_lineitem
   WHERE l_shipdate >= '1994-01-01' AND l_shipdate < '1995-01-01'
   AND l_discount >= 0.05 AND l_discount <= 0.07 AND l_quantity < 24;
   ```
   - **Detected Bottleneck**: `SEQUENTIAL_SCAN` on `tpch_lineitem` with multi-column filter.

4. **TPC-H Q10 (Returned Item Reporting)**:
   - 4-way join across `tpch_customer`, `tpch_orders`, `tpch_lineitem`, and `tpch_nation`.

---

## 3. TPC-H SF 1.0 (1GB Scaling)

For larger benchmarking requirements, a scale factor 1.0 generator script is provided at `database/workload/05-generate-tpch-sf1.sql`.
To populate SF 1.0:
```bash
docker exec -i queryguard-workload-postgres psql -U postgres -d workload_db -f /docker-entrypoint-initdb.d/05-generate-tpch-sf1.sql
```

---

## 4. Join Order Benchmark (JOB / IMDB)

The Join Order Benchmark tests optimizer card stability over extreme real-world correlation. Schema metadata for 21 IMDB tables (`title`, `cast_info`, `movie_companies`, `movie_info`, etc.) is registered in the QueryGuard benchmark catalog.

---

## Privacy & Security Guarantees

1. **Zero Production Data**: Every row in `workload_db` is generated through deterministic synthetic series.
2. **Read-Only Connection**: All query profiling connects via `workload_ro` with read-only transaction parameters:
   ```sql
   SET LOCAL default_transaction_read_only = on;
   SET LOCAL statement_timeout = '5000ms';
   SET LOCAL lock_timeout = '2000ms';
   ```
3. **AstLiteralMasking**: All user literals and constants are replaced with placeholders before any log or database write.
4. **HmacIdentifierTokenization**: Real relation names (`transactions` -> `TBL_2CF5B555`) are replaced with cryptographically salted HMAC tokens.

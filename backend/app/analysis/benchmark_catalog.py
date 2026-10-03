"""
Benchmark Catalog and Sample Query Definitions for QueryGuard AI

Includes:
- Synthetic E-Commerce (default active)
- TPC-H SF 0.1 (installed & ready in workload-postgres)
- TPC-H SF 1.0 (available on demand)
- Join Order Benchmark / IMDB (schema cataloged)
"""

from typing import List, Dict, Any
from app.analysis.schemas import BenchmarkInfo, SampleQueryItem

SAMPLE_QUERIES: List[SampleQueryItem] = [
    # E-Commerce Workload
    SampleQueryItem(
        id="ecom-slow-sales-region",
        name="Slow Sales Summary by Region",
        dataset="synthetic_ecommerce",
        description="Scans entire transactions table without an index on region_id and date. High cost sequential scan.",
        sql=(
            "SELECT region_id, COUNT(*) AS total_tx, SUM(amount) AS total_amount, AVG(amount) AS avg_amount "
            "FROM transactions WHERE region_id = 5 AND transaction_date >= '2025-06-01' GROUP BY region_id;"
        ),
        expected_bottleneck="SEQUENTIAL_SCAN",
        complexity="MODERATE",
    ),
    SampleQueryItem(
        id="ecom-multi-join-drilldown",
        name="Multi-Table Order Drilldown",
        dataset="synthetic_ecommerce",
        description="4-way join across transactions, customers, order items, and products with aggregation and sorting.",
        sql=(
            "SELECT c.customer_code, r.region_code, p.product_code, SUM(oi.quantity * oi.unit_price) AS line_total "
            "FROM transactions t JOIN regions r ON t.region_id = r.id "
            "JOIN customers c ON t.customer_id = c.id "
            "JOIN order_items oi ON oi.transaction_id = t.id "
            "JOIN products p ON oi.product_id = p.id "
            "WHERE r.id = 3 AND t.transaction_date >= '2025-03-01' "
            "GROUP BY c.customer_code, r.region_code, p.product_code "
            "ORDER BY line_total DESC LIMIT 50;"
        ),
        expected_bottleneck="NESTED_LOOP",
        complexity="COMPLEX",
    ),
    SampleQueryItem(
        id="ecom-unindexed-spending",
        name="Unindexed Customer Spending Report",
        dataset="synthetic_ecommerce",
        description="Sort and grouping over completed transactions without covering index, leading to sort memory pressure.",
        sql=(
            "SELECT customer_id, COUNT(id) AS tx_count, SUM(amount) AS total_spent, AVG(amount) AS avg_spent "
            "FROM transactions WHERE status = 'COMPLETED' "
            "GROUP BY customer_id ORDER BY total_spent DESC LIMIT 100;"
        ),
        expected_bottleneck="EXPENSIVE_SORT",
        complexity="SIMPLE",
    ),

    # TPC-H SF 0.1 Workload
    SampleQueryItem(
        id="tpch-q1-pricing-summary",
        name="TPC-H Q1: Pricing Summary Report",
        dataset="tpch_sf01",
        description="Scans lineitem rows shipped before cutoff date, aggregating revenue, discounts, taxes, and quantities.",
        sql=(
            "SELECT l_returnflag, l_linestatus, SUM(l_quantity) AS sum_qty, "
            "SUM(l_extendedprice) AS sum_base_price, "
            "SUM(l_extendedprice * (1 - l_discount)) AS sum_disc_price, "
            "AVG(l_quantity) AS avg_qty, AVG(l_extendedprice) AS avg_price, COUNT(*) AS count_order "
            "FROM tpch_lineitem WHERE l_shipdate <= '1998-09-01' "
            "GROUP BY l_returnflag, l_linestatus "
            "ORDER BY l_returnflag, l_linestatus;"
        ),
        expected_bottleneck="SEQUENTIAL_SCAN",
        complexity="MODERATE",
    ),
    SampleQueryItem(
        id="tpch-q3-shipping-priority",
        name="TPC-H Q3: Shipping Priority Query",
        dataset="tpch_sf01",
        description="3-way join of customer, orders, and lineitem to find high-value unshipped orders for building market segment.",
        sql=(
            "SELECT l.l_orderkey, SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue, "
            "o.o_orderdate, o.o_shippriority "
            "FROM tpch_customer c JOIN tpch_orders o ON c.c_custkey = o.o_custkey "
            "JOIN tpch_lineitem l ON l.l_orderkey = o.o_orderkey "
            "WHERE c.c_mktsegment = 'BUILDING' AND o.o_orderdate < '1995-03-15' AND l.l_shipdate > '1995-03-15' "
            "GROUP BY l.l_orderkey, o.o_orderdate, o.o_shippriority "
            "ORDER BY revenue DESC, o.o_orderdate LIMIT 10;"
        ),
        expected_bottleneck="HASH_JOIN_SPILL",
        complexity="COMPLEX",
    ),
    SampleQueryItem(
        id="tpch-q6-forecasting-revenue",
        name="TPC-H Q6: Forecasting Revenue Change",
        dataset="tpch_sf01",
        description="Quantifies revenue from eliminating discounts within specific percentage and quantity thresholds.",
        sql=(
            "SELECT SUM(l_extendedprice * l_discount) AS revenue FROM tpch_lineitem "
            "WHERE l_shipdate >= '1994-01-01' AND l_shipdate < '1995-01-01' "
            "AND l_discount >= 0.05 AND l_discount <= 0.07 AND l_quantity < 24;"
        ),
        expected_bottleneck="SEQUENTIAL_SCAN",
        complexity="SIMPLE",
    ),
    SampleQueryItem(
        id="tpch-q10-returned-item",
        name="TPC-H Q10: Returned Item Reporting",
        dataset="tpch_sf01",
        description="Identifies customers who experienced problem shipments, joining customer, orders, lineitem, and nation.",
        sql=(
            "SELECT c.c_custkey, c.c_name, SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue, "
            "c.c_acctbal, n.n_name "
            "FROM tpch_customer c JOIN tpch_orders o ON c.c_custkey = o.o_custkey "
            "JOIN tpch_lineitem l ON l.l_orderkey = o.o_orderkey "
            "JOIN tpch_nation n ON c.c_nationkey = n.n_nationkey "
            "WHERE o.o_orderdate >= '1993-10-01' AND o.o_orderdate < '1994-01-01' AND l.l_returnflag = 'R' "
            "GROUP BY c.c_custkey, c.c_name, c.c_acctbal, n.n_name "
            "ORDER BY revenue DESC LIMIT 20;"
        ),
        expected_bottleneck="NESTED_LOOP",
        complexity="COMPLEX",
    ),
]


BENCHMARKS: List[BenchmarkInfo] = [
    BenchmarkInfo(
        id="synthetic_ecommerce",
        name="Synthetic E-Commerce Workload",
        description="High-volume synthetic retail workload with 250k transactions, 50k customers, and 500k order items. Demonstrates typical real-world OLTP/reporting patterns.",
        is_available=True,
        table_count=5,
        estimated_rows=810000,
        tables=["transactions", "customers", "products", "regions", "order_items"],
        sample_queries=[q for q in SAMPLE_QUERIES if q.dataset == "synthetic_ecommerce"],
    ),
    BenchmarkInfo(
        id="tpch_sf01",
        name="TPC-H SF 0.1 Benchmark (100MB)",
        description="Standardized decision support benchmark scaled to factor 0.1 (60k lineitems, 15k orders). Realistic decision support workload with multi-way joins and date grouping.",
        is_available=True,
        table_count=8,
        estimated_rows=86630,
        tables=["tpch_region", "tpch_nation", "tpch_supplier", "tpch_part", "tpch_partsupp", "tpch_customer", "tpch_orders", "tpch_lineitem"],
        sample_queries=[q for q in SAMPLE_QUERIES if q.dataset == "tpch_sf01"],
    ),
    BenchmarkInfo(
        id="tpch_sf1",
        name="TPC-H SF 1.0 Benchmark (1GB)",
        description="Full scale factor 1.0 (6M lineitems, 1.5M orders). Scaled data generation script available in database/workload/05-generate-tpch-sf1.sql.",
        is_available=False,
        table_count=8,
        estimated_rows=6000000,
        tables=["tpch_region", "tpch_nation", "tpch_supplier", "tpch_part", "tpch_partsupp", "tpch_customer", "tpch_orders", "tpch_lineitem"],
        sample_queries=[],
    ),
    BenchmarkInfo(
        id="job_imdb",
        name="Join Order Benchmark (JOB / IMDB)",
        description="Complex join order benchmark representing real movie data with extreme skew, correlated predicates, and 21 relation topologies.",
        is_available=False,
        table_count=21,
        estimated_rows=3500000,
        tables=["title", "cast_info", "movie_companies", "movie_info", "name", "char_name", "role_type"],
        sample_queries=[],
    ),
]


def get_benchmark_catalog() -> List[BenchmarkInfo]:
    return BENCHMARKS


def get_sample_queries(dataset: str = None) -> List[SampleQueryItem]:
    if dataset:
        return [q for q in SAMPLE_QUERIES if q.dataset == dataset]
    return SAMPLE_QUERIES

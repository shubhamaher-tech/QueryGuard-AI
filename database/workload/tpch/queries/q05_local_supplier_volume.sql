-- TPC-H Q05: Local Supplier Volume Query (Complex multi-table join for SLM rewrite route)
-- Expected Bottleneck: NESTED_LOOP_BOTTLENECK / COMPLEX_JOIN
SELECT 
    n.n_name, 
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue 
FROM tpch_sf01.customer c 
JOIN tpch_sf01.orders o ON c.c_custkey = o.o_custkey 
JOIN tpch_sf01.lineitem l ON l.l_orderkey = o.o_orderkey 
JOIN tpch_sf01.supplier s ON l.l_suppkey = s.s_suppkey AND c.c_nationkey = s.s_nationkey 
JOIN tpch_sf01.nation n ON s.s_nationkey = n.n_nationkey 
JOIN tpch_sf01.region r ON n.n_regionkey = r.r_regionkey 
WHERE r.r_name = 'ASIA' 
  AND o.o_orderdate >= '1994-01-01' 
  AND o.o_orderdate < '1995-01-01' 
GROUP BY n.n_name 
ORDER BY revenue DESC;

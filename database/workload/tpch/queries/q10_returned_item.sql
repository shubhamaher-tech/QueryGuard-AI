-- TPC-H Q10: Returned Item Reporting (Multi-table join & top-N sort)
-- Expected Bottleneck: NESTED_LOOP_BOTTLENECK / EXPENSIVE_SORT
SELECT 
    c.c_custkey, 
    c.c_name, 
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue, 
    c.c_acctbal, 
    n.n_name 
FROM tpch_sf01.customer c 
JOIN tpch_sf01.orders o ON c.c_custkey = o.o_custkey 
JOIN tpch_sf01.lineitem l ON l.l_orderkey = o.o_orderkey 
JOIN tpch_sf01.nation n ON c.c_nationkey = n.n_nationkey 
WHERE o.o_orderdate >= '1993-10-01' 
  AND o.o_orderdate < '1994-01-01' 
  AND l.l_returnflag = 'R' 
GROUP BY c.c_custkey, c.c_name, c.c_acctbal, n.n_name 
ORDER BY revenue DESC 
LIMIT 20;

-- TPC-H Q03: Shipping Priority Query (Multi-table join & sort)
-- Expected Bottleneck: HASH_JOIN_SPILL / EXPENSIVE_SORT
SELECT 
    l.l_orderkey, 
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue, 
    o.o_orderdate, 
    o.o_shippriority 
FROM tpch_sf01.customer c 
JOIN tpch_sf01.orders o ON c.c_custkey = o.o_custkey 
JOIN tpch_sf01.lineitem l ON l.l_orderkey = o.o_orderkey 
WHERE c.c_mktsegment = 'BUILDING' 
  AND o.o_orderdate < '1995-03-15' 
  AND l.l_shipdate > '1995-03-15' 
GROUP BY l.l_orderkey, o.o_orderdate, o.o_shippriority 
ORDER BY revenue DESC, o.o_orderdate 
LIMIT 10;

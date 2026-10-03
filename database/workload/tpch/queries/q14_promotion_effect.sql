-- TPC-H Q14: Promotion Effect Query (Aggregate with CASE condition)
-- Expected Bottleneck: HASH_JOIN_HEAVY / AGGREGATION_HEAVY
SELECT 
    100.00 * SUM(CASE WHEN p.p_type LIKE 'PROMO%' THEN l.l_extendedprice * (1 - l.l_discount) ELSE 0 END) / 
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS promo_revenue 
FROM tpch_sf01.lineitem l 
JOIN tpch_sf01.part p ON l.l_partkey = p.p_partkey 
WHERE l.l_shipdate >= '1995-09-01' 
  AND l.l_shipdate < '1995-10-01';

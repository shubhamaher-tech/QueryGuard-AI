-- TPC-H Q06: Forecasting Revenue Change (Missing composite index on shipdate, discount, quantity)
-- Expected Bottleneck: SEQUENTIAL_SCAN
SELECT 
    SUM(l_extendedprice * l_discount) AS revenue 
FROM tpch_sf01.lineitem 
WHERE l_shipdate >= '1994-01-01' 
  AND l_shipdate < '1995-01-01' 
  AND l_discount >= 0.05 
  AND l_discount <= 0.07 
  AND l_quantity < 24;

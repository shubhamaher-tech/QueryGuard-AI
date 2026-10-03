-- TPC-H Q01: Pricing Summary Report (Date-range filter & heavy aggregation)
-- Expected Bottleneck: SEQUENTIAL_SCAN
SELECT 
    l_returnflag, 
    l_linestatus, 
    SUM(l_quantity) AS sum_qty, 
    SUM(l_extendedprice) AS sum_base_price, 
    SUM(l_extendedprice * (1 - l_discount)) AS sum_disc_price, 
    AVG(l_quantity) AS avg_qty, 
    AVG(l_extendedprice) AS avg_price, 
    COUNT(*) AS count_order 
FROM tpch_sf01.lineitem 
WHERE l_shipdate <= '1998-09-01' 
GROUP BY l_returnflag, l_linestatus 
ORDER BY l_returnflag, l_linestatus;

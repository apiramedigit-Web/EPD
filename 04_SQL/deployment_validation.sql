-- =============================================================================
-- deployment_validation.sql — REQ-07 / D02   (READ-ONLY)
-- Independent production totals used to reconcile the dashboard.
-- Sources: Dashboard/export_data_daily.py (TOTALS_SQL),
--          Dashboard/validate_range.py / validate_charts.py (window SQL).
-- =============================================================================

-- 1) Full-history totals — must equal the sum of the embedded daily facts
--    (export_data_daily.py aborts when they differ by more than 0.05)
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.record_status
    FROM public.ppc p
    WHERE p.source = 2 AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE', 'COST_PER_SALE', 'OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) impressions, SUM(clicks) clicks,
           SUM(spend) spend, SUM(sales) sales, SUM(orders) orders
    FROM public.ppc_performance
    WHERE source = 2 AND record_type IN ('campaign', 'ad')
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain
    ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
)
SELECT count(*)                                         AS campaigns,
       count(*) FILTER (WHERE c.record_status = 'running') AS active,
       count(*) FILTER (WHERE c.record_status = 'paused')  AS paused,
       COALESCE(SUM(pm.spend), 0)::numeric(16,2)        AS spend,
       COALESCE(SUM(pm.sales), 0)::numeric(16,2)        AS sales,
       COALESCE(SUM(pm.orders), 0)::numeric(16,0)       AS orders,
       COALESCE(SUM(pm.clicks), 0)::bigint              AS clicks,
       COALESCE(SUM(pm.impressions), 0)::bigint         AS impressions
FROM ebay_campaigns c
LEFT JOIN perf_metrics pm ON pm.parent_id = c.parent_id;

-- 2) Reporting-window totals — compare with the dashboard KPI cards for the
--    same From/To dates. Set :'date_from' and :'date_to' (YYYY-MM-DD).
WITH gp AS (
    SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
    FROM public.ppc_performance
    WHERE source = 2 AND record_type IN ('campaign', 'ad')
    GROUP BY parent_id
),
per AS (
    SELECT pp.parent_id,
           SUM(pp.impressions) impr, SUM(pp.clicks) clk,
           SUM(pp.spend) sp, SUM(pp.sales) sa, SUM(pp.orders) orr
    FROM public.ppc_performance pp
    JOIN gp ON gp.parent_id = pp.parent_id
    WHERE pp.source = 2
      AND ((gp.pref = 0 AND pp.record_type = 'campaign') OR (gp.pref = 1 AND pp.record_type = 'ad'))
      AND pp.date BETWEEN :'date_from' AND :'date_to'
    GROUP BY pp.parent_id
)
SELECT COALESCE(SUM(sp), 0)::numeric(16,2)    AS spend,
       COALESCE(SUM(sa), 0)::numeric(16,2)    AS sales,
       COALESCE(SUM(orr), 0)::numeric(16,0)   AS orders,
       COALESCE(SUM(clk), 0)::bigint          AS clicks,
       COALESCE(SUM(impr), 0)::bigint         AS impressions,
       COUNT(*) FILTER (WHERE sp > 0 OR sa > 0) AS campaigns_with_activity,
       COALESCE(MAX(sa), 0)::numeric(16,2)    AS top_campaign_sales,
       COALESCE(MAX(sp), 0)::numeric(16,2)    AS top_campaign_spend
FROM per;

-- 3) Latest reporting date available in production
SELECT MIN(date) AS first_date, MAX(date) AS last_date
FROM public.ppc_performance
WHERE source = 2;

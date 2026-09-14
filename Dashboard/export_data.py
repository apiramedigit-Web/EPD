#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_data.py  --  eBay PPC Performance Dashboard data exporter.

Runs the FINAL VALIDATED SQL (unchanged) against the production PostgreSQL
database (connection from the DATABASE_URL env var) and writes ./data.js.

Nothing is fabricated, estimated or hardcoded: every value written to data.js
is returned by SQL. Re-run this script any time to refresh the dashboard.
"""
import os
import json
import decimal
import datetime as dt
import psycopg

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")

# --- The FINAL VALIDATED campaign-grain query (parent_id kept first for alignment) ----
VALIDATED_SQL = r"""
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id)
           p.parent_id, p.source, p.ss_name, p.market_place,
           p.record_name, p.record_subtype, p.record_status, p.bid
    FROM public.ppc p
    WHERE p.source = 2 AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) AS impressions, SUM(clicks) AS clicks,
           SUM(spend) AS spend, SUM(sales) AS sales, SUM(orders) AS orders
    FROM public.ppc_performance
    WHERE source = 2 AND record_type IN ('campaign','ad')
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain
    ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
),
perf_dates AS (
    SELECT parent_id, MIN(date) AS start_date, MAX(date) AS last_active_date
    FROM public.ppc_performance
    WHERE source = 2 AND record_type IN ('campaign','ad')
    GROUP BY parent_id
),
top_listing AS (
    SELECT parent_id, ref_id FROM (
        SELECT parent_id, ref_id,
               ROW_NUMBER() OVER (PARTITION BY parent_id
                    ORDER BY SUM(spend) DESC NULLS LAST, SUM(sales) DESC NULLS LAST, ref_id) AS rn
        FROM public.ppc_performance
        WHERE source = 2 AND record_type = 'ad' AND ref_id IS NOT NULL AND ref_id <> '0'
        GROUP BY parent_id, ref_id
    ) r WHERE rn = 1
),
listing_detail AS (
    SELECT ref_id, sku, title FROM (
        SELECT ld.ref_id,
               COALESCE(NULLIF(ld.mapped_sku,''), NULLIF(ld.sku,'')) AS sku,
               NULLIF(ld.title,'') AS title,
               ROW_NUMBER() OVER (PARTITION BY ld.ref_id
                    ORDER BY (NULLIF(ld.title,'') IS NOT NULL) DESC, ld.is_child DESC NULLS LAST, ld.id) AS rn
        FROM public.listing_data ld
        WHERE ld.which_channel = 2 AND ld.wrong_sku = 0
    ) x WHERE rn = 1
),
calc AS (
    SELECT c.parent_id, c.ss_name, c.market_place, c.record_name, c.record_subtype, c.record_status, c.bid,
           tl.ref_id AS listing_id, ld.sku, ld.title,
           pd.start_date, pd.last_active_date,
           COALESCE(pm.impressions,0) AS impressions, COALESCE(pm.clicks,0) AS clicks,
           COALESCE(pm.spend,0) AS spend, COALESCE(pm.sales,0) AS sales, COALESCE(pm.orders,0) AS orders,
           CASE WHEN COALESCE(pm.sales,0)  > 0 THEN pm.spend / pm.sales * 100 END AS acos,
           CASE WHEN COALESCE(pm.spend,0)  > 0 THEN pm.sales / pm.spend       END AS roas,
           CASE WHEN COALESCE(pm.clicks,0) > 0 THEN pm.orders::numeric / pm.clicks * 100 END AS cvr
    FROM ebay_campaigns c
    LEFT JOIN perf_metrics   pm ON pm.parent_id = c.parent_id
    LEFT JOIN perf_dates     pd ON pd.parent_id = c.parent_id
    LEFT JOIN top_listing    tl ON tl.parent_id = c.parent_id
    LEFT JOIN listing_detail ld ON ld.ref_id    = tl.ref_id
)
SELECT
    parent_id,
    TO_CHAR(last_active_date,'YYYY-MM')                    AS month,
    COALESCE(ss_name,'Unknown')                           AS account,
    COALESCE(market_place,'Unknown')                      AS marketplace,
    COALESCE(NULLIF(record_name,''),'(Unnamed Campaign)') AS campaign_name,
    CASE record_subtype WHEN 'ON_SITE' THEN 'Advanced (CPC)'
                        WHEN 'COST_PER_SALE' THEN 'Standard (CPS)'
                        WHEN 'OFF_SITE' THEN 'Off-Site' END AS campaign_type,
    COALESCE(record_status,'unknown')                     AS campaign_status,
    COALESCE(listing_id,'N/A')                            AS listing_id,
    COALESCE(sku,'N/A')                                   AS sku,
    COALESCE(title,'N/A')                                 AS product_title,
    COALESCE(bid,0)::numeric(12,2)                        AS daily_budget,
    sales::numeric(14,2)                                  AS total_sales,
    orders::numeric(14,0)                                 AS order_qty,
    spend::numeric(14,2)                                  AS ad_spend,
    acos::numeric(12,2)                                   AS acos,
    roas::numeric(12,2)                                   AS roas,
    CASE WHEN clicks > 0 THEN (spend/clicks)::numeric(12,2) END           AS avg_cpc,
    clicks::bigint                                        AS clicks,
    impressions::bigint                                  AS impressions,
    CASE WHEN impressions > 0 THEN (clicks::numeric/impressions*100)::numeric(12,2) END AS ctr,
    cvr::numeric(12,2)                                    AS conversion_rate,
    CASE WHEN orders > 0 THEN (sales/orders)::numeric(12,2) END           AS aov,
    TO_CHAR(start_date,'YYYY-MM-DD')                      AS start_date,
    CASE
        WHEN spend = 0 OR sales = 0 OR clicks = 0                THEN 'Low'
        WHEN roas >= 8 AND acos <= 12 AND cvr >= 8               THEN 'High'
        WHEN roas >= 5 AND roas < 8 AND acos > 12 AND acos <= 20 THEN 'Medium'
        WHEN roas < 5 OR acos > 20                               THEN 'Low'
        ELSE 'Medium'
    END                                                   AS performance
FROM calc
ORDER BY ad_spend DESC;
"""

# Column order EXACTLY as the Requirement Document (parent_id excluded from display).
COLUMNS = [
    ("month",           "Month",              "text"),
    ("account",         "Account",            "text"),
    ("marketplace",     "Marketplace",        "text"),
    ("campaign_name",   "Campaign Name",      "text"),
    ("campaign_type",   "Campaign Type",      "text"),
    ("campaign_status", "Campaign Status",    "status"),
    ("listing_id",      "Listing ID",         "text"),
    ("sku",             "SKU",                "text"),
    ("product_title",   "Product Title",      "text"),
    ("daily_budget",    "Daily Budget (£)",   "money"),
    ("total_sales",     "Total Sales (£)",    "money"),
    ("order_qty",       "Order Qty",          "int"),
    ("ad_spend",        "Ad Spend (£)",       "money"),
    ("acos",            "ACOS (%)",           "pct"),
    ("roas",            "ROAS",               "num"),
    ("avg_cpc",         "Avg. CPC (£)",       "money"),
    ("clicks",          "Clicks",             "int"),
    ("impressions",     "Impressions",        "int"),
    ("ctr",             "CTR (%)",            "pct"),
    ("conversion_rate", "Conversion Rate (%)","pct"),
    ("aov",             "AOV (£)",            "money"),
    ("start_date",      "Start Date",         "date"),
    ("performance",     "Performance",        "perf"),
]

TOTALS_SQL = r"""
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.record_status
    FROM public.ppc p
    WHERE p.source = 2 AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) AS impressions, SUM(clicks) AS clicks,
           SUM(spend) AS spend, SUM(sales) AS sales, SUM(orders) AS orders
    FROM public.ppc_performance
    WHERE source = 2 AND record_type IN ('campaign','ad')
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain
    ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
)
SELECT
  count(*)                                                        AS campaigns,
  count(*) FILTER (WHERE c.record_status = 'running')             AS active,
  count(*) FILTER (WHERE c.record_status = 'paused')              AS paused,
  COALESCE(SUM(pm.spend),0)::numeric(16,2)                        AS spend,
  COALESCE(SUM(pm.sales),0)::numeric(16,2)                        AS sales,
  COALESCE(SUM(pm.orders),0)::numeric(16,0)                       AS orders,
  COALESCE(SUM(pm.clicks),0)::bigint                              AS clicks,
  COALESCE(SUM(pm.impressions),0)::bigint                         AS impressions
FROM ebay_campaigns c
LEFT JOIN perf_metrics pm ON pm.parent_id = c.parent_id;
"""

# Per-campaign monthly spend & sales (de-duplicated by authoritative grain) -> trend chart
MONTHLY_SQL = r"""
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) AS pref
  FROM public.ppc_performance
  WHERE source = 2 AND record_type IN ('campaign','ad')
  GROUP BY parent_id
)
SELECT pp.parent_id,
       TO_CHAR(pp.date,'YYYY-MM')          AS m,
       SUM(pp.spend)::numeric(14,2)        AS spend,
       SUM(pp.sales)::numeric(14,2)        AS sales
FROM public.ppc_performance pp
JOIN gp ON gp.parent_id = pp.parent_id
WHERE pp.source = 2
  AND ((gp.pref = 0 AND pp.record_type = 'campaign')
    OR (gp.pref = 1 AND pp.record_type = 'ad'))
GROUP BY pp.parent_id, m;
"""

# Today's spend = spend on the most recent activity date, de-duplicated by grain
TODAY_SQL = r"""
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) AS pref
  FROM public.ppc_performance
  WHERE source = 2 AND record_type IN ('campaign','ad')
  GROUP BY parent_id
),
last_day AS (
  SELECT MAX(date) AS d FROM public.ppc_performance
  WHERE source = 2 AND record_type IN ('campaign','ad')
)
SELECT (SELECT d FROM last_day) AS today_date,
       COALESCE(SUM(pp.spend),0)::numeric(14,2) AS today_spend
FROM public.ppc_performance pp
JOIN gp ON gp.parent_id = pp.parent_id
JOIN last_day l ON pp.date = l.d
WHERE pp.source = 2
  AND ((gp.pref = 0 AND pp.record_type = 'campaign')
    OR (gp.pref = 1 AND pp.record_type = 'ad'));
"""


def num(v):
    """Decimal -> float (2/none preserved); keep ints as int; pass through None/str."""
    if v is None:
        return None
    if isinstance(v, decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def main():
    url = os.environ["DATABASE_URL"]
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SELECT now()")
        generated_at = cur.fetchone()[0].isoformat()

        cur.execute(VALIDATED_SQL)
        raw = cur.fetchall()  # first col = parent_id, then 23 display cols

        cur.execute(TOTALS_SQL)
        t = cur.fetchone()
        sql_totals = {
            "campaigns": int(t[0]), "active": int(t[1]), "paused": int(t[2]),
            "spend": num(t[3]), "sales": num(t[4]), "orders": num(t[5]),
            "clicks": int(t[6]), "impressions": int(t[7]),
        }

        cur.execute(TODAY_SQL)
        td = cur.fetchone()
        today_date = td[0].isoformat() if td[0] else None
        today_spend = num(td[1])

        cur.execute(MONTHLY_SQL)
        monthly_map = {}
        months_set = set()
        for pid, m, sp, sa in cur.fetchall():
            months_set.add(m)
            monthly_map.setdefault(pid, {})[m] = [num(sp), num(sa)]

    # Build rows aligned with monthly vectors
    rows = []
    monthly = []
    for rec in raw:
        pid = rec[0]
        rows.append([num(v) for v in rec[1:]])   # drop parent_id from display payload
        monthly.append(monthly_map.get(pid, {}))

    months = sorted(months_set)
    date_min = months[0] if months else None
    date_max = months[-1] if months else None

    payload = {
        "meta": {
            "title": "eBay PPC Performance Dashboard",
            "generated_at": generated_at,          # Last Sync Time (DB clock)
            "reporting_month": date_max,           # latest activity month
            "date_min": date_min,
            "date_max": date_max,
            "months": months,
            "today_date": today_date,
            "today_spend": today_spend,
            "row_count": len(rows),
            "source_tables": ["public.ppc", "public.ppc_performance", "public.listing_data"],
            "currency_note": "Values are in each marketplace's native currency (GBP/EUR/USD); not FX-normalised.",
        },
        "sql_totals": sql_totals,
        "columns": [{"key": k, "label": l, "type": t} for (k, l, t) in COLUMNS],
        "rows": rows,
        "monthly": monthly,
    }

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* AUTO-GENERATED by export_data.py from production PostgreSQL. Do not edit by hand. */\n")
        f.write("window.DASHBOARD_DATA = ")
        f.write(body)
        f.write(";\n")

    # Console validation summary
    print("Wrote", OUT)
    print("rows          :", len(rows))
    print("sql_totals    :", json.dumps(sql_totals))
    print("today_date    :", today_date, "today_spend:", today_spend)
    print("months        :", date_min, "->", date_max, f"({len(months)})")
    print("file bytes    :", os.path.getsize(OUT))


if __name__ == "__main__":
    main()

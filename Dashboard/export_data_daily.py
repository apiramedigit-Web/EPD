#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_data_daily.py  --  REBUILT dataset for reporting-date filtering.

Instead of one aggregated row per campaign, this exports:
  - dim   : one dimension record per valid eBay campaign (name/account/marketplace/
            type/status/budget/listing/sku/title/start_date) — static attributes.
  - daily : per-campaign daily fact from public.ppc_performance.date, giving
            [dateIndex, impressions, clicks, spend, sales, orders] per active day.
  - dates : the sorted list of reporting dates (dateIndex refers into this).

The dashboard re-aggregates `daily` over the selected reporting period, so KPIs,
table, charts, export and performance counts all reflect the chosen reporting date
range (NOT campaign start date). Start Date remains a display-only dimension field.
"""
import os, json, decimal
import datetime as dt
import psycopg

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
SRC = 2  # eBay

DIM_SQL = """
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.ss_name, p.market_place,
           p.record_name, p.record_subtype, p.record_status, p.bid
    FROM public.ppc p
    WHERE p.source = %(src)s AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_dates AS (
    SELECT parent_id, MIN(date) AS start_date
    FROM public.ppc_performance
    WHERE source = %(src)s AND record_type IN ('campaign','ad')
    GROUP BY parent_id
),
top_listing AS (
    SELECT parent_id, ref_id FROM (
        SELECT parent_id, ref_id,
               ROW_NUMBER() OVER (PARTITION BY parent_id
                    ORDER BY SUM(spend) DESC NULLS LAST, SUM(sales) DESC NULLS LAST, ref_id) rn
        FROM public.ppc_performance
        WHERE source = %(src)s AND record_type='ad' AND ref_id IS NOT NULL AND ref_id <> '0'
        GROUP BY parent_id, ref_id
    ) r WHERE rn = 1
),
listing_detail AS (
    SELECT ref_id, sku, title FROM (
        SELECT ld.ref_id,
               COALESCE(NULLIF(ld.mapped_sku,''), NULLIF(ld.sku,'')) sku,
               NULLIF(ld.title,'') title,
               ROW_NUMBER() OVER (PARTITION BY ld.ref_id
                    ORDER BY (NULLIF(ld.title,'') IS NOT NULL) DESC, ld.is_child DESC NULLS LAST, ld.id) rn
        FROM public.listing_data ld WHERE ld.which_channel = 2 AND ld.wrong_sku = 0
    ) x WHERE rn = 1
),
order_title AS (
    -- eBay titles are absent from listing_data.title for ~98%% of items; fall back to
    -- the most frequent order-line title per item_id, with the trailing variant
    -- suffix "[...]" stripped. Restricted to the campaigns' top listings for speed.
    SELECT ref_id, title FROM (
        SELECT oii_item_id AS ref_id,
               regexp_replace(btrim(oii_item_title), '\\s*\\[[^\\]]*\\]\\s*$', '') AS title,
               ROW_NUMBER() OVER (PARTITION BY oii_item_id
                    ORDER BY count(*) DESC,
                             length(regexp_replace(btrim(oii_item_title),'\\s*\\[[^\\]]*\\]\\s*$','')) DESC) rn
        FROM public.order_item_info
        WHERE oii_item_id IN (SELECT ref_id FROM top_listing)
          AND NULLIF(btrim(oii_item_title),'') IS NOT NULL
        GROUP BY oii_item_id, regexp_replace(btrim(oii_item_title), '\\s*\\[[^\\]]*\\]\\s*$', '')
    ) z WHERE rn = 1
),
order_sku AS (
    -- Some promoted eBay item_ids are absent from listing_data entirely (no SKU there);
    -- fall back to the most frequent order-line SKU per item_id from order_item_info.
    SELECT ref_id, sku FROM (
        SELECT oii_item_id AS ref_id, btrim(oii_item_sku) AS sku,
               ROW_NUMBER() OVER (PARTITION BY oii_item_id
                    ORDER BY count(*) DESC, length(btrim(oii_item_sku)) ASC) rn
        FROM public.order_item_info
        WHERE oii_item_id IN (SELECT ref_id FROM top_listing)
          AND NULLIF(btrim(oii_item_sku),'') IS NOT NULL
        GROUP BY oii_item_id, btrim(oii_item_sku)
    ) z WHERE rn = 1
)
SELECT c.parent_id,
       COALESCE(c.ss_name,'Unknown'),
       COALESCE(c.market_place,'Unknown'),
       COALESCE(NULLIF(c.record_name,''),'(Unnamed Campaign)'),
       CASE c.record_subtype WHEN 'ON_SITE' THEN 'Advanced (CPC)'
                             WHEN 'COST_PER_SALE' THEN 'Standard (CPS)'
                             WHEN 'OFF_SITE' THEN 'Off-Site' END,
       COALESCE(c.record_status,'unknown'),
       COALESCE(tl.ref_id,'N/A'),
       COALESCE(ld.sku, os.sku, 'N/A'),
       COALESCE(ld.title, ot.title, 'N/A'),
       COALESCE(c.bid,0)::numeric(12,2),
       TO_CHAR(pd.start_date,'YYYY-MM-DD')
FROM ebay_campaigns c
LEFT JOIN perf_dates    pd ON pd.parent_id = c.parent_id
LEFT JOIN top_listing   tl ON tl.parent_id = c.parent_id
LEFT JOIN listing_detail ld ON ld.ref_id   = tl.ref_id
LEFT JOIN order_title    ot ON ot.ref_id   = tl.ref_id
LEFT JOIN order_sku      os ON os.ref_id   = tl.ref_id
ORDER BY c.parent_id;
"""

DAILY_SQL = """
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=%(src)s AND record_type IN ('campaign','ad')
  GROUP BY parent_id
)
SELECT pp.parent_id, pp.date,
       SUM(pp.impressions)::bigint, SUM(pp.clicks)::bigint,
       SUM(pp.spend)::numeric(14,2), SUM(pp.sales)::numeric(14,2), SUM(pp.orders)::numeric(14,0)
FROM public.ppc_performance pp JOIN gp ON gp.parent_id = pp.parent_id
WHERE pp.source=%(src)s
  AND ((gp.pref=0 AND pp.record_type='campaign') OR (gp.pref=1 AND pp.record_type='ad'))
GROUP BY pp.parent_id, pp.date;
"""

TOTALS_SQL = """
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.record_status
    FROM public.ppc p
    WHERE p.source=%(src)s AND p.record_main_type='campaign'
      AND p.record_subtype NOT IN ('','0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) impressions, SUM(clicks) clicks,
           SUM(spend) spend, SUM(sales) sales, SUM(orders) orders
    FROM public.ppc_performance WHERE source=%(src)s AND record_type IN ('campaign','ad')
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
)
SELECT count(*), count(*) FILTER (WHERE c.record_status='running'),
       count(*) FILTER (WHERE c.record_status='paused'),
       COALESCE(SUM(pm.spend),0)::numeric(16,2), COALESCE(SUM(pm.sales),0)::numeric(16,2),
       COALESCE(SUM(pm.orders),0)::numeric(16,0), COALESCE(SUM(pm.clicks),0)::bigint,
       COALESCE(SUM(pm.impressions),0)::bigint
FROM ebay_campaigns c LEFT JOIN perf_metrics pm ON pm.parent_id=c.parent_id;
"""

DIM_COLS = ["account","marketplace","campaign_name","campaign_type","campaign_status",
            "listing_id","sku","product_title","daily_budget","start_date"]

COLUMNS = [
    ("month","Month","text"),("account","Account","text"),("marketplace","Marketplace","text"),
    ("campaign_name","Campaign Name","text"),("campaign_type","Campaign Type","text"),
    ("campaign_status","Campaign Status","status"),("listing_id","Listing ID","text"),
    ("sku","SKU","text"),("product_title","Product Title","text"),
    ("daily_budget","Daily Budget (£)","money"),("total_sales","Total Sales (£)","money"),
    ("order_qty","Order Qty","int"),("ad_spend","Ad Spend (£)","money"),
    ("acos","ACOS (%)","pct"),("roas","ROAS","num"),("avg_cpc","Avg. CPC (£)","money"),
    ("clicks","Clicks","int"),("impressions","Impressions","int"),("ctr","CTR (%)","pct"),
    ("conversion_rate","Conversion Rate (%)","pct"),("aov","AOV (£)","money"),
    ("start_date","Start Date","date"),("performance","Performance","perf"),
]


def num(v):
    if v is None: return None
    if isinstance(v, decimal.Decimal):
        f = float(v); return int(f) if f.is_integer() else f
    if isinstance(v, (dt.date, dt.datetime)): return v.isoformat()
    return v


def main():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute("SELECT now()"); generated_at = cur.fetchone()[0].isoformat()

        cur.execute(DIM_SQL, {"src": SRC})
        dim_rows = cur.fetchall()
        pid_index = {}
        dim = []
        for i, r in enumerate(dim_rows):
            pid_index[r[0]] = i
            dim.append([num(v) for v in r[1:]])   # DIM_COLS order

        cur.execute(TOTALS_SQL, {"src": SRC})
        t = cur.fetchone()
        sql_totals = {"campaigns": int(t[0]), "active": int(t[1]), "paused": int(t[2]),
                      "spend": num(t[3]), "sales": num(t[4]), "orders": num(t[5]),
                      "clicks": int(t[6]), "impressions": int(t[7])}

        cur.execute(DAILY_SQL, {"src": SRC})
        fact = cur.fetchall()

    # build sorted date list + index
    all_dates = sorted({r[1].isoformat() for r in fact})
    date_index = {d: i for i, d in enumerate(all_dates)}

    daily = [[] for _ in dim]                     # aligned to dim
    chk = {"spend": 0.0, "sales": 0.0, "orders": 0, "clicks": 0, "impressions": 0}
    for pid, d, impr, clk, sp, sa, orr in fact:
        j = pid_index.get(pid)
        if j is None:
            continue                              # campaign not in valid dimension (e.g. junk subtype)
        di = date_index[d.isoformat()]
        impr = int(impr); clk = int(clk); sp = num(sp) or 0; sa = num(sa) or 0; orr = int(orr)
        daily[j].append([di, impr, clk, sp, sa, orr])
        chk["impressions"] += impr; chk["clicks"] += clk
        chk["spend"] += sp; chk["sales"] += sa; chk["orders"] += orr
    for lst in daily:
        lst.sort(key=lambda e: e[0])

    # integrity: daily-sum must reconcile with the independent DB campaign-level totals
    def close(a, b): return abs((a or 0) - (b or 0)) <= 0.05
    recon = all(close(chk[k], sql_totals[k]) for k in ("spend","sales","orders","clicks","impressions"))

    payload = {
        "meta": {
            "title": "eBay PPC Performance Dashboard",
            "generated_at": generated_at,
            "reporting_date_field": "public.ppc_performance.date",
            "date_min": all_dates[0], "date_max": all_dates[-1],
            "today_date": all_dates[-1],                 # reference "today" = latest reporting date
            "default_preset": "last30",
            "dates_count": len(all_dates),
            "source_tables": ["public.ppc","public.ppc_performance","public.listing_data"],
            "currency_note": "Values are in each marketplace's native currency (GBP/EUR/USD); not FX-normalised.",
        },
        "sql_totals": sql_totals,                        # full-window integrity check
        "columns": [{"key": k, "label": l, "type": t} for (k, l, t) in COLUMNS],
        "dim_cols": DIM_COLS,
        "dates": all_dates,
        "dim": dim,
        "daily": daily,
    }

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("/* AUTO-GENERATED by export_data_daily.py — per-campaign daily reporting facts. */\n")
        f.write("window.DASHBOARD_DATA = " + body + ";\n")
        f.write("window.dashboardData = window.DASHBOARD_DATA;\n")

    print("wrote", OUT, "bytes:", os.path.getsize(OUT))
    print("campaigns (dim):", len(dim), " active-with-daily:", sum(1 for d in daily if d))
    print("dates:", len(all_dates), all_dates[0], "->", all_dates[-1])
    print("daily-sum:", json.dumps({k: round(v,2) if isinstance(v,float) else v for k,v in chk.items()}))
    print("sql_totals:", json.dumps(sql_totals))
    print("RECONCILES (daily-sum == DB totals):", recon)
    if not recon:
        raise SystemExit("ABORT: daily facts do not reconcile with DB totals.")


if __name__ == "__main__":
    main()

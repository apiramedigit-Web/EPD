#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_dashboard.py — build one standalone dashboard HTML per ebay_priors user
for a given reporting month, from live PostgreSQL production data.

- Metrics are aggregated over the reporting month window only (previous month).
- Uses the same validated campaign-grain SQL (authoritative-grain de-dup, one row
  per campaign, no hardcoded values).
- Monthly Trend chart is fed a trailing 13-month series for context.
- The frontend (CSS/HTML/JS) is taken verbatim from ../dashboard.html; only the
  embedded data block and the header "Assigned User" line differ per file.
"""
import os, re, json, decimal, sys
import datetime as dt

import config

# ------------------------------------------------------------------ SQL
ROWS_SQL = """
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.ss_name, p.market_place,
           p.record_name, p.record_subtype, p.record_status, p.bid
    FROM public.ppc p
    WHERE p.source = %(src)s AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) impressions, SUM(clicks) clicks,
           SUM(spend) spend, SUM(sales) sales, SUM(orders) orders
    FROM public.ppc_performance
    WHERE source = %(src)s AND record_type IN ('campaign','ad')
      AND date BETWEEN %(m_start)s AND %(m_end)s
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain
    ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
),
perf_dates AS (
    SELECT parent_id, MIN(date) start_date, MAX(date) last_active_date
    FROM public.ppc_performance
    WHERE source = %(src)s AND record_type IN ('campaign','ad')
      AND date BETWEEN %(m_start)s AND %(m_end)s
    GROUP BY parent_id
),
top_listing AS (
    SELECT parent_id, ref_id FROM (
        SELECT parent_id, ref_id,
               ROW_NUMBER() OVER (PARTITION BY parent_id
                    ORDER BY SUM(spend) DESC NULLS LAST, SUM(sales) DESC NULLS LAST, ref_id) rn
        FROM public.ppc_performance
        WHERE source = %(src)s AND record_type='ad' AND ref_id IS NOT NULL AND ref_id <> '0'
          AND date BETWEEN %(m_start)s AND %(m_end)s
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
calc AS (
    SELECT c.parent_id, c.ss_name, c.market_place, c.record_name, c.record_subtype, c.record_status, c.bid,
           tl.ref_id listing_id, ld.sku, ld.title, pd.start_date,
           COALESCE(pm.impressions,0) impressions, COALESCE(pm.clicks,0) clicks,
           COALESCE(pm.spend,0) spend, COALESCE(pm.sales,0) sales, COALESCE(pm.orders,0) orders,
           CASE WHEN COALESCE(pm.sales,0) > 0 THEN pm.spend / pm.sales * 100 END acos,
           CASE WHEN COALESCE(pm.spend,0) > 0 THEN pm.sales / pm.spend       END roas,
           CASE WHEN COALESCE(pm.clicks,0)> 0 THEN pm.orders::numeric / pm.clicks * 100 END cvr
    FROM ebay_campaigns c
    LEFT JOIN perf_metrics   pm ON pm.parent_id = c.parent_id
    LEFT JOIN perf_dates     pd ON pd.parent_id = c.parent_id
    LEFT JOIN top_listing    tl ON tl.parent_id = c.parent_id
    LEFT JOIN listing_detail ld ON ld.ref_id    = tl.ref_id
)
SELECT
    parent_id,
    %(rmonth)s                                            AS month,
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

TOTALS_SQL = """
WITH ebay_campaigns AS (
    SELECT DISTINCT ON (p.parent_id) p.parent_id, p.record_status
    FROM public.ppc p
    WHERE p.source = %(src)s AND p.record_main_type = 'campaign'
      AND p.record_subtype NOT IN ('', '0')
      AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')
    ORDER BY p.parent_id, p.ppc_etl_id
),
perf_by_grain AS (
    SELECT parent_id, record_type,
           SUM(impressions) impressions, SUM(clicks) clicks,
           SUM(spend) spend, SUM(sales) sales, SUM(orders) orders
    FROM public.ppc_performance
    WHERE source = %(src)s AND record_type IN ('campaign','ad')
      AND date BETWEEN %(m_start)s AND %(m_end)s
    GROUP BY parent_id, record_type
),
perf_metrics AS (
    SELECT DISTINCT ON (parent_id) parent_id, impressions, clicks, spend, sales, orders
    FROM perf_by_grain
    ORDER BY parent_id, CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END
)
SELECT count(*) campaigns,
       count(*) FILTER (WHERE c.record_status='running') active,
       count(*) FILTER (WHERE c.record_status='paused')  paused,
       COALESCE(SUM(pm.spend),0)::numeric(16,2)  spend,
       COALESCE(SUM(pm.sales),0)::numeric(16,2)  sales,
       COALESCE(SUM(pm.orders),0)::numeric(16,0) orders,
       COALESCE(SUM(pm.clicks),0)::bigint        clicks,
       COALESCE(SUM(pm.impressions),0)::bigint   impressions
FROM ebay_campaigns c
LEFT JOIN perf_metrics pm ON pm.parent_id = c.parent_id;
"""

MONTHLY_SQL = """
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=%(src)s AND record_type IN ('campaign','ad')
  GROUP BY parent_id
)
SELECT pp.parent_id, TO_CHAR(pp.date,'YYYY-MM') m,
       SUM(pp.spend)::numeric(14,2), SUM(pp.sales)::numeric(14,2)
FROM public.ppc_performance pp JOIN gp ON gp.parent_id = pp.parent_id
WHERE pp.source=%(src)s
  AND ((gp.pref=0 AND pp.record_type='campaign') OR (gp.pref=1 AND pp.record_type='ad'))
  AND pp.date BETWEEN %(trend_start)s AND %(m_end)s
GROUP BY pp.parent_id, m;
"""

TODAY_SQL = """
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=%(src)s AND record_type IN ('campaign','ad')
  GROUP BY parent_id
)
SELECT COALESCE(SUM(pp.spend),0)::numeric(14,2)
FROM public.ppc_performance pp JOIN gp ON gp.parent_id = pp.parent_id
WHERE pp.source=%(src)s AND pp.date = %(m_end)s
  AND ((gp.pref=0 AND pp.record_type='campaign') OR (gp.pref=1 AND pp.record_type='ad'));
"""

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

PLACEHOLDER = "__ASSIGNED_USER__"
INJECT_TARGET = '            <span>Reporting Month: <b id="hdr-month">—</b></span>'
INJECT_REPL   = ('            <span>Assigned User : <b id="hdr-user">' + PLACEHOLDER + '</b></span>\n'
                 + INJECT_TARGET)
DATA_BLOCK_RE = re.compile(r"<script>\s*/\* ---- Embedded production data.*?</script>", re.S)


def _num(v):
    if v is None: return None
    if isinstance(v, decimal.Decimal):
        f = float(v); return int(f) if f.is_integer() else f
    if isinstance(v, (dt.date, dt.datetime)): return v.isoformat()
    return v


def build_payload(cur, rep):
    p = {"src": config.SOURCE_EBAY, "m_start": rep["window_start"], "m_end": rep["window_end"],
         "rmonth": rep["reporting_month"], "trend_start": rep["trend_start"]}

    cur.execute("SELECT now()")
    generated_at = cur.fetchone()[0].isoformat()

    cur.execute(ROWS_SQL, p)
    raw = cur.fetchall()

    cur.execute(TOTALS_SQL, p)
    t = cur.fetchone()
    sql_totals = {"campaigns": int(t[0]), "active": int(t[1]), "paused": int(t[2]),
                  "spend": _num(t[3]), "sales": _num(t[4]), "orders": _num(t[5]),
                  "clicks": int(t[6]), "impressions": int(t[7])}

    cur.execute(TODAY_SQL, p)
    today_spend = _num(cur.fetchone()[0])

    cur.execute(MONTHLY_SQL, p)
    mmap, months = {}, set()
    for pid, m, sp, sa in cur.fetchall():
        months.add(m); mmap.setdefault(pid, {})[m] = [_num(sp), _num(sa)]

    rows, monthly = [], []
    for rec in raw:
        pid = rec[0]
        rows.append([_num(v) for v in rec[1:]])
        monthly.append(mmap.get(pid, {}))

    months = sorted(months) or [rep["reporting_month"]]
    payload = {
        "meta": {
            "title": config.PROJECT_NAME,
            "generated_at": generated_at,
            "reporting_month": rep["reporting_month"],
            "reporting_label": rep["reporting_label"],
            "window_start": rep["window_start"], "window_end": rep["window_end"],
            "date_min": months[0], "date_max": rep["reporting_month"], "months": months,
            "today_date": rep["window_end"], "today_spend": today_spend,
            "row_count": len(rows), "source_tables": config.SOURCE_TABLES,
            "currency_note": config.CURRENCY_NOTE,
        },
        "sql_totals": sql_totals,
        "columns": [{"key": k, "label": l, "type": t} for (k, l, t) in COLUMNS],
        "rows": rows, "monthly": monthly,
    }
    return payload, sql_totals


def render_template(payload):
    """Inject fresh data into the verbatim frontend template."""
    tpl = open(config.TEMPLATE_HTML, encoding="utf-8").read()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")
    data_block = ("<script>\n/* Embedded production data — generated by automation/generate_dashboard.py */\n"
                  "window.DASHBOARD_DATA = " + data_json + ";\n"
                  "window.dashboardData = window.DASHBOARD_DATA;\n  </script>")
    if not DATA_BLOCK_RE.search(tpl):
        raise RuntimeError("Could not locate embedded data block in template.")
    tpl = DATA_BLOCK_RE.sub(lambda _m: data_block, tpl, count=1)
    if tpl.count(INJECT_TARGET) != 1:
        raise RuntimeError("Could not locate header inject target in template.")
    tpl = tpl.replace(INJECT_TARGET, INJECT_REPL, 1)   # add Assigned User line (with placeholder)
    return tpl


def generate(rep, version, log=print):
    config.ensure_dirs()
    with config.connect() as conn, conn.cursor() as cur:
        payload, sql_totals = build_payload(cur, rep)
    log(f"Fetched {payload['meta']['row_count']} campaigns for {rep['reporting_label']} "
        f"({rep['window_start']}..{rep['window_end']})")
    log(f"SQL totals: {json.dumps(sql_totals)}")

    template = render_template(payload)
    files = []
    for user in config.USERS:
        content = template.replace(PLACEHOLDER, user)
        fname = config.filename_for(rep["run_date"], user, version)
        fpath = os.path.join(config.OUTPUT_DIR, fname)
        with open(fpath, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        files.append({"user": user, "path": fpath, "name": fname, "bytes": os.path.getsize(fpath)})
        log(f"Generated {fname} ({os.path.getsize(fpath):,} bytes)")

    manifest = {"reporting": rep, "version": version, "sql_totals": sql_totals,
                "files": files, "meta": payload["meta"]}
    with open(os.path.join(config.OUTPUT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="reporting month YYYY-MM (default: previous month)")
    ap.add_argument("--version", type=int, default=999)
    a = ap.parse_args()
    rep = config.compute_reporting(dt.date.today(), a.month)
    m = generate(rep, a.version)
    print(json.dumps({"reporting": rep, "files": [f["name"] for f in m["files"]]}, indent=2))

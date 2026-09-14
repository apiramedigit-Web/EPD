#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_charts.py — reconcile the REAL rendered dashboard output (from
validate_harness.js) against the filtered SQL dataset (queried per reporting
window) and against the KPI totals. Prints a PASS/FAIL validation report.
"""
import os, json, csv, io
import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(HERE, "_harness_out.json"), encoding="utf-8"))

WINDOW_SQL = """
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=2 AND record_type IN ('campaign','ad') GROUP BY parent_id
),
per AS (
  SELECT pp.parent_id,
         SUM(pp.impressions) impr, SUM(pp.clicks) clk, SUM(pp.spend) sp, SUM(pp.sales) sa, SUM(pp.orders) orr
  FROM public.ppc_performance pp JOIN gp ON gp.parent_id=pp.parent_id
  WHERE pp.source=2 AND ((gp.pref=0 AND record_type='campaign') OR (gp.pref=1 AND record_type='ad'))
    AND pp.date BETWEEN %(f)s AND %(t)s
  GROUP BY pp.parent_id
)
SELECT COALESCE(SUM(sp),0)::numeric(16,2), COALESCE(SUM(sa),0)::numeric(16,2),
       COALESCE(SUM(orr),0)::numeric(16,0), COALESCE(SUM(clk),0)::bigint, COALESCE(SUM(impr),0)::bigint,
       COUNT(*) FILTER (WHERE sp>0 OR sa>0), COALESCE(MAX(sa),0)::numeric(16,2), COALESCE(MAX(sp),0)::numeric(16,2)
FROM per;
"""
MONTHS_SQL = """
WITH gp AS (
  SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=2 AND record_type IN ('campaign','ad') GROUP BY parent_id
)
SELECT DISTINCT TO_CHAR(pp.date,'YYYY-MM')
FROM public.ppc_performance pp JOIN gp ON gp.parent_id=pp.parent_id
WHERE pp.source=2 AND ((gp.pref=0 AND record_type='campaign') OR (gp.pref=1 AND record_type='ad'))
  AND pp.date BETWEEN %(f)s AND %(t)s ORDER BY 1;
"""
DIMSTATUS_SQL = """
WITH ec AS (
  SELECT DISTINCT ON (p.parent_id) p.record_status FROM public.ppc p
  WHERE p.source=2 AND p.record_main_type='campaign' AND p.record_subtype NOT IN ('','0')
    AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE') ORDER BY p.parent_id, p.ppc_etl_id)
SELECT count(*), count(*) FILTER (WHERE record_status='running'), count(*) FILTER (WHERE record_status='paused') FROM ec;
"""

def f(v): return None if v is None else float(v)
def eqm(a, b, tol=0.02): return abs((a or 0) - (b or 0)) <= tol
def eqi(a, b): return int(a or 0) == int(b or 0)

conn = psycopg.connect(os.environ["DATABASE_URL"]); cur = conn.cursor()
cur.execute(DIMSTATUS_SQL); tot_c, tot_active, tot_paused = cur.fetchone()

def db_window(fr, to):
    cur.execute(WINDOW_SQL, {"f": fr, "t": to}); r = cur.fetchone()
    cur.execute(MONTHS_SQL, {"f": fr, "t": to}); months = [x[0] for x in cur.fetchall()]
    return {"spend": f(r[0]), "sales": f(r[1]), "orders": int(r[2]), "clicks": int(r[3]), "impressions": int(r[4]),
            "activity": int(r[5]), "max_sales": f(r[6]), "max_spend": f(r[7]), "months": months}

results = {"KPI": [], "Charts": [], "Filters": [], "Export": [], "Pagination": [], "Search": [], "Table": []}
rows_report = []

for name, snap in H["presets"].items():
    fr, to = snap["window"]
    db = db_window(fr, to)
    k = snap["kpi"]; ch = snap["charts"]
    checks = []
    # KPI vs SQL
    checks += [
        ("campaigns==dim", eqi(k["campaigns"], tot_c)),
        ("active==dim", eqi(k["active"], tot_active)),
        ("paused==dim", eqi(k["paused"], tot_paused)),
        ("spend==SQL", eqm(k["spend"], db["spend"])),
        ("sales==SQL", eqm(k["sales"], db["sales"])),
        ("orders==SQL", eqi(k["orders"], db["orders"])),
        ("clicks==SQL", eqi(k["clicks"], db["clicks"])),
        ("impr==SQL", eqi(k["impressions"], db["impressions"])),
    ]
    kpi_ok = all(c for _, c in checks); results["KPI"].append(kpi_ok)
    # Charts vs SQL/KPI
    cch = [
        ("scatter pts==activity", eqi(ch["scatterPoints"], db["activity"])),
        ("perf donut sum==campaigns", eqi(sum(ch["perf"].values()), tot_c)),
        ("status donut sum==campaigns", eqi(sum(ch["status"].values()), tot_c)),
        ("topSales[0]==SQL max", (not ch["topSales"]) if db["max_sales"] == 0 else eqm(ch["topSales"][0], db["max_sales"], 0.5)),
        ("topSpend[0]==SQL max", (not ch["topSpend"]) if db["max_spend"] == 0 else eqm(ch["topSpend"][0], db["max_spend"], 0.5)),
        # trend labels are a subset of SQL months (axis labels every other month when >12 months)
        ("trend months⊆SQL", set(ch["trendMonths"]) <= set(db["months"]) and (len(ch["trendMonths"]) > 0 or db["spend"] == 0)),
    ]
    ch_ok = all(c for _, c in cch); results["Charts"].append(ch_ok)
    rows_report.append((name, fr, to, k, db, ch, kpi_ok, ch_ok, dict(checks), dict(cch)))

# Filters: reporting-date presets produce DIFFERENT results (not stale) + custom works
full = H["presets"]["custom_FULL"]["kpi"]; last7 = H["presets"]["last7"]["kpi"]
filters_ok = (full["spend"] != last7["spend"] and full["sales"] != last7["sales"])
results["Filters"] = [filters_ok]

# Stale check: the 5 PERIOD-DEPENDENT charts must differ Full vs Last7.
# Status Distribution is a DIMENSION attribute (period-independent) -> correctly identical.
PERIOD_CHARTS = ["scatter", "perf", "topSales", "topSpend", "trend"]
stale_ok = all(H["stale"][c]["differ"] for c in PERIOD_CHARTS)
status_period_independent = not H["stale"]["status"]["differ"]

# Table tests
tt = H["table_tests"]
# proper CSV parse (handles commas/quotes inside campaign names)
rdr = list(csv.reader(io.StringIO(tt["export"]["csvText"])))
hdr, body = rdr[0], rdr[1:]
spIdx, saIdx = hdr.index("Ad Spend (£)"), hdr.index("Total Sales (£)")
csv_rows = len(body)
csv_spend = round(sum(float(r[spIdx] or 0) for r in body), 2)
csv_sales = round(sum(float(r[saIdx] or 0) for r in body), 2)

search_ok = tt["search"]["pageRows"] > 0 and ("of " in tt["search"]["pageInfo"]) and \
            (int(tt["search"]["pageInfo"].split("of")[1].split("campaign")[0].replace(",", "").strip()) < tot_c)
pagination_ok = "26" in tt["pagination"]["page2"] and str(tot_c) in tt["pagination"]["page2"].replace(",", "")
sorting_ok = tt["sorting"]["isAscending"] and len(tt["sorting"]["firstNamesAsc"]) > 1
colvis_ok = tt["colVisibility"]["skuHiddenThenRestored"] is True
export_ok = csv_rows == tot_c and eqm(csv_spend, H["sql_totals"]["spend"]) and eqm(csv_sales, H["sql_totals"]["sales"])
results["Search"] = [search_ok]; results["Pagination"] = [pagination_ok]; results["Export"] = [export_ok]
results["Table"] = [sorting_ok and colvis_ok and pagination_ok and search_ok]

# ---------------- report ----------------
print("="*78)
print("  eBay PPC Dashboard — CHART / REPORTING-DATE FILTER VALIDATION")
print("  Reporting date field:", H["meta"]["reporting_date_field"], " | ref today:", H["meta"]["today"])
print("="*78)
print(f"\n{'Preset':<16}{'From':<12}{'To':<12}{'KPI Spend':>13}{'SQL Spend':>13}{'Scatter/Act':>13} {'KPI':>4} {'Chart':>6}")
print("-"*95)
for name, fr, to, k, db, ch, kpi_ok, ch_ok, kc, cc in rows_report:
    print(f"{name:<16}{fr:<12}{to:<12}{(k['spend'] or 0):>13,.2f}{(db['spend'] or 0):>13,.2f}"
          f"{str(ch['scatterPoints'])+'/'+str(db['activity']):>13} {'PASS' if kpi_ok else 'FAIL':>4} {'PASS' if ch_ok else 'FAIL':>6}")

print("\n--- Chart-values change across reporting periods (proof charts are filtered) ---")
for name in ["today","last7","lastmonth","custom_FULL"]:
    s = H["presets"][name]["charts"]
    print(f"  {name:<12} scatterPts={s['scatterPoints']:>4}  perf={s['perf']}  trendMonths={len(s['trendMonths'])}")

print("\n--- No stale/cached data: Full vs Last-7 chart output hashes ---")
for c, v in H["stale"].items():
    tag = "(period-independent: status is a dimension attribute — same by design)" if c == "status" else ""
    print(f"  {c:<10} differ={str(v['differ']):<5} {tag}")

def verdict(name, ok): print(f"  {name:<12}: {'PASS' if ok else 'FAIL'}")
print("\n================= VALIDATION REPORT =================")
verdict("KPI", all(results["KPI"]))
verdict("Table", all(results["Table"]))
verdict("Charts", all(results["Charts"]) and stale_ok)
verdict("Filters", all(results["Filters"]))
verdict("Export", all(results["Export"]))
verdict("Pagination", all(results["Pagination"]))
verdict("Search", all(results["Search"]))
print("----------------------------------------------------")
print("  Presets validated :", ", ".join(H["presets"].keys()))
print("  Stale-data check   :", "PASS (5 period charts differ Full vs Last7; status period-independent by design)" if (stale_ok and status_period_independent) else "FAIL")
print("  Export reconciles  :", f"{csv_rows} rows, spend {csv_spend:,.2f} == SQL {H['sql_totals']['spend']:,.2f}, sales {csv_sales:,.2f} == SQL {H['sql_totals']['sales']:,.2f}")
allpass = all(all(v) for v in results.values()) and stale_ok
print("  OVERALL            :", "ALL PASS" if allpass else "FAILURES PRESENT")
conn.close()

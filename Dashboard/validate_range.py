#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reconcile the REAL dashboard output (validate_range.js) for the two custom
reporting-date ranges against the production database, and report PASS/FAIL."""
import os, json, csv, io, subprocess
import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))

RANGES = [("2025-10-17", "2026-06-30"), ("2026-06-01", "2026-06-30")]

SQL = """
WITH ec AS (SELECT DISTINCT ON (p.parent_id) p.parent_id, p.record_status FROM public.ppc p
  WHERE p.source=2 AND p.record_main_type='campaign' AND p.record_subtype NOT IN ('','0')
    AND p.record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE') ORDER BY p.parent_id, p.ppc_etl_id),
gp AS (SELECT parent_id, MIN(CASE record_type WHEN 'campaign' THEN 0 ELSE 1 END) pref
  FROM public.ppc_performance WHERE source=2 AND record_type IN ('campaign','ad') GROUP BY parent_id),
per AS (SELECT pp.parent_id, SUM(pp.impressions) impr, SUM(pp.clicks) clk, SUM(pp.spend) sp, SUM(pp.sales) sa, SUM(pp.orders) orr
  FROM public.ppc_performance pp JOIN gp ON gp.parent_id=pp.parent_id
  WHERE pp.source=2 AND ((gp.pref=0 AND record_type='campaign') OR (gp.pref=1 AND record_type='ad'))
    AND pp.date BETWEEN %s AND %s GROUP BY pp.parent_id)
SELECT (SELECT count(*) FROM ec), (SELECT count(*) FROM ec WHERE record_status='running'), (SELECT count(*) FROM ec WHERE record_status='paused'),
  COALESCE(SUM(sp),0)::numeric(16,2), COALESCE(SUM(sa),0)::numeric(16,2), COALESCE(SUM(orr),0)::numeric(16,0),
  COALESCE(SUM(clk),0)::bigint, COALESCE(SUM(impr),0)::bigint, COUNT(*) FILTER (WHERE sp>0 OR sa>0),
  COALESCE(MAX(sa),0)::numeric(16,2), COALESCE(MAX(sp),0)::numeric(16,2) FROM per;
"""

def db(fr, to):
    cur.execute(SQL, (fr, to)); r = cur.fetchone()
    sp, sa, orr, clk, impr = float(r[3]), float(r[4]), int(r[5]), int(r[6]), int(r[7])
    return {"campaigns": int(r[0]), "active": int(r[1]), "paused": int(r[2]), "spend": sp, "sales": sa,
            "orders": orr, "clicks": clk, "impressions": impr, "active_in_range": int(r[8]),
            "max_sales": float(r[9]), "max_spend": float(r[10]),
            "acos": round(sp/sa*100, 2) if sa else None, "roas": round(sa/sp, 2) if sp else None,
            "ctr": round(clk/impr*100, 2) if impr else None, "cvr": round(orr/clk*100, 2) if clk else None,
            "aov": round(sa/orr, 2) if orr else None, "cpc": round(sp/clk, 2) if clk else None}

def parse_csv(text):
    rows = list(csv.reader(io.StringIO(text))); hdr = rows[0]; body = rows[1:]
    ix = {h: i for i, h in enumerate(hdr)}
    spend = round(sum(float(r[ix["Ad Spend (£)"]] or 0) for r in body), 2)
    sales = round(sum(float(r[ix["Total Sales (£)"]] or 0) for r in body), 2)
    orders = int(sum(float(r[ix["Order Qty"]] or 0) for r in body))
    clicks = int(sum(float(r[ix["Clicks"]] or 0) for r in body))
    impr = int(sum(float(r[ix["Impressions"]] or 0) for r in body))
    active = sum(1 for r in body if (float(r[ix["Ad Spend (£)"]] or 0) > 0 or float(r[ix["Total Sales (£)"]] or 0) > 0))
    start = {(r[ix["Campaign Name"]], r[ix["Account"]], r[ix["Marketplace"]]): r[ix["Start Date"]] for r in body}
    return {"rows": len(body), "spend": spend, "sales": sales, "orders": orders, "clicks": clicks,
            "impressions": impr, "active": active, "start": start, "cols": len(hdr)}

# run the real dashboard harness
H = json.loads(subprocess.check_output(["node", os.path.join(HERE, "validate_range.js")]))

conn = psycopg.connect(os.environ["DATABASE_URL"]); cur = conn.cursor()
DB = {"range1": db(*RANGES[0]), "range2": db(*RANGES[1])}
CSVP = {"range1": parse_csv(H["range1"]["csvText"]), "range2": parse_csv(H["range2"]["csvText"])}

def eqm(a, b, t=0.02): return abs((a or 0)-(b or 0)) <= t
def eqi(a, b): return int(a or 0) == int(b or 0)
def gm(v): return None if v in (None, "—", "") else float(str(v).replace("£", "").replace(",", "").replace("%", ""))

report, mism = {}, []
for rk, (fr, to) in zip(["range1", "range2"], RANGES):
    k = H[rk]["kpi"]; d = DB[rk]; c = CSVP[rk]
    def cmp(name, dash, sql, integer=False):
        ok = eqi(dash, sql) if integer else eqm(gm(dash), sql)
        if not ok: mism.append(f"{rk} {name}: dashboard={dash} vs SQL={sql}")
        return ok
    kpi = all([
        cmp("Total Campaigns", k["campaigns"], d["campaigns"], True),
        cmp("Active", k["active"], d["active"], True),
        cmp("Paused", k["paused"], d["paused"], True),
        cmp("Ad Spend", k["spend"], d["spend"]),
        cmp("Sales", k["sales"], d["sales"]),
        cmp("Orders", k["orders"], d["orders"], True),
        cmp("Clicks", k["clicks"], d["clicks"], True),
        cmp("Impressions", k["impressions"], d["impressions"], True),
        cmp("ACOS", gm(k["acos"]), d["acos"]), cmp("ROAS", gm(k["roas"]), d["roas"]),
        cmp("CTR", gm(k["ctr"]), d["ctr"]), cmp("CVR", gm(k["cvr"]), d["cvr"]),
        cmp("AOV", gm(k["aov"]), d["aov"]), cmp("CPC", gm(k["cpc"]), d["cpc"]),
    ])
    # window filters by reporting date -> csv metrics == SQL and == KPI
    exp = eqi(c["rows"], d["campaigns"]) and eqm(c["spend"], d["spend"]) and eqm(c["sales"], d["sales"]) \
          and eqi(c["active"], d["active_in_range"])
    if c["rows"] != d["campaigns"]: mism.append(f"{rk} export rows {c['rows']} != {d['campaigns']}")
    if not eqm(c["spend"], d["spend"]): mism.append(f"{rk} export spend {c['spend']} != {d['spend']}")
    # charts reconcile with SQL
    ch = H[rk]["charts"]
    chart = eqi(ch["scatterPts"], d["active_in_range"]) and sum(ch["perf"].values()) == d["campaigns"] \
            and (not ch["topSales"] or eqm(ch["topSales"][0], d["max_sales"], 0.5)) \
            and (not ch["topSpend"] or eqm(ch["topSpend"][0], d["max_spend"], 0.5))
    # export filename carries the range
    dl = H[rk]["downloadName"]; fname_ok = fr in dl and to in dl
    report[rk] = {"kpi": kpi, "export": exp, "chart": chart, "fname_ok": fname_ok, "dl": dl,
                  "csv": c, "db": d, "dashKPI": k, "chartsVals": ch}

# start_date unchanged across the two ranges
s1, s2 = CSVP["range1"]["start"], CSVP["range2"]["start"]
common = set(s1) & set(s2)
start_unchanged = all(s1[k] == s2[k] for k in common) and len(common) > 0
start_samples = [(k[0][:34], s1[k]) for k in list(common)[:4]]

# charts refresh: baseline vs range1, range1 vs range2 (5 period charts differ; status same)
PERIOD = ["scatter", "perf", "topSales", "topSpend", "trend"]
b, r1, r2 = H["baseline"]["charts"]["hash"], H["range1"]["charts"]["hash"], H["range2"]["charts"]["hash"]
refresh_b_r1 = all(b[c] != r1[c] for c in PERIOD)
refresh_r1_r2 = all(r1[c] != r2[c] for c in PERIOD)
status_same = (r1["status"] == r2["status"])

# ---------------- print ----------------
def L(s=""): print(s)
L("="*86); L("  DATE RANGE FILTER VALIDATION — REAL DASHBOARD vs PRODUCTION DB"); L("  Reporting date field: " + H["meta"]["reporting_date_field"]); L("="*86)
for rk, (fr, to) in zip(["range1", "range2"], RANGES):
    d = report[rk]["db"]; k = report[rk]["dashKPI"]; c = report[rk]["csv"]
    L(f"\n--- {rk.upper()}  {fr} -> {to}  (report period: {H[rk]['reportPeriod']}) ---")
    L(f"  {'Metric':<20}{'Dashboard':>18}{'Production SQL':>18}{'Match':>8}")
    def row(nm, dash, sql):
        ok = "OK" if (eqm(gm(dash), gm(sql)) if not isinstance(sql, int) else eqi(dash, sql)) else "MISMATCH"
        L(f"  {nm:<20}{str(dash):>18}{str(sql):>18}{ok:>8}")
    row("Total Campaigns", k["campaigns"], d["campaigns"]); row("Active Campaigns", k["active"], d["active"]); row("Paused Campaigns", k["paused"], d["paused"])
    row("Ad Spend (£)", k["spend"], d["spend"]); row("Sales (£)", k["sales"], d["sales"]); row("Orders", k["orders"], d["orders"])
    row("Clicks", k["clicks"], d["clicks"]); row("Impressions", k["impressions"], d["impressions"])
    row("ACOS (%)", k["acos"], d["acos"]); row("ROAS", k["roas"], d["roas"]); row("CTR (%)", k["ctr"], d["ctr"])
    row("Conversion Rate (%)", k["cvr"], d["cvr"]); row("AOV (£)", k["aov"], d["aov"]); row("Avg CPC (£)", k["cpc"], d["cpc"])
    L(f"  Export: {c['rows']} rows (all campaigns) | active-in-range {c['active']} == SQL {d['active_in_range']} | "
      f"spend £{c['spend']:,.2f} == SQL £{d['spend']:,.2f} | sales £{c['sales']:,.2f} == SQL £{d['sales']:,.2f}")
    L(f"  Export filename: {report[rk]['dl']}  (contains range: {report[rk]['fname_ok']})")
    L(f"  Charts: scatterPts {report[rk]['chartsVals']['scatterPts']} == active-in-range {d['active_in_range']} | "
      f"perf {report[rk]['chartsVals']['perf']} | topSales#1 £{(report[rk]['chartsVals']['topSales'] or [0])[0]:,.2f} == SQL max £{d['max_sales']:,.2f}")

L("\n--- Charts refresh (output hash changes) ---")
L(f"  baseline(last30) -> range1 : 5 period charts differ = {refresh_b_r1}")
L(f"  range1 -> range2           : 5 period charts differ = {refresh_r1_r2}")
L(f"  status distribution same across ranges (period-independent) = {status_same}")
L("\n--- Start Date column unchanged across ranges ---")
L(f"  compared {len(common)} common campaigns; identical start_date = {start_unchanged}")
for nm, sd in start_samples: L(f"    {nm:<36} Start Date={sd}")

L("\n================= FINAL REPORT =================")
def V(nm, ok): L(f"  {nm:<22}: {'PASS' if ok else 'FAIL'}")
kpi_all = report["range1"]["kpi"] and report["range2"]["kpi"]
exp_all = report["range1"]["export"] and report["range2"]["export"] and report["range1"]["fname_ok"] and report["range2"]["fname_ok"]
chart_all = report["range1"]["chart"] and report["range2"]["chart"] and refresh_b_r1 and refresh_r1_r2
tbl_all = report["range1"]["csv"]["active"] == report["range1"]["db"]["active_in_range"] and report["range2"]["csv"]["active"] == report["range2"]["db"]["active_in_range"]
range_all = (report["range1"]["dashKPI"]["spend"] != report["range2"]["dashKPI"]["spend"])
sql_all = kpi_all and exp_all
V("Date Range Filter", range_all); V("KPI Reconciliation", kpi_all); V("Campaign Table", tbl_all)
V("Charts", chart_all); V("Export", exp_all); V("Start Date Column", start_unchanged); V("SQL Reconciliation", sql_all)
L("-"*48)
L("  Mismatches: " + ("NONE" if not mism else ""))
for x in mism: L("    - " + x)
L("  OVERALL: " + ("ALL PASS" if (range_all and kpi_all and tbl_all and chart_all and exp_all and start_unchanged and sql_all and not mism) else "SEE MISMATCHES"))
conn.close()

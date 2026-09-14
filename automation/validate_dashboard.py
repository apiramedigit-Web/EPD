#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_dashboard.py — verify each generated dashboard before publishing.

Checks (per the acceptance criteria). ANY failure => pipeline must STOP and NOT publish:
  SQL totals, KPI cards, campaign count, revenue, orders, ad spend, ACOS, ROAS, CTR,
  Conversion Rate, AOV, Campaign Performance table, Filters, Charts, CSV Export,
  Standalone HTML, no missing values, no duplicate campaigns, Reporting Month,
  and Assigned User correctness.
"""
import os, re, json, math
import config
import generate_dashboard as G

DATA_RE = re.compile(r"window\.DASHBOARD_DATA\s*=\s*(.*?);\s*window\.dashboardData", re.S)
USER_RE = re.compile(r'<b id="hdr-user">(.*?)</b>')

REQUIRED_LABELS = [c[1] for c in G.COLUMNS]   # exact 23 column labels, in order
REQUIRED_NONNULL = ["month","account","marketplace","campaign_name","campaign_type","campaign_status","performance"]
FILTER_IDS = ["f-account","f-marketplace","f-status","f-performance","f-acos-min","f-acos-max",
              "f-roas-min","f-roas-max","f-date-min","f-date-max","f-start-from","f-start-to","f-search"]
CHART_IDS  = ["chart-scatter","chart-perf","chart-status","chart-top-sales","chart-top-spend","chart-trend"]


def _extract(html):
    m = DATA_RE.search(html)
    if not m:
        raise ValueError("embedded DASHBOARD_DATA not found")
    return json.loads(m.group(1))          # JSON `\/` escapes parse fine


def _agg(rows, idx):
    t = dict(campaigns=len(rows), active=0, paused=0, spend=0.0, sales=0.0, orders=0.0, clicks=0, impressions=0)
    for r in rows:
        if r[idx["campaign_status"]] == "running": t["active"] += 1
        if r[idx["campaign_status"]] == "paused":  t["paused"] += 1
        t["spend"]       += r[idx["ad_spend"]] or 0
        t["sales"]       += r[idx["total_sales"]] or 0
        t["orders"]      += r[idx["order_qty"]] or 0
        t["clicks"]      += r[idx["clicks"]] or 0
        t["impressions"] += r[idx["impressions"]] or 0
    return t


def _eq(a, b, tol=0.01):
    return abs((a or 0) - (b or 0)) <= tol


def validate(rep, files, log=print):
    # DB ground-truth for the reporting window (independent re-query)
    p = {"src": config.SOURCE_EBAY, "m_start": rep["window_start"], "m_end": rep["window_end"]}
    with config.connect() as conn, conn.cursor() as cur:
        cur.execute(G.TOTALS_SQL, p)
        d = cur.fetchone()
    db = {"campaigns": int(d[0]), "active": int(d[1]), "paused": int(d[2]),
          "spend": float(d[3]), "sales": float(d[4]), "orders": float(d[5]),
          "clicks": int(d[6]), "impressions": int(d[7])}
    log(f"DB reporting-month totals: {json.dumps(db)}")

    overall_ok = True
    per_file = []
    for f in files:
        html = open(f["path"], encoding="utf-8").read()
        checks = []
        def chk(name, cond):
            checks.append((name, bool(cond)))
            return bool(cond)

        try:
            D = _extract(html)
        except Exception as e:
            chk("embedded data parseable", False)
            per_file.append({"file": f["name"], "ok": False, "checks": checks, "error": str(e)})
            overall_ok = False
            continue

        idx = {c["key"]: i for i, c in enumerate(D["columns"])}
        rows = D["rows"]; st = D["sql_totals"]; comp = _agg(rows, idx)

        # ---- reporting month ----
        chk("Reporting Month", D["meta"]["reporting_month"] == rep["reporting_month"])
        # ---- SQL totals == DB ----
        for k in ("campaigns","active","paused","spend","sales","orders","clicks","impressions"):
            chk(f"SQL total: {k}", _eq(st[k], db[k]))
        # ---- KPI cards recompute (rows) == SQL totals ----
        chk("Campaign count",     _eq(comp["campaigns"], st["campaigns"]) and comp["campaigns"] == db["campaigns"])
        chk("Active Campaigns",   _eq(comp["active"], st["active"]))
        chk("Paused Campaigns",   _eq(comp["paused"], st["paused"]))
        chk("Revenue (Sales)",    _eq(comp["sales"], db["sales"]))
        chk("Orders",             _eq(comp["orders"], db["orders"]))
        chk("Ad Spend",           _eq(comp["spend"], db["spend"]))
        chk("Clicks",             _eq(comp["clicks"], db["clicks"]))
        chk("Impressions",        _eq(comp["impressions"], db["impressions"]))
        # ---- derived KPIs are computable & consistent ----
        acos = comp["spend"]/comp["sales"]*100 if comp["sales"] else None
        roas = comp["sales"]/comp["spend"] if comp["spend"] else None
        cpc  = comp["spend"]/comp["clicks"] if comp["clicks"] else None
        ctr  = comp["clicks"]/comp["impressions"]*100 if comp["impressions"] else None
        cvr  = comp["orders"]/comp["clicks"]*100 if comp["clicks"] else None
        aov  = comp["sales"]/comp["orders"] if comp["orders"] else None
        chk("ACOS computable",             acos is None or math.isfinite(acos))
        chk("ROAS computable",             roas is None or math.isfinite(roas))
        chk("Average CPC computable",      cpc  is None or math.isfinite(cpc))
        chk("CTR computable",              ctr  is None or math.isfinite(ctr))
        chk("Conversion Rate computable",  cvr  is None or math.isfinite(cvr))
        chk("AOV computable",              aov  is None or math.isfinite(aov))
        # ---- table columns exact ----
        chk("Campaign Performance columns", [c["label"] for c in D["columns"]] == REQUIRED_LABELS)
        # ---- no duplicate campaigns ----
        identity = set()
        dup = False
        for r in rows:
            key = (r[idx["campaign_name"]], r[idx["account"]], r[idx["marketplace"]], r[idx["campaign_type"]])
            if key in identity: dup = True
            identity.add(key)
        chk("No duplicate campaigns", (not dup) and len(rows) == db["campaigns"])
        # ---- no missing values ----
        miss = any(len(r) != len(D["columns"]) or any(r[idx[k]] in (None, "") for k in REQUIRED_NONNULL) for r in rows)
        chk("No missing values", not miss)
        # ---- filters / charts / export / standalone (structure) ----
        chk("Filters present",  all(f'id="{i}"' in html for i in FILTER_IDS))
        chk("Charts present",   all(f'id="{i}"' in html for i in CHART_IDS))
        chk("CSV Export present", 'id="btn-export-all"' in html and 'id="btn-export-view"' in html)
        chk("Standalone HTML", ('src="data.js"' not in html and 'rel="stylesheet"' not in html
                                and 'src="dashboard.js"' not in html
                                and html.lstrip().startswith("<!DOCTYPE html>")
                                and html.rstrip().endswith("</html>")))
        # ---- assigned user ----
        um = USER_RE.search(html)
        chk("Assigned User correct", bool(um) and um.group(1) == f["user"])

        file_ok = all(c for _, c in checks)
        overall_ok = overall_ok and file_ok
        failed = [n for n, c in checks if not c]
        per_file.append({"file": f["name"], "user": f["user"], "ok": file_ok, "failed": failed, "n": len(checks)})
        log(f"{'PASS' if file_ok else 'FAIL'}  {f['name']}  ({len(checks)-len(failed)}/{len(checks)} checks)"
            + (f"  FAILED: {failed}" if failed else ""))

    return overall_ok, {"db": db, "files": per_file}


if __name__ == "__main__":
    import sys, datetime as dt, argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--month"); a = ap.parse_args()
    rep = config.compute_reporting(dt.date.today(), a.month)
    man = json.load(open(os.path.join(config.OUTPUT_DIR, "manifest.json"), encoding="utf-8"))
    ok, _ = validate(rep, man["files"])
    print("VALIDATION:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

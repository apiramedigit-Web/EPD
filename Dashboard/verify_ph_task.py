#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Read-only verification: prove all 4 ph_task rows hold the LATEST dashboard build."""
import os, hashlib, re
import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "dashboard.html")

TASKS = {
    395: ("epd_Thinesh_ebay_ppc_performance_2026-06",  "Thinesh"),
    396: ("epd_Jarsini_ebay_ppc_performance_2026-06",  "Jarsini"),
    397: ("epd_kobiga_ebay_ppc_performance_2026-06",   "kobiga"),
    398: ("epd_powsteena_ebay_ppc_performance_2026-06","powsteena"),
}
PLACEHOLDER   = "__ASSIGNED_USER__"
INJECT_TARGET = '<span>Reporting Period: <b id="hdr-month">—</b></span>'
INJECT_REPL   = ('<span>Assigned User : <b id="hdr-user">' + PLACEHOLDER + '</b></span>\n            '
                 + INJECT_TARGET)

base = open(BASE, encoding="utf-8").read()
base_sha = hashlib.sha256(base.encode("utf-8")).hexdigest()
template = base.replace(INJECT_TARGET, INJECT_REPL, 1)
gen = re.search(r'"generated_at":"([^"]+)"', base)
data_gen = gen.group(1) if gen else "?"

# expected per-user SHA from the CURRENT on-disk build
expect = {}
for rid,(tid,user) in TASKS.items():
    c = template.replace(PLACEHOLDER, user)
    expect[rid] = (hashlib.sha256(c.encode("utf-8")).hexdigest(), len(c))

print("current on-disk dashboard.html bytes:", os.path.getsize(BASE))
print("current base sha256                :", base_sha)
print("embedded data generated_at         :", data_gen)
print()

with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    cur.execute("SELECT current_database()")
    print("connected DB:", cur.fetchone()[0], "\n")
    cur.execute("""
        SELECT id, assigned_user,
               length(html_content),
               encode(sha256(convert_to(html_content,'UTF8')),'hex'),
               (html_content LIKE '%%id="f-campaign-type"%%'),
               (html_content LIKE '%%FILTERS.campaignType && r.campaign_type%%'),
               (html_content LIKE '%%>N/A<%%'),
               (position(%s in html_content) > 0),
               updated_at
        FROM tech_team_outputs.ph_task WHERE id = ANY(%s) ORDER BY id
    """, (data_gen, list(TASKS)))
    rows = cur.fetchall()

allok = True
print("{:<5} | {:<10} | {:<9} | {:<9} | {:<8} | {:<8} | {:<7} | {:<9} | {}".format(
      "id","user","sha_match","len_match","CT_html","CT_js","no_NA","data_ts","updated_at"))
print("-"*118)
for rid,user,clen,sha,ct_html,ct_js,na,data_ts,uat in rows:
    esha,elen = expect[rid]
    sm, lm = sha==esha, clen==elen
    latest = sm and lm and ct_html and ct_js and (not na) and data_ts
    allok &= latest
    print("{:<5} | {:<10} | {:<9} | {:<9} | {:<8} | {:<8} | {:<7} | {:<9} | {}".format(
        rid, user, str(sm), str(lm), str(ct_html), str(ct_js), str(not na), str(data_ts),
        uat.strftime("%Y-%m-%d %H:%M:%S%z")))

print("\nRESULT:", "PASS — all 4 rows hold the identical latest validated build"
                   if allok else "FAIL — at least one row differs from the current build")

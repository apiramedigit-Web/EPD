#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export  SELECT * FROM tech_team_outputs.ph_task WHERE project_code='epd' ORDER BY id
to CSV with EVERY column exactly as stored, including the complete html_content.
Then round-trip verify that the CSV holds the full html_content (SHA-256 match).
"""
import os, csv, hashlib, sys
import datetime as dt
import psycopg

csv.field_size_limit(50_000_000)   # html_content fields are ~378 KB, well over the 128 KB default

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "epd_ph_task_export_2026-07-20.csv")
SQL  = "SELECT * FROM tech_team_outputs.ph_task WHERE project_code = 'epd' ORDER BY id;"

def cell(v):
    if v is None:
        return ""                      # NULL -> empty (actual stored value)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    return str(v)

def main():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(SQL)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
        hi = cols.index("html_content")
        # DB-side ground-truth digests for html_content
        db_sha = {}
        for r in rows:
            cur.execute("SELECT encode(sha256(convert_to(html_content,'UTF8')),'hex'), length(html_content) "
                        "FROM tech_team_outputs.ph_task WHERE id=%s", (r[0],))
            db_sha[r[0]] = cur.fetchone()

    # write CSV with all columns, full html_content
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([cell(v) for v in r])

    # round-trip verify: read CSV back, hash html_content per row, compare to DB
    with open(OUT, "r", encoding="utf-8-sig", newline="") as f:
        rd = list(csv.reader(f))
    hdr, body = rd[0], rd[1:]
    ci = hdr.index("html_content"); idi = hdr.index("id")

    print("columns:", cols)
    print("total rows:", len(rows))
    print("file path :", OUT)
    print("file size :", os.path.getsize(OUT), "bytes")
    print("\nper-row html_content completeness:")
    all_ok = True
    for br in body:
        rid = int(br[idi])
        csv_html = br[ci]
        csv_sha = hashlib.sha256(csv_html.encode("utf-8")).hexdigest()
        dbsha, dblen = db_sha[rid]
        ok = (csv_sha == dbsha) and (len(csv_html) == dblen)
        all_ok = all_ok and ok
        print(f"  id {rid}: csv_chars={len(csv_html)} db_chars={dblen} "
              f"sha_match={csv_sha==dbsha} "
              f"starts_with_doctype={csv_html.lstrip().startswith('<!DOCTYPE html>')} "
              f"ends_with_html={csv_html.rstrip().endswith('</html>')} -> {'OK' if ok else 'FAIL'}")
    print("\nALL html_content COMPLETE & VERIFIED:", all_ok)

if __name__ == "__main__":
    main()

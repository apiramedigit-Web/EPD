#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run the EXACT 17-column SELECT for project_code='epd' and export every returned
column (including the complete html_content) to CSV, then round-trip verify.
"""
import os, csv, hashlib
import datetime as dt
import psycopg

csv.field_size_limit(50_000_000)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "epd_ph_task_export_2026-07-20.csv")

SQL = """
SELECT
      id, project_name, project_code, task_name, task_id, team, developer,
      assigned_user, html_content, description, phase_level, version_level,
      version_status, action_took_by, action_took_date_time, created_at, updated_at
FROM tech_team_outputs.ph_task
WHERE project_code = 'epd'
ORDER BY id;
"""

def cell(v):
    if v is None:
        return ""
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    return str(v)

def main():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
        cur.execute(SQL)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
        hi = cols.index("html_content"); idi = cols.index("id")
        db_sha = {}
        for r in rows:
            cur.execute("SELECT encode(sha256(convert_to(html_content,'UTF8')),'hex'), length(html_content) "
                        "FROM tech_team_outputs.ph_task WHERE id=%s", (r[idi],))
            db_sha[r[idi]] = cur.fetchone()

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([cell(v) for v in r])

    with open(OUT, "r", encoding="utf-8-sig", newline="") as f:
        rd = list(csv.reader(f))
    hdr, body = rd[0], rd[1:]
    ci = hdr.index("html_content"); idx = hdr.index("id")

    print("columns exported (in query order):")
    print("  " + ", ".join(cols))
    print("total rows:", len(rows))
    print("file path :", OUT)
    print("file size :", os.path.getsize(OUT), "bytes")
    print("\nper-row html_content completeness:")
    all_ok = True
    for br in body:
        rid = int(br[idx]); html = br[ci]
        sha = hashlib.sha256(html.encode("utf-8")).hexdigest()
        dbsha, dblen = db_sha[rid]
        ok = (sha == dbsha) and (len(html) == dblen)
        all_ok = all_ok and ok
        print(f"  id {rid}: csv_chars={len(html)} db_chars={dblen} sha_match={sha==dbsha} "
              f"doctype_start={html.lstrip().startswith('<!DOCTYPE html>')} "
              f"html_end={html.rstrip().endswith('</html>')} -> {'OK' if ok else 'FAIL'}")
    print("\nALL html_content COMPLETE & VERIFIED:", all_ok)

if __name__ == "__main__":
    main()

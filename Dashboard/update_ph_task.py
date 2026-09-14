#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
update_ph_task.py — push the LATEST rebuilt dashboard.html into the existing
tech_team_outputs.ph_task rows for the eBay PPC Performance Dashboard task.

- Updates the 4 existing ebay_priors rows in place (no duplicates).
- Re-injects each user's "Assigned User" header line (per existing convention),
  adapted to the current 'Reporting Period' header string.
- Sets html_content = latest build, updated_at = now().  No other columns touched.
- Verifies each stored row by SHA-256 against the per-user source before commit.
"""
import os, sys, hashlib
import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "dashboard.html")

# task_id -> assigned_user  (the 4 existing rows, ids 395-398)
TASKS = {
    "epd_Thinesh_ebay_ppc_performance_2026-06":   "Thinesh",
    "epd_Jarsini_ebay_ppc_performance_2026-06":   "Jarsini",
    "epd_kobiga_ebay_ppc_performance_2026-06":     "kobiga",
    "epd_powsteena_ebay_ppc_performance_2026-06":  "powsteena",
}

PLACEHOLDER   = "__ASSIGNED_USER__"
INJECT_TARGET = '<span>Reporting Period: <b id="hdr-month">—</b></span>'
INJECT_REPL   = ('<span>Assigned User : <b id="hdr-user">' + PLACEHOLDER + '</b></span>\n            '
                 + INJECT_TARGET)

UPDATE_SQL = """
UPDATE tech_team_outputs.ph_task
   SET html_content = %(html_content)s,
       updated_at   = now()
 WHERE task_id = %(task_id)s
RETURNING id, updated_at;
"""
VERIFY_SQL = """
SELECT id, assigned_user, assigned_user_team, version_level, version_status,
       length(html_content) AS char_len,
       encode(sha256(convert_to(html_content,'UTF8')),'hex') AS sha256,
       created_at, updated_at
FROM tech_team_outputs.ph_task WHERE id = %s;
"""

def main():
    base = open(BASE, encoding="utf-8").read()
    if base.count(INJECT_TARGET) != 1:
        sys.exit(f"ABORT: header inject target found {base.count(INJECT_TARGET)} times (need 1).")
    template = base.replace(INJECT_TARGET, INJECT_REPL, 1)
    if template.count(PLACEHOLDER) != 1:
        sys.exit("ABORT: placeholder injection failed.")

    base_sha = hashlib.sha256(base.encode("utf-8")).hexdigest()
    url = os.environ["DATABASE_URL"]
    results = []
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        db = cur.fetchone()[0]
        print("connected DB:", db)
        print("base dashboard.html bytes:", os.path.getsize(BASE), " sha256:", base_sha)

        for task_id, user in TASKS.items():
            content  = template.replace(PLACEHOLDER, user)
            src_sha  = hashlib.sha256(content.encode("utf-8")).hexdigest()
            rec = {"task_id": task_id, "user": user, "src_len": len(content), "src_sha": src_sha}

            cur.execute("SELECT id FROM tech_team_outputs.ph_task WHERE task_id=%s", (task_id,))
            row = cur.fetchone()
            if row is None:
                rec["status"] = "MISSING (no row to update)"; results.append(rec); continue

            cur.execute(UPDATE_SQL, {"html_content": content, "task_id": task_id})
            upd = cur.fetchall()
            rec["rows_affected"] = len(upd)
            rec["id"] = upd[0][0]
            rec["updated_at"] = upd[0][1].isoformat()

            cur.execute(VERIFY_SQL, (rec["id"],))
            rid, au, aut, vl, vs, clen, dsha, cat, uat = cur.fetchone()
            rec.update(db_len=clen, db_sha=dsha, db_user=au, db_team=aut,
                       version_level=vl, version_status=vs,
                       created_at=cat.isoformat(), verified_updated_at=uat.isoformat())
            rec["sha_match"] = (dsha == src_sha)
            rec["len_match"] = (clen == len(content))
            rec["status"] = "UPDATED OK" if (rec["sha_match"] and rec["len_match"]) else "UPDATED (VERIFY FAIL)"
            results.append(rec)

        all_ok = all(r.get("status") == "UPDATED OK" for r in results)
        if all_ok:
            conn.commit(); print("\nCOMMITTED.")
        else:
            conn.rollback(); print("\nROLLED BACK (a verification failed).")

    print("\n===================== UPDATE SUMMARY =====================")
    print("{:<6} | {:<10} | {:>4} | {:<9} | {:<9} | {}".format("id","user","rows","sha_match","len_match","status"))
    print("-"*80)
    for r in results:
        print("{:<6} | {:<10} | {:>4} | {:<9} | {:<9} | {}".format(
            str(r.get("id","-")), r["user"], r.get("rows_affected","-"),
            str(r.get("sha_match","-")), str(r.get("len_match","-")), r["status"]))
    print("\n---- detail ----")
    for r in results:
        print(f"\n{r['user']}  (task_id={r['task_id']})")
        print(f"  row id            : {r.get('id')}")
        print(f"  rows_affected     : {r.get('rows_affected')}")
        print(f"  source len / sha  : {r['src_len']} / {r['src_sha']}")
        if "db_sha" in r:
            print(f"  stored len / sha  : {r['db_len']} / {r['db_sha']}")
            print(f"  version           : {r['version_level']} / {r['version_status']} (unchanged)")
            print(f"  created_at        : {r['created_at']} (unchanged)")
            print(f"  updated_at (new)  : {r['verified_updated_at']}")
        print(f"  status            : {r['status']}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
publish_dashboards.py
Generate one standalone dashboard HTML per ebay_priors user (only the
"Assigned User" name differs) and insert one row per user into
tech_team_outputs.ph_task. Large html_content is written via psycopg
(DATABASE_URL), never inline SQL.

Safe: SELECT-verifies before inserting; skips a user whose task_id already
exists; only NEW ph_task rows are written — no other production data touched.
"""
import os, sys, hashlib, datetime
import psycopg

HERE   = os.path.dirname(os.path.abspath(__file__))
BASE   = os.path.join(HERE, "dashboard.html")
DIST   = os.path.join(HERE, "dist")
DATED  = "2026-07-20"

USERS  = ["Thinesh", "Jarsini", "kobiga", "powsteena"]   # ebay_priors team
TEAM   = "ebay_priors"

PLACEHOLDER = "__ASSIGNED_USER__"
INJECT_TARGET = '            <span>Reporting Month: <b id="hdr-month">—</b></span>'
INJECT_REPL   = ('            <span>Assigned User : <b id="hdr-user">' + PLACEHOLDER + '</b></span>\n'
                 + INJECT_TARGET)

DESCRIPTION = ("eBay PPC Performance Dashboard (June 2026) showing campaign-level advertising "
    "performance including Total Sales, Orders, Ad Spend, ACOS, ROAS, CPC, CTR, Conversion Rate, "
    "AOV, KPI Summary, Filters, Campaign Performance Table, Charts and CSV Export. Built entirely "
    "from live PostgreSQL production data. HTML is fully standalone with embedded CSS, JavaScript "
    "and production data.")

FIXED = dict(
    project_name="eBay PPC Performance Dashboard",
    project_code="epd",
    task_name="REQ-07-D01 eBay PPC Performance Dashboard — June 2026",
    team="Development",
    developer="Apirame",
    assigned_user_team=TEAM,
    description=DESCRIPTION,
    phase_level=1,
    version_level=2,
    version_status="released",
)

INSERT_SQL = """
INSERT INTO tech_team_outputs.ph_task
  (project_name, project_code, task_name, task_id, team, developer,
   assigned_user, html_content, description, phase_level, version_level,
   version_status, action_took_by, action_took_date_time, assigned_user_team)
VALUES
  (%(project_name)s, %(project_code)s, %(task_name)s, %(task_id)s, %(team)s, %(developer)s,
   %(assigned_user)s, %(html_content)s, %(description)s, %(phase_level)s, %(version_level)s,
   %(version_status)s, NULL, NULL, %(assigned_user_team)s)
RETURNING id, created_at, updated_at;
"""

VERIFY_SQL = """
SELECT assigned_user, assigned_user_team,
       length(html_content)                                    AS char_len,
       encode(sha256(convert_to(html_content,'UTF8')),'hex')   AS sha256,
       created_at, updated_at
FROM tech_team_outputs.ph_task WHERE id = %s;
"""

def main():
    os.makedirs(DIST, exist_ok=True)
    base = open(BASE, encoding="utf-8").read()

    # Build template with the Assigned User line injected once.
    if base.count(INJECT_TARGET) != 1:
        sys.exit(f"ABORT: header inject target found {base.count(INJECT_TARGET)} times (need 1).")
    template = base.replace(INJECT_TARGET, INJECT_REPL, 1)
    if template.count(PLACEHOLDER) != 1:
        sys.exit("ABORT: placeholder injection failed.")

    url = os.environ["DATABASE_URL"]
    results = []
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        # roster verification (must exist AND be in ebay_priors)
        cur.execute("""SELECT DISTINCT assigned_user FROM tech_team_outputs.ph_task
                       WHERE assigned_user_team = %s""", (TEAM,))
        roster = {r[0] for r in cur.fetchall()}
        print("ebay_priors roster (from DB):", sorted(roster))

        for user in USERS:
            row = {**FIXED}
            row["assigned_user"] = user
            row["task_id"] = f"epd_{user}_ebay_ppc_performance_2026-06"
            fname = f"{DATED}_{user}_dashboard_V002.html"
            fpath = os.path.join(DIST, fname)

            # ---- generate + write the per-user file ----
            content = template.replace(PLACEHOLDER, user)
            with open(fpath, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            file_bytes = open(fpath, "rb").read()
            src_sha = hashlib.sha256(file_bytes).hexdigest()
            row["html_content"] = content

            rec = {"user": user, "file": fname, "task_id": row["task_id"],
                   "src_sha": src_sha, "src_len": len(content), "file_bytes": len(file_bytes)}

            # ---- PRE-INSERT verification ----
            rec["exists_in_team"] = user in roster
            cur.execute("SELECT 1 FROM tech_team_outputs.ph_task WHERE task_id = %s", (row["task_id"],))
            rec["task_id_taken"] = cur.fetchone() is not None
            rec["file_exists"] = os.path.exists(fpath)

            if not rec["exists_in_team"]:
                rec["status"] = "SKIPPED (not in ebay_priors)"; results.append(rec); continue
            if rec["task_id_taken"]:
                rec["status"] = "SKIPPED (task_id already exists)"; results.append(rec); continue

            # ---- INSERT ----
            cur.execute(INSERT_SQL, row)
            new_id, created_at, updated_at = cur.fetchone()
            rec["id"] = new_id

            # ---- POST-INSERT verification ----
            cur.execute(VERIFY_SQL, (new_id,))
            au, aut, char_len, db_sha, c_at, u_at = cur.fetchone()
            rec["db_user"] = au
            rec["db_team"] = aut
            rec["db_len"] = char_len
            rec["db_sha"] = db_sha
            rec["created_at"] = c_at.isoformat() if c_at else None
            rec["updated_at"] = u_at.isoformat() if u_at else None
            rec["sha_match"] = (db_sha == src_sha)
            rec["user_match"] = (au == user)
            rec["team_match"] = (aut == TEAM)
            rec["status"] = "INSERTED OK" if (rec["sha_match"] and rec["user_match"] and rec["team_match"]) else "INSERTED (verify FAIL)"
            results.append(rec)
        conn.commit()

    # ---- report ----
    print("\n================= PUBLISH SUMMARY =================")
    hdr = ("Assigned User", "HTML File", "Task ID", "Row ID", "SHA match", "Status")
    print("{:<13} | {:<40} | {:<44} | {:>6} | {:<9} | {}".format(*hdr))
    print("-"*150)
    for r in results:
        print("{:<13} | {:<40} | {:<44} | {:>6} | {:<9} | {}".format(
            r["user"], r["file"], r["task_id"], str(r.get("id","-")),
            str(r.get("sha_match","-")), r["status"]))
    print("\n---- detail ----")
    for r in results:
        print(f"\n{r['user']}:")
        print(f"  file bytes        : {r['file_bytes']}")
        print(f"  source SHA-256    : {r['src_sha']}")
        if "db_sha" in r:
            print(f"  stored SHA-256    : {r['db_sha']}")
            print(f"  char len src/db   : {r['src_len']} / {r['db_len']}")
            print(f"  db assigned_user  : {r['db_user']}  team: {r['db_team']}")
            print(f"  created_at        : {r['created_at']}")
            print(f"  updated_at        : {r['updated_at']}")
        print(f"  exists_in_team    : {r['exists_in_team']}  task_id_taken: {r['task_id_taken']}")

if __name__ == "__main__":
    main()

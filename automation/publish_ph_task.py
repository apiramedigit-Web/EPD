#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
publish_ph_task.py — insert one tech_team_outputs.ph_task row per user for the
reporting month. Only NEW rows are written; a user whose task_id already exists
is skipped (idempotent re-runs). Large html_content is sent via psycopg params.
"""
import os, hashlib
import config

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
SELECT assigned_user, assigned_user_team, length(html_content),
       encode(sha256(convert_to(html_content,'UTF8')),'hex')
FROM tech_team_outputs.ph_task WHERE id = %s;
"""


def get_next_version(cur):
    """version_level auto-increment: one past the current max for project_code='epd'."""
    cur.execute("SELECT COALESCE(MAX(version_level),0)+1 FROM tech_team_outputs.ph_task "
                "WHERE project_code = %s", (config.PROJECT_CODE,))
    return int(cur.fetchone()[0])


def task_id_for(user, reporting_month):
    return f"{config.PROJECT_CODE}_{user}_ebay_ppc_performance_{reporting_month}"


def publish(rep, files, version, dry_run=False, log=print):
    task_name = f"{config.TASK_PREFIX} — {rep['reporting_label']}"
    description = config.DESCRIPTION_TMPL.format(label=rep["reporting_label"])
    results = []
    with config.connect() as conn, conn.cursor() as cur:
        # verify roster membership
        cur.execute("SELECT DISTINCT assigned_user FROM tech_team_outputs.ph_task "
                    "WHERE assigned_user_team = %s", (config.ASSIGNED_TEAM,))
        roster = {r[0] for r in cur.fetchall()}

        for f in files:
            user = f["user"]
            tid = task_id_for(user, rep["reporting_month"])
            content = open(f["path"], encoding="utf-8").read()
            src_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
            rec = {"user": user, "file": f["name"], "task_id": tid, "src_sha": src_sha}

            in_team = user in roster or user in config.USERS
            cur.execute("SELECT 1 FROM tech_team_outputs.ph_task WHERE task_id=%s", (tid,))
            taken = cur.fetchone() is not None
            rec["in_team"] = in_team; rec["task_id_taken"] = taken

            if not in_team:
                rec["status"] = "SKIPPED (not in ebay_priors)"; results.append(rec); log(rec["status"]+f" {user}"); continue
            if taken:
                rec["status"] = "SKIPPED (task_id exists)"; results.append(rec); log(rec["status"]+f" {tid}"); continue
            if dry_run:
                rec["status"] = "DRY-RUN (would insert)"; rec["version_level"] = version
                results.append(rec); log(f"DRY-RUN would insert {tid} V{version:03d}"); continue

            row = dict(project_name=config.PROJECT_NAME, project_code=config.PROJECT_CODE,
                       task_name=task_name, task_id=tid, team=config.DEV_TEAM, developer=config.DEVELOPER,
                       assigned_user=user, html_content=content, description=description,
                       phase_level=1, version_level=version, version_status="released",
                       assigned_user_team=config.ASSIGNED_TEAM)
            cur.execute(INSERT_SQL, row)
            new_id, created_at, updated_at = cur.fetchone()
            cur.execute(VERIFY_SQL, (new_id,))
            au, aut, length, db_sha = cur.fetchone()
            rec.update(id=new_id, version_level=version, db_len=length, db_sha=db_sha,
                       created_at=created_at.isoformat(), updated_at=updated_at.isoformat(),
                       sha_match=(db_sha == src_sha), user_match=(au == user), team_match=(aut == config.ASSIGNED_TEAM))
            rec["status"] = ("INSERTED OK" if rec["sha_match"] and rec["user_match"] and rec["team_match"]
                             else "INSERTED (verify FAIL)")
            log(f"{rec['status']}  id={new_id}  {tid}  V{version:03d}  sha_match={rec['sha_match']}")
            results.append(rec)
        if not dry_run:
            conn.commit()
    return results

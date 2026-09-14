# Publish Procedure — ph_task

There are two publishing modes. Pick the one that matches the change.

## A. Update existing rows (D02 mode — default)

Use when the dashboard content changes but the task stays the same.

- Script: `Dashboard/update_ph_task.py`
- Identifies rows by `task_id` (`epd_<user>_ebay_ppc_performance_2026-06`)
- Sets `html_content` (per-user build) and `updated_at = now()` only
- Commits once, after all 4 rows verify by SHA-256 and length
- A missing `task_id` is reported and **not** created

## B. Insert new rows (D01 mode)

Use only for a genuinely new task or version agreed with the team.

- Script: `Dashboard/publish_dashboards.py`
- Writes `dist/<date>_<user>_dashboard_V<nnn>.html` and inserts one row per user
- Checks roster membership (`assigned_user_team = 'ebay_priors'`) and skips an existing `task_id`
- Before reuse, update the constants `DATED`, `task_id` pattern, `task_name`, `version_level`,
  `DESCRIPTION`, and the header inject target. The script still targets the D01
  "Reporting Month" header, while the D02 build uses "Reporting Period".

## Rules for both modes

1. HTML goes through psycopg bound parameters, never inline SQL.
2. Never publish without a passing `validate_charts.py` / `validate_range.py` run on the same data.
3. Assigned users: Thinesh, Jarsini, kobiga, powsteena (`ebay_priors`). Only the header name
   differs between their copies.
4. Do not change `version_status` set by an assigned user (e.g. row 397 `completed`) without
   agreement.
5. Save console output as evidence (`06_EVIDENCE/Deployment_Logs/`).

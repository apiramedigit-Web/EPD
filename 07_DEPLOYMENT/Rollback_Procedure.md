# Rollback Procedure

## What can be rolled back

`ph_task` keeps no history: an UPDATE overwrites `html_content`. A rollback writes a
**known earlier build** back into the same rows.

| Target | Source file (local only, not in Git) | Identification |
|---|---|---|
| D01 (2026-07-20) | `Dashboard/dist/2026-07-20_<user>_dashboard_V002.html` | SHA-256 in `06_EVIDENCE/SHA256_Results/local_file_sha256_2026-09-14.txt` |
| D01 full rows | `Dashboard/epd_ph_task_export_2026-07-20.csv` | round-trip SHA check in `export_epd_csv.py` |
| Any later build | a saved copy of `dashboard.html` + its `data.js` | record SHA-256 before each release |

## Steps

1. **Freeze**: tell the `ebay_priors` users that a rollback is in progress.
2. **Snapshot current state**: run query 1 of `04_SQL/rollback_queries.sql` and save the output.
3. **Save the current build**: copy `Dashboard/dashboard.html` and `data.js` aside, so the
   rollback can itself be reversed.
4. **Restore**, per user, in one transaction:
   - Load the earlier file as UTF-8 text (use the file as is; do not re-inject the header when
     restoring a `dist/` file, since it already contains it).
   - `UPDATE ... SET html_content = %s, updated_at = now() WHERE task_id = %s` via psycopg.
   - Compare DB `sha256(convert_to(html_content,'UTF8'))` with Python `sha256(text.utf8)`.
   - Commit only if all 4 match; otherwise roll back.
   Reuse the pattern in `Dashboard/update_ph_task.py`, replacing the per-user content source.
5. **Verify**: re-run query 1; the SHA-256 values must equal the restored files.
6. **Record**: add a Change_Log entry and save the console output in `06_EVIDENCE/Deployment_Logs/`.

## Cautions

- Rolling back to D01 removes the reporting-period and Campaign Type features for all users.
- Row 397 is `completed` by its assigned user; agree before replacing its content.
- `verify_ph_task.py` checks for the **current** on-disk build. It reports FAIL after a
  rollback, which is expected.

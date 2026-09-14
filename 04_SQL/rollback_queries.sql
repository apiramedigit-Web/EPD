-- =============================================================================
-- rollback_queries.sql — REQ-07 / D02
--
-- IMPORTANT: ph_task keeps no history. The UPDATE overwrote html_content, and
-- no copy of the previous database value is stored in the database.
-- Rollback therefore means writing a known earlier build back into the row.
--
-- Earlier build available locally (NOT in Git — contains production data):
--   Dashboard/dist/2026-07-20_<user>_dashboard_V002.html
--   = the exact html_content inserted for D01 by publish_dashboards.py.
--   Also: Dashboard/epd_ph_task_export_2026-07-20.csv (full rows as of 2026-07-20).
--
-- As with the forward update, html_content must be sent as a bound parameter
-- from Python (reuse the UPDATE + VERIFY pattern in Dashboard/update_ph_task.py),
-- not pasted into SQL.
-- =============================================================================

-- 1) Snapshot the current state BEFORE rolling back (record the output)
SELECT id, task_id, assigned_user, version_status,
       length(html_content)                                    AS char_len,
       encode(sha256(convert_to(html_content, 'UTF8')), 'hex') AS sha256,
       updated_at
FROM tech_team_outputs.ph_task
WHERE id IN (395, 396, 397, 398)
ORDER BY id;

-- 2) Restore one row to a previous build (run once per user, inside a transaction)
BEGIN;

UPDATE tech_team_outputs.ph_task
   SET html_content = :'previous_html_content',   -- bound from the dist/V002 file
       updated_at   = now()
 WHERE task_id = :'task_id'
RETURNING id, updated_at;

-- 3) Verify: sha256 must equal sha256 of the file you restored (computed in Python
--    over the UTF-8 text). If it does not match: ROLLBACK;
SELECT id,
       length(html_content)                                    AS char_len,
       encode(sha256(convert_to(html_content, 'UTF8')), 'hex') AS sha256
FROM tech_team_outputs.ph_task
WHERE task_id = :'task_id';

COMMIT;   -- only after the verification matches

-- Note: row 397 (kobiga) has version_status = 'completed', set by the user on
-- 2026-08-21. A content rollback does not change version_status; agree with the
-- assigned user before replacing content on a row they have completed.

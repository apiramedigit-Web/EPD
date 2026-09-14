-- =============================================================================
-- update_ph_task.sql — REQ-07 / D02
-- The in-place update applied to the four eBay PPC dashboard rows.
--
-- Source of truth: Dashboard/update_ph_task.py (UPDATE_SQL / VERIFY_SQL).
-- html_content is ~3.9 million characters, so it is ALWAYS sent as a bound
-- parameter by update_ph_task.py. Do not paste HTML into this file.
-- The statements below use psql variables for reference/review only.
-- =============================================================================

-- Rows in scope (task_id -> assigned_user):
--   395  epd_Thinesh_ebay_ppc_performance_2026-06    Thinesh
--   396  epd_Jarsini_ebay_ppc_performance_2026-06    Jarsini
--   397  epd_kobiga_ebay_ppc_performance_2026-06     kobiga
--   398  epd_powsteena_ebay_ppc_performance_2026-06  powsteena

-- 1) Pre-check: the row must already exist (the script never inserts)
SELECT id
FROM tech_team_outputs.ph_task
WHERE task_id = :'task_id';

-- 2) Update: only html_content and updated_at change
UPDATE tech_team_outputs.ph_task
   SET html_content = :'html_content',
       updated_at   = now()
 WHERE task_id = :'task_id'
RETURNING id, updated_at;

-- 3) Verify inside the same transaction; compare with the per-user source
--    SHA-256 / length computed in Python. COMMIT only if all 4 rows match.
SELECT id, assigned_user, assigned_user_team, version_level, version_status,
       length(html_content)                                  AS char_len,
       encode(sha256(convert_to(html_content, 'UTF8')), 'hex') AS sha256,
       created_at, updated_at
FROM tech_team_outputs.ph_task
WHERE id = :id;

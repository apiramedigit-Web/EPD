-- =============================================================================
-- verification_queries.sql — REQ-07 / D02   (READ-ONLY)
-- Source of truth: Dashboard/verify_ph_task.py
-- =============================================================================

-- 1) All epd rows, content summarised (no html dump)
SELECT id, task_id, assigned_user, assigned_user_team,
       phase_level, version_level, version_status,
       length(html_content)                                    AS char_len,
       encode(sha256(convert_to(html_content, 'UTF8')), 'hex') AS sha256,
       created_at, updated_at, action_took_by
FROM tech_team_outputs.ph_task
WHERE project_code = 'epd'
ORDER BY id;

-- 2) Feature markers of the D02 build inside each stored row
--    :'generated_at' = meta.generated_at of the current data.js
--    (2026-08-03T08:44:04.037684+05:30 for the released build)
SELECT id, assigned_user,
       (html_content LIKE '%id="f-campaign-type"%')                      AS campaign_type_filter_html,
       (html_content LIKE '%FILTERS.campaignType && r.campaign_type%')   AS campaign_type_filter_js,
       NOT (html_content LIKE '%>N/A<%')                                  AS no_literal_na,
       (position(:'generated_at' in html_content) > 0)                    AS latest_data_timestamp,
       (html_content LIKE '%id="hdr-user">' || assigned_user || '<%')    AS assigned_user_header,
       updated_at
FROM tech_team_outputs.ph_task
WHERE id IN (395, 396, 397, 398)
ORDER BY id;

-- 3) No duplicate rows were created
SELECT task_id, count(*) AS rows_per_task
FROM tech_team_outputs.ph_task
WHERE project_code = 'epd'
GROUP BY task_id
HAVING count(*) > 1;          -- expect 0 rows

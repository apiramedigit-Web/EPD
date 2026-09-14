# Deployment Validation Report — ph_task rows 395–398

**Result: PASS** — verified 2026-09-14 with `Dashboard/verify_ph_task.py` (read-only).
Raw output: `06_EVIDENCE/MCP_Verification/verify_ph_task_2026-09-14.txt`.

## What was deployed

| Item | Value |
|---|---|
| Base build | `Dashboard/dashboard.html`, 3,918,824 bytes |
| Base SHA-256 | `5d5fc4134feea1e9d7e56be73c982ce0f2087d4043b155b23097b6bdf814b95f` |
| Embedded data timestamp | 2026-08-03T08:44:04.037684+05:30 |
| Target | `tech_team_outputs.ph_task` in `order_management_copy` |
| Method | `update_ph_task.py` — UPDATE by `task_id`, verify, single commit |
| Deployed at | 2026-08-03 08:51:37 +05:30 (`updated_at` of rows 395, 396, 398) |

## Per-row verification

| id | User | SHA match | Length match | Campaign Type (HTML) | Campaign Type (JS) | No "N/A" | Latest data timestamp |
|---|---|---|---|---|---|---|---|
| 395 | Thinesh | True | True | True | True | True | True |
| 396 | Jarsini | True | True | True | True | True | True |
| 397 | kobiga | True | True | True | True | True | True |
| 398 | powsteena | True | True | True | True | True | True |

Script verdict: `PASS — all 4 rows hold the identical latest validated build`.

## Unchanged columns confirmed

| Column | Value | Status |
|---|---|---|
| `created_at` | 2026-07-20 15:00:19 +05:30 (all rows) | unchanged since D01 insert |
| `version_level` | 2 | unchanged |
| `assigned_user_team` | `ebay_priors` | unchanged |
| Row count for `project_code = 'epd'` | 4 | no duplicates created |

## Change after deployment (not made by this task)

Row 397 (kobiga): `version_status` changed `released` → `completed`, `action_took_by = kobiga`,
`updated_at` 2026-08-21 03:36:58 +05:30. Its `html_content` still matches the deployed build.

# Existing Publish Convention — `tech_team_outputs.ph_task`

Learned from `Dashboard/publish_dashboards.py` (D01) and the live rows.

## Row layout

| Column | Value used for `epd` |
|---|---|
| `project_name` | eBay PPC Performance Dashboard |
| `project_code` | `epd` |
| `task_name` | REQ-07-D01 eBay PPC Performance Dashboard — June 2026 |
| `task_id` | `epd_<user>_ebay_ppc_performance_2026-06` (one per user; no unique constraint, so the scripts check for it first) |
| `team` | Development |
| `developer` | Apirame |
| `assigned_user` | Thinesh / Jarsini / kobiga / powsteena |
| `assigned_user_team` | `ebay_priors` |
| `html_content` | complete standalone HTML |
| `phase_level` / `version_level` | 1 / 2 |
| `version_status` | `released` (kobiga's row later changed to `completed` by kobiga) |
| `action_took_by`, `action_took_date_time` | NULL on insert |

## Conventions

1. **One row per assigned user.** Every row holds the same dashboard; only the header line
   `Assigned User : <b id="hdr-user">NAME</b>` differs.
2. **Large HTML goes through a driver parameter** (psycopg), never inlined into SQL text.
3. **Verify before trusting**: SHA-256 of `convert_to(html_content,'UTF8')` and `length()` must
   match the source.
4. **Release file names**: `YYYY-MM-DD_<user>_dashboard_V<nnn>.html` (see `Dashboard/dist/`).
5. **Roster check**: users must already appear with `assigned_user_team = 'ebay_priors'`.

## Rows for this project

| id | assigned_user | created_at |
|---|---|---|
| 395 | Thinesh | 2026-07-20 15:00:19 +05:30 |
| 396 | Jarsini | 2026-07-20 15:00:19 +05:30 |
| 397 | kobiga | 2026-07-20 15:00:19 +05:30 |
| 398 | powsteena | 2026-07-20 15:00:19 +05:30 |

D02 **updates** these rows; it adds none.

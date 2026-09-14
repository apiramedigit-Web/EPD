# Production Deployment Report — REQ-07 / D02

| Field | Value |
|---|---|
| Deployment | In-place content update of `tech_team_outputs.ph_task` |
| Database | `order_management_copy` |
| Rows | 395 Thinesh, 396 Jarsini, 397 kobiga, 398 powsteena |
| Deployed | 2026-08-03 08:51:37 +05:30 |
| Data snapshot | 2026-08-03 08:44:04 +05:30 (reporting dates 2025-01-01 → 2026-08-03) |
| Build | `dashboard.html` 3,918,824 bytes, SHA-256 `5d5fc413…814b95f` |
| Method | `Dashboard/update_ph_task.py` |
| Verified | 2026-09-14 — PASS |

## Content of the release

- Reporting-period filtering on `ppc_performance.date` with 7 presets (default Last 30 Days)
- Campaign Type filter
- Metrics recalculated per period: KPIs, table, 6 charts, pagination, CSV export
- Charts placed below the Campaign Performance table
- Missing text values shown as "—"
- Build-time integrity banner: 997 campaigns · Spend 319,065.82 · Sales 2,373,474.15 ·
  Orders 203,255 · Clicks 1,858,976 · Impressions 963,714,869

## Result

| Check | Result |
|---|---|
| Rows updated / inserted | 4 / 0 |
| SHA-256 + length per row | match (4/4) |
| Feature markers per row | present (4/4) |
| `created_at`, `version_level` | unchanged |

## Post-deployment events

- 2026-08-21: kobiga marked row 397 `completed`.
- 2026-09-14: production data has moved on (1,144 campaigns, data to 2026-09-14). A data refresh
  release is recommended; see `05_VALIDATION/Production_Verification.md`.

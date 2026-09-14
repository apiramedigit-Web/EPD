# Dashboard Test Report

Tests run 2026-09-14 against the released build (`Dashboard/dashboard.js` + `Dashboard/data.js`,
data generated 2026-08-03 08:44 +05:30). The real dashboard JavaScript runs headless in Node
with a DOM shim (`validate_harness.js`, `validate_range.js`). Its output is reconciled with
live production SQL (`validate_charts.py`, `validate_range.py`).

Raw outputs: `06_EVIDENCE/SQL_Output/validate_charts_2026-09-14.txt`,
`06_EVIDENCE/SQL_Output/validate_range_2026-09-14.txt`.

## How to read the results

The scripts compare a **2026-08-03 snapshot** with **production as of 2026-09-14**. Production
has since grown: 997 → 1,144 campaigns, data up to 2026-09-14, and some historical dates
back-filled. Any check that uses the live campaign count, or a period touched by late data,
now reports FAIL even though the dashboard computes correctly. Periods whose production data
has not changed are the valid test of the logic.

## A. Build-time integrity — PASS

Sum of every embedded daily fact = production totals captured at build time.

| Metric | Daily-sum | SQL totals |
|---|---|---|
| Campaigns / Active / Paused | 997 / 331 / 151 | 997 / 331 / 151 |
| Spend | 319,065.82 | 319,065.82 |
| Sales | 2,373,474.15 | 2,373,474.15 |
| Orders | 203,255 | 203,255 |
| Clicks | 1,858,976 | 1,858,976 |
| Impressions | 963,714,869 | 963,714,869 |

Evidence: `06_EVIDENCE/SQL_Output/embedded_dataset_reconciliation_2026-09-14.txt`.

## B. Stable period — June 2026 — PASS on every period metric

| Metric | Dashboard | Production SQL |
|---|---|---|
| Ad Spend | 12,512.75 | 12,512.75 |
| Sales | 95,460.92 | 95,460.92 |
| Orders | 7,132 | 7,132 |
| Clicks | 64,669 | 64,669 |
| Impressions | 44,515,900 | 44,515,900 |
| ACOS / ROAS | 13.11% / 7.63 | 13.11 / 7.63 |
| CTR / CVR | 0.15% / 11.03% | 0.15 / 11.03 |
| AOV / CPC | £13.38 / £0.19 | 13.38 / 0.19 |
| Campaigns with activity (scatter points) | 293 | 293 |
| Top campaign by sales | £3,185.90 | £3,185.90 |
| CSV export spend / sales | 12,512.75 / 95,460.92 | same |
| Export filename | `ebay_ppc_2026-06-01_to_2026-06-30_filtered.csv` | contains range |

Only the campaign counts differ (997 vs 1,144 live), because campaigns were added after the build.

## C. Behaviour checks — PASS

| Check | Result |
|---|---|
| Date presets produce different results (Full vs Last 7) | PASS |
| 5 period-dependent charts change between periods (scatter, performance, top sales, top spend, trend) | PASS |
| Status distribution unchanged between periods (status is a campaign attribute) | PASS, by design |
| Start Date identical across two ranges (993 common campaigns) | PASS |
| Search narrows results | PASS |
| Export of the full-history view: 997 rows, spend 319,065.82, sales 2,373,474.15 = build SQL totals | PASS |
| Early period 2025-03: spend 15,745.17 = SQL; 237 active = 237 | values match |

## D. Checks reporting FAIL on 2026-09-14 — caused by production data added after the build

| Check | Dashboard (snapshot) | Production now | Cause |
|---|---|---|---|
| Total / Active / Paused campaigns | 997 / 331 / 151 | 1,144 / 423 / 185 | new campaigns |
| Last 30 days spend (2026-07-05 → 08-03) | 10,966.16 | 13,069.80 | late-arriving data |
| Today 2026-08-03 spend | 3.17 | 462.31 | late-arriving data |
| 2025-10-17 → 2026-06-30 spend | 150,903.81 | 157,968.36 | historical back-fill |
| Pagination / Table | page text "of 997" | expects 1,144 | depends on live count |

**Conclusion:** the logic reproduces SQL exactly wherever production data is unchanged. To make
these checks pass again, re-export and republish (see `07_DEPLOYMENT/Deployment_Process.md`).
No screenshots of the dashboard were kept.

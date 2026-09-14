# Daily Requirement — REQ-07 / D02

| Field | Value |
|---|---|
| Project | eBay PPC Performance Dashboard |
| Project code | `epd` |
| Requirement | REQ-07 |
| Deliverable | D02 (follows D01, the June 2026 release) |
| Developer | Apirame (Development) |
| Assigned team | `ebay_priors` — Thinesh, Jarsini, kobiga, powsteena |
| Delivery target | `tech_team_outputs.ph_task` rows 395–398 |
| Documented | 2026-09-14 |

## Source of this requirement

The original written D02 requirement text is **not stored in this project**. The requirement
below is reconstructed from the delivered code, file timestamps and the production `ph_task`
rows. Every statement links to the evidence it came from.

## D01 baseline (already released 2026-07-20)

- One standalone HTML dashboard per `ebay_priors` user, published by
  `Dashboard/publish_dashboards.py` as `ph_task` ids 395–398 (`version_level = 2`,
  `version_status = released`, task name "REQ-07-D01 eBay PPC Performance Dashboard — June 2026").
- Data was one aggregated row per campaign (`Dashboard/export_data.py`).
- Date filtering was by month (`f-date-min` / `f-date-max` in `Dashboard/dashboard01.txt`).

## D02 requirement (as delivered)

1. **Reporting-date filtering** — the Date Range must filter the reporting period using
   `public.ppc_performance.date`, not the campaign start date. KPIs, table, charts, pagination,
   search and CSV export must all use the selected period.
   Evidence: `Dashboard/export_data_daily.py` docstring, `Dashboard/dashboard.js` header comment.
2. **Date presets** — Today, Yesterday, Last 7 Days, Last 30 Days (default), This Month,
   Last Month, Custom Range. Evidence: `PRESETS` in `Dashboard/dashboard.js`.
3. **Campaign Type filter** — new `f-campaign-type` select (Advanced (CPC) / Standard (CPS) /
   Off-Site). Evidence: `Dashboard/layout.html`, `FILTERS.campaignType` in `dashboard.js`.
4. **No literal "N/A" in the rendered page** — missing text values show as "—".
   Evidence: `fmtByType` in `dashboard.js`; `no_NA` check in `Dashboard/verify_ph_task.py`.
5. **Update the existing ph_task rows in place** — no new rows. Refresh `html_content` and
   `updated_at` only. Keep each user's "Assigned User" header line. Evidence:
   `Dashboard/update_ph_task.py`.
6. **Prove the stored content** — SHA-256 and length of each stored row must equal the per-user
   build. Evidence: `Dashboard/verify_ph_task.py`.
7. **Layout** — charts moved below the Campaign Performance table; header reads
   "Reporting Period". Evidence: `Dashboard/layout.html` (comment "CHARTS (below the table)").

## Status

Delivered. The latest build (data generated 2026-08-03 08:44 +05:30) was written to rows
395–398 at 2026-08-03 08:51:37 +05:30 and still matches byte-for-byte on 2026-09-14
(`06_EVIDENCE/MCP_Verification/verify_ph_task_2026-09-14.txt`).

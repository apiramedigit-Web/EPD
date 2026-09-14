# Requirement Checklist — REQ-07 / D02

Status key: **Done** = delivered and verified by evidence; **Partial** = delivered with a noted gap.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Date Range filters by `public.ppc_performance.date` | Done | `dashboard.js` `buildRows()`; `06_EVIDENCE/SQL_Output/validate_range_2026-09-14.txt` (June 2026 range matches SQL on every metric) |
| 2 | Presets Today / Yesterday / Last 7 / Last 30 / This Month / Last Month / Custom | Done | `PRESETS` in `dashboard.js`; preset table in `validate_charts_2026-09-14.txt` |
| 3 | Default preset Last 30 Days | Done | `meta.default_preset = "last30"` in `data.js` |
| 4 | KPIs, table, charts, pagination, export follow the period | Done | `render()` in `dashboard.js`; charts-refresh hashes differ between ranges |
| 5 | Start Date is display-only | Done | "identical start_date = True" across 993 common campaigns (`validate_range_2026-09-14.txt`) |
| 6 | Campaign Type filter | Done | `f-campaign-type` present 5× and filter predicate present in stored HTML (`verify_ph_task_2026-09-14.txt`, columns CT_html / CT_js) |
| 7 | No literal "N/A" in rendered HTML | Done | `no_NA = True` for rows 395–398 |
| 8 | Export filename carries the period | Done | `ebay_ppc_2026-06-01_to_2026-06-30_filtered.csv` (`validate_range_2026-09-14.txt`) |
| 9 | Standalone HTML (no external CSS/JS/data) | Done | 0 × `src="data.js"`, `rel="stylesheet"`, `src="dashboard.js"`, `http(s)://` in `dashboard.html` |
| 10 | Daily facts reconcile with production totals at build time | Done | `06_EVIDENCE/SQL_Output/embedded_dataset_reconciliation_2026-09-14.txt` — PASS |
| 11 | ph_task rows 395–398 updated in place, no new rows | Done | Only 4 `epd` rows exist; `created_at` unchanged (2026-07-20 15:00:19) |
| 12 | Assigned User header per row | Done | `hdr-user` equals `assigned_user` for all 4 rows |
| 13 | Stored SHA-256 = per-user build | Done | `sha_match` / `len_match` True for all 4 rows |
| 14 | Monthly automation works with the D02 build | Partial | `automation/` still targets the D01 layout — see `08_DOCUMENTATION/Technical_Documentation.md` § Known gaps |

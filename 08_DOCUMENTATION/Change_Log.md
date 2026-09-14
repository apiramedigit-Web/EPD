# Change Log

Dates +05:30. Newest first.

## 2026-09-14 — Documentation and repository publication
- Filled AIOS documentation folders 01–09 from code, database state and re-run validation.
- Added evidence outputs under `06_EVIDENCE/` (read-only runs).
- Added `.gitignore`. Production data files (`data.js`, `dashboard.html`, `dist/`, ph_task CSV
  export) and runtime output are excluded from the public repository.
- No change to dashboard source, business logic or production rows.

## 2026-08-21 — Row status change (by assigned user)
- ph_task 397 (kobiga): `version_status` → `completed`, `action_took_by = kobiga`.

## 2026-08-03 — REQ-07 D02 deployed
- `export_data_daily.py` final revision; dataset regenerated (997 campaigns, 565 dates to 2026-08-03).
- `dashboard.html` rebuilt with `build_standalone.py`.
- ph_task 395–398 `html_content` updated in place (`update_ph_task.py`), verified by SHA-256.

## 2026-07-21 — REQ-07 D02 development
- `layout.html`: Reporting Period presets, From/To dates, Campaign Type filter, charts below table.
- `dashboard.js`: per-period re-aggregation from daily facts; Campaign Type filter; "—" for missing values.
- `update_ph_task.py` and `verify_ph_task.py` added.

## 2026-07-20 — REQ-07 D01 released + tooling
- `export_data.py`, `merge_standalone.py`, `publish_dashboards.py`: June 2026 dashboard inserted as
  ph_task 395–398 (`version_level 2`, `released`); `dist/*_V002.html` written.
- `export_epd_csv.py`, `export_epd_query_csv.py`: full row export with SHA round-trip.
- `automation/` monthly pipeline (D01 layout).
- `build_standalone.py`, `style.css`, validation harnesses (`validate_harness.js`,
  `validate_charts.py`, `validate_range.js`, `validate_range.py`).

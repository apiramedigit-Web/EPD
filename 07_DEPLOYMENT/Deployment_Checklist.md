# Deployment Checklist — eBay PPC Performance Dashboard

Use for every content refresh of ph_task rows 395–398. Tick each line; stop at the first failure.

## Before

- [ ] `DATABASE_URL` is set in the environment (do not print it)
- [ ] `python -c "import psycopg"` works; `node --version` works
- [ ] Record the current state: `04_SQL/verification_queries.sql` query 1 → save to `06_EVIDENCE/SHA256_Results/`
- [ ] Rollback source identified (previous `dashboard.html` copy or `dist/*_V002.html`)

## Build

- [ ] `python export_data_daily.py` ends with `RECONCILES (daily-sum == DB totals): True`
- [ ] `python build_standalone.py` reports `external ... none` for all four tokens
- [ ] `window.DASHBOARD_DATA: True` and `window.dashboardData : True`

## Validate

- [ ] `node validate_harness.js > _harness_out.json` exits 0
- [ ] `python validate_charts.py` → `OVERALL : ALL PASS` (run straight after the export so production has not moved)
- [ ] `PYTHONIOENCODING=utf-8 python validate_range.py` → `OVERALL: ALL PASS`

## Deploy

- [ ] `python update_ph_task.py` prints `COMMITTED.`
- [ ] Summary shows `UPDATED OK` with `sha_match True`, `len_match True` for all 4 users
- [ ] Console output saved to `06_EVIDENCE/Deployment_Logs/update_ph_task_YYYY-MM-DD.txt`

## After

- [ ] `python verify_ph_task.py` → `RESULT: PASS`
- [ ] `04_SQL/verification_queries.sql` query 3 returns 0 rows (no duplicates)
- [ ] `08_DOCUMENTATION/Change_Log.md` and `07_DEPLOYMENT/Release_Notes.md` updated
- [ ] Assigned users informed if a row's `version_status` is not `released` (e.g. row 397 `completed`)

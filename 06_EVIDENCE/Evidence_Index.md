# Evidence Index — REQ-07 / D02

All evidence below was produced on 2026-09-14 with read-only database access. The files contain
no credentials. They contain aggregate figures and staff first names that already appear in
the source code.

| File | What it proves | Used in |
|---|---|---|
| `MCP_Verification/verify_ph_task_2026-09-14.txt` | Rows 395–398 hold the latest build: SHA, length, Campaign Type markers, no "N/A", data timestamp | Deployment_Validation_Report |
| `SHA256_Results/ph_task_epd_rows_2026-09-14.txt` | All `epd` rows: status, version, length, SHA-256, created/updated timestamps | SHA256_Verification_Report |
| `SHA256_Results/local_file_sha256_2026-09-14.txt` | SHA-256 of the local build and source files | SHA256_Verification_Report |
| `SQL_Output/embedded_dataset_reconciliation_2026-09-14.txt` | Embedded daily facts = build-time SQL totals | Dashboard_Test_Report § A |
| `SQL_Output/validate_charts_2026-09-14.txt` | Output of `validate_charts.py` (presets, charts, stale-data check) | Dashboard_Test_Report § C, D |
| `SQL_Output/validate_range_2026-09-14.txt` | Output of `validate_range.py` (two custom ranges vs SQL) | Dashboard_Test_Report § B, D |
| `SQL_Output/campaign_type_filter_2026-09-14.txt` | Per-type June 2026 totals = SQL | Campaign_Type_Filter_Validation |

## Evidence that does not exist

| Item | Status |
|---|---|
| Console logs of the 2026-08-03 export / update runs | Not kept; timestamps reconstructed in `03_DEVELOPMENT/implementation_log.md` |
| Screenshots of the dashboard | None taken |
| Original written D02 requirement | Not in the project; reconstructed in `01_REQUIREMENTS/` |

## Reproduce

```bash
cd Dashboard
export PYTHONIOENCODING=utf-8          # Windows console
python verify_ph_task.py
node validate_harness.js > _harness_out.json && python validate_charts.py
python validate_range.py
```

`DATABASE_URL` must be set in the environment. Results for periods after 2026-08-03 change as
production data grows.

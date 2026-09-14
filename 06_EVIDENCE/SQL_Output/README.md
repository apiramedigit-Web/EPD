# SQL Output Evidence

| File | Produced by | Result |
|---|---|---|
| `embedded_dataset_reconciliation_2026-09-14.txt` | Python over `Dashboard/data.js` | PASS |
| `campaign_type_filter_2026-09-14.txt` | Python over `data.js` + read-only SQL | PASS |
| `validate_range_2026-09-14.txt` | `Dashboard/validate_range.py` | June 2026: all period metrics match. Other mismatches = data added after the build |
| `validate_charts_2026-09-14.txt` | `Dashboard/validate_charts.py` | Filters, Search, stale-data check PASS. KPI/Charts/Export/Pagination FAIL against live counts = data added after the build |

The FAIL lines are kept exactly as the scripts printed them. Their cause is explained in
`../../05_VALIDATION/Dashboard_Test_Report.md` § D.

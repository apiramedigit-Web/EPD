# Validation Checklist — REQ-07 / D02

Run 2026-09-14. PASS = verified; DRIFT = fails only because production data changed after the
2026-08-03 build; GAP = not covered by an automated test.

| # | Check | Result | Report |
|---|---|---|---|
| 1 | Embedded daily facts reconcile with build-time SQL totals | PASS | Dashboard_Test_Report § A |
| 2 | Period KPIs = SQL for an unchanged period (June 2026) | PASS | Dashboard_Test_Report § B |
| 3 | ACOS, ROAS, CTR, CVR, AOV, CPC = SQL (June 2026) | PASS | Dashboard_Test_Report § B |
| 4 | Charts change with the period; status chart constant by design | PASS | Dashboard_Test_Report § C |
| 5 | Start Date not affected by period | PASS | Dashboard_Test_Report § C |
| 6 | CSV export totals = SQL; filename carries the range | PASS | Dashboard_Test_Report § B, C |
| 7 | Search narrows results | PASS | Dashboard_Test_Report § C |
| 8 | Campaign Type filter totals = SQL per type | PASS | Campaign_Type_Filter_Validation |
| 9 | Campaign Type select driven by the headless harness | GAP | Campaign_Type_Filter_Validation § Limitation |
| 10 | Standalone HTML: no external CSS/JS/data/URLs | PASS | SHA256_Verification_Report; `dashboard.html` scan |
| 11 | `dashboard.html` reproducible from source parts | PASS | SHA256_Verification_Report § Reproducibility |
| 12 | 4 ph_task rows SHA/length = per-user build | PASS | SHA256_Verification_Report |
| 13 | Campaign Type + no "N/A" + latest data timestamp in stored rows | PASS | Deployment_Validation_Report |
| 14 | No duplicate ph_task rows; created_at / version unchanged | PASS | Deployment_Validation_Report |
| 15 | Campaign counts, Last 30 / Today / Last Month KPIs vs live SQL | DRIFT | Dashboard_Test_Report § D |
| 16 | Pagination / Table checks (use live campaign count) | DRIFT | Dashboard_Test_Report § D |
| 17 | Monthly `automation/` pipeline runs on the D02 build | GAP | Technical_Documentation § Known gaps |
| 18 | Visual check in a browser (screenshots) | GAP | none kept |

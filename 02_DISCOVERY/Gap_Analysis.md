# Gap Analysis — D01 → D02

| Area | D01 (2026-07-20) | D02 (2026-08-03) | Gap closed by |
|---|---|---|---|
| Data grain | One aggregated row per campaign | Daily facts per campaign + dimension | `export_data_daily.py` |
| Date filter | Month min/max selects | Reporting-date presets + From/To dates | `layout.html`, `dashboard.js` |
| Metric recalculation | Fixed totals | Re-aggregated for the selected period | `buildRows()` |
| Campaign Type filter | Not present | `f-campaign-type` | `layout.html`, `dashboard.js` |
| Header label | Reporting Month | Reporting Period (shows `from → to`) | `layout.html`, `syncRangeUI()` |
| Chart position | Above table | Below table | `layout.html` |
| Missing text values | Could display `N/A` | Displayed as "—" | `fmtByType()` |
| Build | `merge_standalone.py` (inject data.js into HTML) | `build_standalone.py` (assemble from parts) | new script |
| Publish | INSERT new rows | UPDATE existing rows in place | `update_ph_task.py` |
| Verification | SHA after insert | SHA + feature markers + data timestamp | `verify_ph_task.py` |
| Validation | Totals only | Real JS logic run headless and reconciled with SQL | `validate_harness.js`, `validate_range.js` + `.py` |

## Gaps still open

1. **`automation/` not upgraded** — `config.TEMPLATE_HTML` points to `<project>/dashboard.html`,
   which does not exist (the file is in `Dashboard/`). `generate_dashboard.py` looks for the D01
   "Reporting Month" header and a `rows` payload. `validate_dashboard.py` expects D01 filter ids
   (`f-date-min`, `f-start-from`, …). The monthly pipeline cannot run against the D02 build
   as-is.
2. **Snapshot drift** — the embedded data stops at 2026-08-03. On 2026-09-14, production had 1,144
   valid campaigns (997 at build) and data up to 2026-09-14.
3. **Currency** — mixed GBP/EUR/USD values are summed without FX conversion.
4. **Console encoding** — `validate_range.py` crashes on a Windows cp1252 console when printing
   `→`. Run with `PYTHONIOENCODING=utf-8`.

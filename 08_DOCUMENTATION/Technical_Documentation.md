# Technical Documentation

## Repository layout

```
ebay_ppc_dashboard/
├─ 01_REQUIREMENTS … 09_REUSABLE_KNOWLEDGE   AIOS documentation
├─ Dashboard/                  live D02 source + tooling
│  ├─ layout.html  style.css  dashboard.js       front end
│  ├─ export_data_daily.py                       D02 exporter -> data.js
│  ├─ build_standalone.py                        -> dashboard.html
│  ├─ update_ph_task.py  verify_ph_task.py       D02 publish / verify
│  ├─ validate_harness.js  validate_charts.py    preset + chart validation
│  ├─ validate_range.js    validate_range.py     custom-range validation
│  ├─ export_data.py  merge_standalone.py  dashboard01.txt   D01 (superseded)
│  ├─ publish_dashboards.py                      D01 insert publisher
│  └─ export_epd_csv.py  export_epd_query_csv.py ph_task CSV export
└─ automation/                 monthly pipeline (D01 layout — see Known gaps)
```

Not in Git (local, regenerated or containing production data): `data.js`, `dashboard.html`,
`dist/`, `epd_ph_task_export_*.csv`, `_harness_*`, `__pycache__/`, `logs/`.

## Data contract — `window.DASHBOARD_DATA`

| Key | Content |
|---|---|
| `meta` | title, `generated_at`, `reporting_date_field`, `date_min`, `date_max`, `today_date`, `default_preset`, `dates_count`, `source_tables`, `currency_note` |
| `sql_totals` | campaigns, active, paused, spend, sales, orders, clicks, impressions (full history) |
| `columns` | 23 × `{key, label, type}` — type ∈ text, status, money, int, pct, num, date, perf |
| `dim_cols` | account, marketplace, campaign_name, campaign_type, campaign_status, listing_id, sku, product_title, daily_budget, start_date |
| `dates` | sorted ISO dates |
| `dim` | one array per campaign in `dim_cols` order |
| `daily` | per campaign: `[dateIndex, impressions, clicks, spend, sales, orders]`, sorted by dateIndex |

## Front-end flow (`dashboard.js`)

`init → wire() → reconcile() → buildRows() → render()`

- `buildRows()` sums daily facts inside `[lowerIdx(from), upperIdx(to)]` and derives ratios and tier.
- `render()` filters (`getFiltered`), sorts (`getSorted`), then draws KPIs, SVG charts, table,
  pagination and the header.
- Date changes call `rebuildAndRender()`; other filters only call `render()`.
- `reconcile()` shows the banner comparing full-history facts with `sql_totals` (tolerance 0.02).
- Charts are inline SVG: scatter, 2 donuts, 2 horizontal bar charts, monthly trend. No libraries.
- CSV: `Export CSV` = the whole filtered/sorted view with all columns; `Export Current View` =
  the current page with visible columns.

## Tooling reference

| Script | Reads | Writes |
|---|---|---|
| `export_data_daily.py` | ppc, ppc_performance, listing_data, order_item_info | `data.js` |
| `build_standalone.py` | 4 source parts | `dashboard.html` |
| `validate_harness.js` / `validate_range.js` | `data.js`, `dashboard.js` | stdout JSON |
| `validate_charts.py` / `validate_range.py` | harness JSON + SQL | report |
| `update_ph_task.py` | `dashboard.html` | ph_task 395–398 |
| `verify_ph_task.py` | `dashboard.html` + ph_task | report |

## Known gaps

1. **`automation/` targets D01.**
   - `config.TEMPLATE_HTML = <project>/dashboard.html` does not exist; the build lives in `Dashboard/`.
   - `generate_dashboard.py` needs the "Reporting Month" header and a `rows`/`monthly` payload.
   - `validate_dashboard.py` expects filter ids `f-date-min`, `f-date-max`, `f-start-from`, `f-start-to`.
   - `publish_ph_task.py` inserts new monthly rows, while D02 updates rows in place.
2. **Harnesses do not drive `f-campaign-type`.** Covered by data-level validation instead.
3. **`validate_range.py` hard-codes ranges** and needs `PYTHONIOENCODING=utf-8` on Windows.
4. **`export_data_daily.py` writes before it validates.** On abort, `data.js` has already been replaced.
5. **`Dashboard/README.md`** describes source files as being at the project root; they are in `Dashboard/`.
6. **No FX normalisation** of EUR/USD marketplaces.

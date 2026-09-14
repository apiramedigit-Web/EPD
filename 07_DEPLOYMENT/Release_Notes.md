# Release Notes — eBay PPC Performance Dashboard

## REQ-07 D02 — deployed 2026-08-03

**New**
- Reporting Period filter based on the performance date (`ppc_performance.date`), with presets
  Today, Yesterday, Last 7 Days, Last 30 Days, This Month, Last Month, Custom Range, plus From/To
  date pickers. Default: Last 30 Days, ending on the latest date in the data.
- Campaign Type filter: Advanced (CPC), Standard (CPS), Off-Site.
- All KPI cards, the table, charts, pagination and CSV export recalculate for the selected period.
- Export file names include the period, e.g. `ebay_ppc_2026-06-01_to_2026-06-30_filtered.csv`.
- "Today's Spend" card = spend on the latest reporting date.

**Changed**
- Header shows "Reporting Period: from → to" instead of "Reporting Month".
- Charts moved below the Campaign Performance table.
- Missing Listing ID / SKU / Product Title are shown as "—" instead of "N/A".
- Product Title and SKU fall back to order-line data when the listing record has none.

**Unchanged**
- Campaign rules, performance tiers (High / Medium / Low), 23 table columns.
- The four ph_task rows (395–398): same task, same version level.

**Known limitations**
- Data snapshot ends 2026-08-03; the page does not refresh from the database.
- Values from UK, EU and US marketplaces are summed in native currency without FX conversion.
- Campaign Start Date is informational only.

## REQ-07 D01 — released 2026-07-20

First release: June 2026 campaign-level dashboard with KPI summary, filters, campaign table,
charts and CSV export, published as ph_task rows 395–398 (`version_level = 2`).

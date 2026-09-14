# Requirement Analysis — REQ-07 / D02

## Problem with D01

D01 exported one **pre-aggregated** row per campaign over the whole history. A date filter on
that data could only hide or show whole campaigns. It could not recalculate spend, sales or
clicks for a chosen period. D01's month filter therefore could not answer "how did campaigns
perform last week?".

## Approach chosen

| Need | Design decision | Where |
|---|---|---|
| Metrics for any period | Export per-campaign **daily facts** and re-aggregate in the browser | `export_data_daily.py` (`DAILY_SQL`), `dashboard.js` `buildRows()` |
| Static campaign attributes | Separate `dim` array (account, marketplace, name, type, status, listing, SKU, title, budget, start date) | `DIM_SQL`, `DIM_COLS` |
| Compact payload | Dates stored once; facts reference a date index: `[dateIndex, impressions, clicks, spend, sales, orders]` | `export_data_daily.py` |
| One grain per campaign | Use `record_type='campaign'` rows if the campaign has them, else `'ad'` rows — never both | `gp.pref` in `DAILY_SQL` |
| Data integrity | Daily facts must sum to independently queried totals (±0.05) or the export aborts | `recon` in `export_data_daily.py` |
| Start date must not filter | Start Date kept as display-only dimension | `dashboard.js` footnote |
| Standalone HTML | CSS, layout, data and JS inlined into one file | `build_standalone.py` |
| No duplicate ph_task rows | UPDATE by `task_id`, verify SHA-256, commit only if all 4 pass | `update_ph_task.py` |

## Business rules carried over from D01 unchanged

- eBay only: `source = 2`.
- Valid campaigns: `record_main_type = 'campaign'` and `record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')`.
- One row per `parent_id` (`DISTINCT ON (parent_id) ORDER BY ppc_etl_id`).
- Performance tiers (High / Medium / Low) — see `08_DOCUMENTATION/Business_Rules.md`.

## Constraints and risks identified

- **Currency**: values are in each marketplace's native currency (GBP/EUR/USD) and are not
  FX-normalised, although labels show £. Stated in the dashboard footnote.
- **Titles**: `listing_data.title` is empty for most eBay items, so titles fall back to the most
  frequent order-line title (`order_title` CTE).
- **Snapshot data**: the HTML embeds a snapshot. It does not refresh itself; live production data
  keeps moving after the build (see `05_VALIDATION/Production_Verification.md`).
- **Payload size**: the standalone file is 3.9 MB (3,918,824 bytes).

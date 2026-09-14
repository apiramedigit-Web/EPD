# Database Mapping — eBay PPC Performance Dashboard

Database: `order_management_copy` (reported by `SELECT current_database()` in `verify_ph_task.py`).

## Dimension fields (`dim`)

| Dashboard column | Source | Rule |
|---|---|---|
| Account | `ppc.ss_name` | `COALESCE(...,'Unknown')` |
| Marketplace | `ppc.market_place` | `COALESCE(...,'Unknown')` |
| Campaign Name | `ppc.record_name` | empty → `(Unnamed Campaign)` |
| Campaign Type | `ppc.record_subtype` | `ON_SITE` → Advanced (CPC); `COST_PER_SALE` → Standard (CPS); `OFF_SITE` → Off-Site |
| Campaign Status | `ppc.record_status` | `COALESCE(...,'unknown')`; `running` shown as Active |
| Listing ID | `ppc_performance.ref_id` | the campaign's top ad listing by spend, then sales, then ref_id |
| SKU | `listing_data.mapped_sku` / `sku`, then `order_item_info.oii_item_sku` | first non-empty; else `N/A` |
| Product Title | `listing_data.title`, then `order_item_info.oii_item_title` | trailing `[variant]` suffix removed; else `N/A` |
| Daily Budget | `ppc.bid` | `COALESCE(...,0)` |
| Start Date | `MIN(ppc_performance.date)` | display-only |

`public.ppc` campaign row chosen with `DISTINCT ON (parent_id) ORDER BY parent_id, ppc_etl_id`.

## Fact fields (`daily`)

From `public.ppc_performance` where `source = 2`, grouped by `parent_id, date`:
`SUM(impressions)`, `SUM(clicks)`, `SUM(spend)`, `SUM(sales)`, `SUM(orders)`.

**Grain rule**: if the campaign has any `record_type = 'campaign'` rows, only those are summed;
otherwise its `record_type = 'ad'` rows are summed. This stops double counting.

## Joins

| From | To | Key |
|---|---|---|
| `ppc` (campaign) | `ppc_performance` | `parent_id` |
| top listing | `listing_data` | `listing_data.ref_id = ppc_performance.ref_id`, `which_channel = 2`, `wrong_sku = 0` |
| top listing | `order_item_info` | `oii_item_id = ref_id` |

## Dataset profile at build (2026-08-03 08:44 +05:30)

| Measure | Value |
|---|---|
| Campaigns | 997 (Advanced (CPC) 587, Standard (CPS) 395, Off-Site 15) |
| Status | deleted 456, running 331, paused 151, ended 59 |
| Marketplaces | UK 467, Germany 361, France 60, US 46, Italy 31, Canada 25, Spain 7 |
| Accounts | 5 |
| Reporting dates | 565 (2025-01-01 → 2026-08-03) |
| Listing ID / SKU / Title shown as "—" | 447 / 455 / 478 campaigns |

## Output table

`tech_team_outputs.ph_task` — see `02_DISCOVERY/Existing_Publish_Convention.md`.

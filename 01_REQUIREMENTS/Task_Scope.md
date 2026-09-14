# Task Scope — REQ-07 / D02

## In scope

- Rebuild the dashboard dataset as per-campaign daily facts (`Dashboard/export_data_daily.py`).
- Front-end changes in `Dashboard/layout.html`, `Dashboard/dashboard.js`, `Dashboard/style.css`:
  reporting-period presets, From/To date inputs, Campaign Type filter, charts below the table.
- Assemble the standalone file (`Dashboard/build_standalone.py`).
- Validate the real dashboard logic against production SQL (`validate_harness.js` +
  `validate_charts.py`, `validate_range.js` + `validate_range.py`).
- Update `html_content` / `updated_at` of the four existing `ph_task` rows (`update_ph_task.py`)
  and verify them (`verify_ph_task.py`).

## Out of scope

- Creating new `ph_task` rows or changing `task_id`, `task_name`, `version_level`,
  `version_status`, `description` or `created_at`.
- Changing the D01 business rules (campaign validity, grain de-duplication, performance tiers).
- FX conversion of non-GBP marketplaces.
- Updating the `automation/` monthly pipeline to the D02 layout.
- Any write to production tables other than `tech_team_outputs.ph_task`.

## Data sources (read-only)

| Table | Use |
|---|---|
| `public.ppc` | Campaign dimension (account, marketplace, name, type, status, bid) |
| `public.ppc_performance` | Daily facts: impressions, clicks, spend, sales, orders |
| `public.listing_data` | Listing SKU and title (`which_channel = 2`, `wrong_sku = 0`) |
| `public.order_item_info` | Fallback title and SKU for promoted items |

Database: `order_management_copy`, connection from the `DATABASE_URL` environment variable.

## Write target

`tech_team_outputs.ph_task`, rows 395–398 (`project_code = 'epd'`).

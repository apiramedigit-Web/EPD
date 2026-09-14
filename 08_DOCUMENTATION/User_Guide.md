# User Guide — eBay PPC Performance Dashboard

For the `ebay_priors` team (Thinesh, Jarsini, kobiga, powsteena). Your copy shows your name next to
**Assigned User** in the header.

## 1. Choose a reporting period

- Use the buttons: **Today, Yesterday, Last 7 Days, Last 30 Days, This Month, Last Month**.
- Or set **From Date** and **To Date** for a custom period.
- "Today" means the **latest date in the data** (currently 2026-08-03), not your computer's date.
- The header shows the active period as `from → to`.

Everything on the page recalculates for that period: KPI cards, charts, table and exports.

## 2. Filter

| Filter | Use |
|---|---|
| Account, Marketplace | pick one seller account or site |
| Campaign Type | Advanced (CPC), Standard (CPS), Off-Site |
| Campaign Status | running (Active), paused, ended, deleted |
| Performance | High, Medium, Low (see below) |
| ACOS / ROAS range | enter min and/or max |
| Search | campaign name, Listing ID, SKU or product title |

**Reset Filters** clears everything and returns to Last 30 Days.

## 3. KPI cards

Totals for the filtered campaigns in the period. "Average" ACOS/ROAS/CPC/CTR/Conversion/AOV are
calculated from the totals, e.g. total spend ÷ total sales. "Today's Spend" is the spend on the
latest date.

## 4. Performance tiers

- **High**: ROAS ≥ 8, ACOS ≤ 12% and conversion ≥ 8%.
- **Medium**: ROAS 5–8 with ACOS 12–20%, or anything that is neither High nor Low.
- **Low**: no spend, no sales or no clicks in the period; or ROAS < 5; or ACOS > 20%.

A campaign's tier can change when you change the period.

## 5. Table

- Click a column header to sort; drag its edge to resize.
- **Columns ▾** hides or shows columns.
- Click any cell to copy its value.
- Tick rows to count a selection; choose 25/50/100/250 rows per page.
- "—" means the value is not available (for example, no listing linked).

## 6. Export

- **Export CSV** — all filtered rows, all columns, in the current sort order.
- **Export Current View** — only the rows on this page, visible columns only.
- File names include the period, e.g. `ebay_ppc_2026-07-01_to_2026-07-31_filtered.csv`.

## 7. Things to know

- The data is a snapshot taken **2026-08-03 08:44**, shown as "Last Sync". Refresh reloads the
  page; it does not fetch new data.
- UK, EU and US campaigns are in their own currencies (GBP/EUR/USD) and are added together as-is.
- **Start Date** is when the campaign first had activity. It does not affect the period filter.
- The green banner confirms that the embedded data matched the database when it was built.

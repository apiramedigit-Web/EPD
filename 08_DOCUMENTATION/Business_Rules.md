# Business Rules

Every rule below is implemented in code; the location is given for each.

## 1. Campaign population

| Rule | Implementation |
|---|---|
| eBay only | `ppc.source = 2`, `ppc_performance.source = 2` |
| Campaign records only | `ppc.record_main_type = 'campaign'` |
| Valid types only | `record_subtype IN ('ON_SITE','COST_PER_SALE','OFF_SITE')` (excludes `''`, `'0'`) |
| One record per campaign | `DISTINCT ON (parent_id) ORDER BY parent_id, ppc_etl_id` |
| All statuses included | running, paused, ended, deleted |

## 2. Metric grain (no double counting)

For each `parent_id`: if any `ppc_performance.record_type = 'campaign'` rows exist, only those
are summed; otherwise the `'ad'` rows are summed.

## 3. Reporting period

- Filter field: `public.ppc_performance.date`.
- "Today" = latest date in the data (`meta.today_date`), not the viewer's clock.
- Presets: Today; Yesterday; Last 7 Days = today−6 … today; Last 30 Days = today−29 … today;
  This Month = 1st … today; Last Month = previous calendar month. Dates are clamped to the data range.
- Custom From > To is swapped automatically.
- Campaign Start Date = first performance date. It is display-only and never filters.
- A campaign with no activity in the period stays in the table with zero metrics.

## 4. KPI formulas (period totals)

| KPI | Formula | Empty when |
|---|---|---|
| ACOS (%) | spend ÷ sales × 100 | sales = 0 |
| ROAS | sales ÷ spend | spend = 0 |
| Avg. CPC | spend ÷ clicks | clicks = 0 |
| CTR (%) | clicks ÷ impressions × 100 | impressions = 0 |
| Conversion Rate (%) | orders ÷ clicks × 100 | clicks = 0 |
| AOV | sales ÷ orders | orders = 0 |
| Active / Paused campaigns | status = `running` / `paused` | — |
| Today's Spend | spend on the latest reporting date | — |

"Average" KPI cards are portfolio ratios of the summed totals, not averages of campaign ratios.
Values are rounded to 2 decimals.

## 5. Performance tier (per campaign, per period)

Evaluated in this order:

1. spend = 0 **or** sales = 0 **or** clicks = 0 → **Low**
2. ROAS ≥ 8 **and** ACOS ≤ 12 **and** CVR ≥ 8 → **High**
3. 5 ≤ ROAS < 8 **and** 12 < ACOS ≤ 20 → **Medium**
4. ROAS < 5 **or** ACOS > 20 → **Low**
5. otherwise → **Medium**

(`dashboard.js` `buildRows()`; identical CASE in `automation/generate_dashboard.py`.)

## 6. Descriptive fields

- Campaign Type labels: ON_SITE = Advanced (CPC), COST_PER_SALE = Standard (CPS), OFF_SITE = Off-Site.
- Listing ID = the campaign's ad listing with the highest spend (then sales, then ID).
- SKU = `listing_data` mapped SKU, else SKU, else the most frequent order-line SKU.
- Title = `listing_data` title, else the most frequent order-line title with any trailing
  `[variant]` removed.
- Missing values display as "—".

## 7. Currency

Amounts are in each marketplace's own currency (GBP, EUR, USD) and are **not** converted, although
labels show £. This is stated in the dashboard footnote.

## 8. Distribution

One identical dashboard per `ebay_priors` member (Thinesh, Jarsini, kobiga, powsteena); only the
"Assigned User" header differs.

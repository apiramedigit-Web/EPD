# PostgreSQL Findings

1. **Two grains in `ppc_performance`.** A campaign can have `record_type = 'campaign'` rows,
   `'ad'` rows, or both. Summing both double counts. Rule: prefer `campaign` rows, fall back to
   `ad` rows (`gp.pref`).
2. **Junk campaign subtypes.** `ppc.record_subtype` contains `''` and `'0'`. Only `ON_SITE`,
   `COST_PER_SALE` and `OFF_SITE` are real eBay campaign types.
3. **Several `ppc` rows per campaign.** A campaign appears more than once in `ppc`; the first
   by `ppc_etl_id` is used (`DISTINCT ON (parent_id)`).
4. **Titles mostly missing in `listing_data`.** The code comment records that eBay titles are
   absent from `listing_data.title` for about 98% of items. `order_item_info.oii_item_title`
   (most frequent value, variant suffix removed) is used as a fallback.
5. **Some promoted items are not in `listing_data`.** SKU falls back to the most frequent
   `order_item_info.oii_item_sku`.
6. **`listing_data` filters**: `which_channel = 2` (eBay) and `wrong_sku = 0`.
7. **Mixed currencies.** `ppc_performance` values are in marketplace currency; there is no FX
   step in this project.
8. **Late-arriving data.** Comparing the 2026-08-03 snapshot with production on 2026-09-14:
   - valid campaigns 997 → 1,144 (running 331 → 423, paused 151 → 185)
   - `ppc_performance` (source 2) now ends 2026-09-14
   - range 2025-10-17 → 2026-06-30 spend grew from £150,903.81 to £157,968.36, so historical
     dates were also back-filled
   - June 2026 (2026-06-01 → 2026-06-30) was unchanged on every metric
9. **Large text values.** SHA-256 must be computed on `convert_to(html_content,'UTF8')` to
   compare with a Python UTF-8 digest.

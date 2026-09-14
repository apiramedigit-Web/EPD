# Campaign Type Filter Validation

**Result: PASS** — run 2026-09-14, read-only.
Raw output: `06_EVIDENCE/SQL_Output/campaign_type_filter_2026-09-14.txt`

## 1. Filter is present in the delivered build

| Check | Result | Evidence |
|---|---|---|
| `<select id="f-campaign-type">` in `layout.html` | Present | `layout.html` line 59 |
| Filter predicate `FILTERS.campaignType && r.campaign_type` in `dashboard.js` | Present | `getFiltered()` |
| Options built from the data (`distinct` of `campaign_type`) | Yes | `wire()` |
| Reset Filters clears it | Yes | `btn-reset` handler resets `campaignType` and `f-campaign-type` |
| Present in all 4 stored ph_task rows | True (CT_html, CT_js) | `06_EVIDENCE/MCP_Verification/verify_ph_task_2026-09-14.txt` |

## 2. Type mapping

| `ppc.record_subtype` | Dashboard label | Campaigns at build |
|---|---|---|
| `ON_SITE` | Advanced (CPC) | 587 |
| `COST_PER_SALE` | Standard (CPS) | 395 |
| `OFF_SITE` | Off-Site | 15 |
| **Total** | | **997** = dataset size (no campaign lost or double counted) |

## 3. Numbers per type — June 2026 (2026-06-01 → 2026-06-30)

The embedded data was aggregated the same way `buildRows()` does it, then split by campaign
type. It was compared with an independent production SQL query grouped by `record_subtype`.

| Type | Spend | Sales | Orders | Clicks | Impressions | Match |
|---|---|---|---|---|---|---|
| Advanced (CPC) | 7,799.04 | 42,100.97 | 3,172 | 43,874 | 20,775,043 | OK |
| Standard (CPS) | 4,713.71 | 53,359.95 | 3,960 | 20,795 | 23,740,857 | OK |
| Off-Site | 0.00 | 0.00 | 0 | 0 | 0 | OK |
| **All types** | **12,512.75** | **95,460.92** | | | | equals the unfiltered June totals in `Dashboard_Test_Report.md` |

June 2026 was chosen because production data for that month is unchanged since the build
(see `Production_Verification.md`). Later periods have received late-arriving data.

## Limitation

This test aggregates the embedded data in Python using the same rules as `dashboard.js`. The
headless harnesses (`validate_harness.js`, `validate_range.js`) do not yet drive the
`f-campaign-type` select, so the in-browser event handler was verified by code review only.

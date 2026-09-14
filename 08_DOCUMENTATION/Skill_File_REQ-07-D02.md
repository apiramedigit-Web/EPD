# Skill File — REQ-07 D02: Period-filterable standalone dashboard published to ph_task

## When to use

A standalone HTML dashboard must let users pick any date range, with every figure recalculated,
and be delivered to named users through `tech_team_outputs.ph_task`.

## Inputs

- Read access to the fact table (daily grain) and dimension tables.
- The `ph_task` rows to update (`task_id` per assigned user).
- `DATABASE_URL` in the environment.

## Procedure

1. **Model the data as `dim` + `daily`.** One dimension record per entity. Per-entity daily facts
   are stored as `[dateIndex, m1, m2, …]`, with a shared sorted `dates` list.
   (`export_data_daily.py`)
2. **Fix the grain in SQL.** Choose exactly one source grain per entity (here: campaign rows,
   else ad rows).
3. **Reconcile at export.** Query totals independently; abort if the sum of daily facts differs
   by more than 0.05.
4. **Re-aggregate in the browser.** Binary-search the date index for the period bounds. Sum facts
   per entity, then derive ratios (ACOS, ROAS, CTR, CVR, AOV, CPC) from the sums.
   (`dashboard.js` `buildRows()`)
5. **Everything reads from one filtered view.** KPIs, charts, table, pagination and export all use
   the same `VIEW`.
6. **Assemble one standalone file.** Inline CSS, layout, data (escape `</script`) and JS.
   Assert there are no external references. (`build_standalone.py`)
7. **Validate the real JS headless.** Use a DOM shim that drives presets and custom ranges,
   then reconcile KPIs, charts and CSV with SQL for the same window.
   (`validate_harness.js` / `validate_range.js` + `.py`)
8. **Publish in place.** Per user, inject the header line. UPDATE `html_content` and `updated_at`
   by `task_id`, recompute SHA-256 in the DB, and commit only if every row matches.
   (`update_ph_task.py`)
9. **Prove it read-only.** SHA, length, feature markers and the data timestamp in the stored rows.
   (`verify_ph_task.py`)

## Acceptance

- Build-time reconciliation PASS.
- Stable-period KPIs = SQL on every metric.
- Period charts change between ranges; period-independent charts do not.
- All target rows: SHA match, length match, no new rows.

## Pitfalls

- A snapshot drifts from production. Validate immediately after export, and tag evidence with
  the data timestamp.
- Do not filter on entity start date when the requirement is reporting date.
- Large HTML must use bound parameters; never inline it in SQL or MCP calls.
- Set `PYTHONIOENCODING=utf-8` on Windows.

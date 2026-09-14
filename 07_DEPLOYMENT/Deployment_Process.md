# Deployment Process

All commands run from `Dashboard/`. Production reads use `public.ppc`, `public.ppc_performance`,
`public.listing_data` and `public.order_item_info`. The only write is to
`tech_team_outputs.ph_task`.

```bash
cd Dashboard
export PYTHONIOENCODING=utf-8   # Windows console safety

# 1. Export production data -> data.js (aborts if facts don't reconcile)
python export_data_daily.py

# 2. Assemble the standalone page -> dashboard.html
python build_standalone.py

# 3. Validate the real dashboard logic against SQL
node validate_harness.js > _harness_out.json
python validate_charts.py
python validate_range.py

# 4. Push the build into ph_task rows 395-398 (verify + single commit)
python update_ph_task.py

# 5. Independent read-only proof
python verify_ph_task.py
```

## Step details

| Step | Output | Stop if |
|---|---|---|
| 1 | `data.js` (~3.9 MB): `meta`, `sql_totals`, `columns`, `dim_cols`, `dates`, `dim`, `daily` | `ABORT: daily facts do not reconcile with DB totals.` |
| 2 | `dashboard.html` | any `PRESENT (BAD)` external reference |
| 3 | PASS/FAIL report | any FAIL (run immediately after step 1) |
| 4 | UPDATE summary | `ROLLED BACK (a verification failed).` or any `MISSING` row |
| 5 | per-row table | `RESULT: FAIL` |

## Notes

- `validate_range.py` has two fixed ranges (`2025-10-17 → 2026-06-30`, `2026-06-01 → 2026-06-30`).
  Update `RANGES` if the data window changes.
- Step 1 writes `data.js` **before** its reconciliation check. If it aborts, the new `data.js`
  is already on disk. Do not run step 2 until step 1 passes.
- The `automation/` monthly pipeline is **not** part of this process. It targets the D01 layout
  (see `08_DOCUMENTATION/Technical_Documentation.md`).

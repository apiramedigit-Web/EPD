# Production Deployment Pattern — Build · Validate · Publish · Prove

```
 export (read)  ──►  reconcile totals ──► build artefact ──► validate real logic vs SQL
                          │ fail: abort                          │ fail: stop
                                                                 ▼
 prove (read-only) ◄── commit ◄── verify every row ◄── publish (bound params, one txn)
                                     │ fail: rollback all
```

## Stages

| Stage | Gate | REQ-07 implementation |
|---|---|---|
| Export | independent totals equal the exported facts | `export_data_daily.py` |
| Build | no external references; deterministic from sources | `build_standalone.py` |
| Validate | the real front-end code reproduces SQL for several periods | `validate_harness.js` + `validate_charts.py`; `validate_range.*` |
| Publish | target rows exist; single transaction | `update_ph_task.py` |
| Verify | SHA-256 + length per row, inside the transaction | `update_ph_task.py` |
| Prove | separate read-only script after commit | `verify_ph_task.py` |
| Record | evidence saved with the data timestamp | `06_EVIDENCE/` |

## Rules

- Run Export → Validate back to back; production data keeps changing.
- Every gate prints a clear PASS/FAIL or ABORT line, so a human or scheduler can stop on it.
- Publishing is idempotent: re-running with the same build gives the same stored hashes.
- Keep the previous artefact and its hash so a rollback is a normal publish of known content.

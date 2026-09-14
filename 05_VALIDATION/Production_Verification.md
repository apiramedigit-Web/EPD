# Production Verification

Checked 2026-09-14, read-only, database `order_management_copy`.

## 1. Delivered content in production — PASS

All four `ph_task` rows hold the D02 build byte-for-byte. See `Deployment_Validation_Report.md`.

## 2. Does production data still match the delivered snapshot?

The dashboard is a snapshot (`meta.generated_at` 2026-08-03 08:44 +05:30). It does not refresh
itself.

| Measure | Snapshot (2026-08-03) | Production (2026-09-14) |
|---|---|---|
| Valid eBay campaigns | 997 | 1,144 |
| Running / paused | 331 / 151 | 423 / 185 |
| Last reporting date | 2026-08-03 | 2026-09-14 |
| Spend dated after 2026-08-03 (campaign + ad grains) | — | 31,350.35 |
| June 2026 spend / sales | 12,512.75 / 95,460.92 | 12,512.75 / 95,460.92 (unchanged) |
| 2025-10-17 → 2026-06-30 spend | 150,903.81 | 157,968.36 (back-filled) |

## Verdict

- **Deployment**: verified — production serves exactly what was built and validated.
- **Freshness**: the snapshot is 6 weeks behind production. Users who pick periods after
  2026-08-03 see no data, and some earlier periods are understated.
- **Action**: refresh the dataset and republish with the documented process
  (`07_DEPLOYMENT/Deployment_Process.md`). That is a new release and is outside this
  documentation task.

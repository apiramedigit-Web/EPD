# Database Verification Evidence

| File | Produced by | Result |
|---|---|---|
| `verify_ph_task_2026-09-14.txt` | `Dashboard/verify_ph_task.py` (read-only) | PASS — all 4 rows hold the identical latest validated build |

The script connects through `DATABASE_URL`, reports `current_database()` (`order_management_copy`),
recomputes the expected per-user SHA-256 from the local `dashboard.html`, and compares it with
each stored row.

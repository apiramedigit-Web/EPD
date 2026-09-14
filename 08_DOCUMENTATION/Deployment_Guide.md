# Deployment Guide

Short guide for a developer who needs to refresh the dashboard. The detailed references are in
`07_DEPLOYMENT/`.

## 1. Prerequisites

| Need | Check |
|---|---|
| Python 3.10+ with psycopg 3 | `python -c "import psycopg; print(psycopg.__version__)"` |
| Node.js | `node --version` |
| Database access | `DATABASE_URL` set in your user environment (never commit it, never echo it) |
| Local data files | `data.js` / `dashboard.html` are not in Git; step 2 regenerates them |

## 2. Refresh and publish

```bash
cd Dashboard
export PYTHONIOENCODING=utf-8
python export_data_daily.py
python build_standalone.py
node validate_harness.js > _harness_out.json
python validate_charts.py
python validate_range.py
python update_ph_task.py
python verify_ph_task.py
```

Follow `07_DEPLOYMENT/Deployment_Checklist.md` while doing it.

## 3. If something fails

| Symptom | Meaning | Action |
|---|---|---|
| `ABORT: daily facts do not reconcile` | export inconsistent | investigate SQL grain; do not build |
| `ABORT: header inject target found N times` | layout header changed | fix `INJECT_TARGET` in `update_ph_task.py` to match `layout.html` |
| `ROLLED BACK (a verification failed)` | stored content ≠ build | nothing was changed; re-run |
| `UnicodeEncodeError: 'charmap'` | Windows console encoding | set `PYTHONIOENCODING=utf-8` |
| Validation FAIL for recent periods | production changed after export | re-run export and validation together |

## 4. Rollback

See `07_DEPLOYMENT/Rollback_Procedure.md`.

# eBay PPC Performance Dashboard — REQ-07 / D02

| Field | Value |
|---|---|
| Project | eBay PPC Performance Dashboard |
| Requirement ID | REQ-07 |
| Deliverable ID | D02 |
| Structure created | 2026-07-23 |
| Status | Delivered 2026-08-03; AIOS documentation completed 2026-09-14 |

## Source Code (live — do not duplicate)

The working source stays at the project root and in its existing folders:

| File / Folder | Role |
|---|---|
| `dashboard.html`, `dashboard.js`, `layout.html`, `style.css`, `data.js` | Dashboard front end |
| `update_ph_task.py`, `verify_ph_task.py`, `publish_dashboards.py` | Publish + verification scripts |
| `build_standalone.py`, `merge_standalone.py` | Standalone build |
| `export_data*.py`, `export_epd*.py` | Data export |
| `validate_charts.py`, `validate_range.py`, `validate_harness.js`, `validate_range.js` | Validation harness |
| `automation/` | config, generator, publisher, monthly runner, validator |
| `dist/` | Published dashboard output |
| `archive/`, `logs/` | Prior versions and run logs |

`03_DEVELOPMENT/` holds development **notes** only — no copies of the above.

## AIOS Documentation Sections

| Folder | Purpose |
|---|---|
| 01_REQUIREMENTS | Daily requirement, analysis, scope, checklist |
| 02_DISCOVERY | Publish convention, PostgreSQL/MCP findings, DB mapping, gap analysis |
| 03_DEVELOPMENT | Deployment notes, implementation log |
| 04_SQL | Update, verification, deployment-validation, rollback queries |
| 05_VALIDATION | Deployment/SHA256/campaign-filter validation and test reports |
| 06_EVIDENCE | Deployment logs, MCP verification, SQL output, screenshots, SHA256 results |
| 07_DEPLOYMENT | Deployment/publish/rollback procedures, checklist, release notes |
| 08_DOCUMENTATION | Skill file, business rules, user + technical docs, lessons, change log |
| 09_REUSABLE_KNOWLEDGE | Reusable patterns and parent-AIOS candidates |

Sections 01–09 are complete. Start with `06_EVIDENCE/Evidence_Index.md` and
`08_DOCUMENTATION/Technical_Documentation.md`.

Not in Git (production data or generated output): `data.js`, `dashboard.html`, `dist/`,
`epd_ph_task_export_*.csv`, `_harness_*`. Regenerate with `07_DEPLOYMENT/Deployment_Process.md`.

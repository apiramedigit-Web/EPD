# Parent AIOS Candidates

Items from this project that may be worth promoting to the Parent AIOS. They are **candidates
only**; nothing has been changed in the Parent AIOS.

| # | Candidate | Source in this project | Why reusable |
|---|---|---|---|
| 1 | Dashboard Publishing Standard | `Dashboard_Publishing_Standard.md` | Every ph_task dashboard has the same row, transfer and proof needs |
| 2 | SHA-256 validation pattern | `SHA256_Validation_Pattern.md`, `update_ph_task.py` | Only reliable proof that multi-MB content arrived intact |
| 3 | Assigned User personalisation | `Assigned_User_Personalization.md` | Team-wide distribution through one row per member |
| 4 | Daily-fact dashboard data model (`dim` + `daily` + `dates`) | `export_data_daily.py`, `dashboard.js` | Any date-filterable standalone dashboard |
| 5 | Headless validation of real front-end JS | `validate_harness.js`, `validate_range.js` | Reconciles what users actually see with SQL, without a browser |
| 6 | Grain rule for PPC performance (campaign rows else ad rows) | `export_data_daily.py` `DAILY_SQL` | Stops double counting in any eBay PPC report |
| 7 | "Snapshot drift" note for validation evidence | `05_VALIDATION/Dashboard_Test_Report.md` § D | Explains later FAILs that are unrelated to code |
| 8 | Public-repo exclusion list for data-embedding dashboards | `.gitignore` | Stops production data leaking to public GitHub |

## Suggested owner action

Review 1, 2 and 8 first. They are process rules with no project-specific logic.

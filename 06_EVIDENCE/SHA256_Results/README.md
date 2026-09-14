# SHA-256 Results

| File | Content |
|---|---|
| `ph_task_epd_rows_2026-09-14.txt` | Read-only listing of every `project_code = 'epd'` row with length and SHA-256 of `html_content` (content itself not included) |
| `local_file_sha256_2026-09-14.txt` | `sha256sum` of `dashboard.html`, `data.js`, `dashboard.js`, `layout.html`, `style.css` and the D01 `dist/*.html` files |

Interpretation: `../../05_VALIDATION/SHA256_Verification_Report.md`.

The `dist/*_V002.html` hashes identify the D01 files that could be used for a rollback
(see `../../04_SQL/rollback_queries.sql`). Those files are kept locally, not in Git.

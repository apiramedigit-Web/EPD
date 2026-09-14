# MCP / Database Access Discovery

## How the project reaches PostgreSQL

Every script connects with `psycopg.connect(os.environ["DATABASE_URL"])`. No connection string,
host or password is stored in the repository.

| Script | Access |
|---|---|
| `export_data.py`, `export_data_daily.py` | read |
| `validate_charts.py`, `validate_range.py`, `verify_ph_task.py` | read |
| `export_epd_csv.py`, `export_epd_query_csv.py` | read (writes a local CSV) |
| `publish_dashboards.py` | INSERT into `tech_team_outputs.ph_task` |
| `update_ph_task.py` | UPDATE `tech_team_outputs.ph_task` |
| `automation/*` | read + INSERT (monthly pipeline) |

## Why a Python driver instead of an MCP SQL tool for writes

Each `html_content` value is about 3.9 million characters. That is far too large to pass inline
through an MCP `execute_sql` call. Parameterised psycopg statements send it as a bound value,
and the SHA-256 check runs server-side in the same transaction.

## Connected database

`current_database()` returns `order_management_copy`. Both the data tables (`public.*`) and the
output table (`tech_team_outputs.ph_task`) are in this database.

## Verification method used on 2026-09-14

Read-only queries (`SET TRANSACTION READ ONLY` for ad-hoc checks) plus the project's own
`verify_ph_task.py`. Outputs are in `06_EVIDENCE/MCP_Verification/` and `06_EVIDENCE/SHA256_Results/`.

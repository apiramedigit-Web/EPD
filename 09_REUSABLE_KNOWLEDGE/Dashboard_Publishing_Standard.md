# Dashboard Publishing Standard (ph_task)

Derived from REQ-07. Applies to standalone HTML dashboards delivered through
`tech_team_outputs.ph_task`.

## Artefact

- [ ] One self-contained `.html` file: inline CSS, JS and data; no `src=`/`href=` to local files; no CDN.
- [ ] Embedded data carries `generated_at`, source tables and the reporting date field.
- [ ] A visible integrity banner or footnote states what the data reconciles to.
- [ ] Built by a script from source parts, never edited by hand.

## Rows

- [ ] One row per assigned user; identical content apart from the Assigned User line.
- [ ] `task_id` pattern `<project_code>_<user>_<slug>_<period>`; check existence before insert (no unique constraint).
- [ ] New task/version → INSERT. Refresh of the same task → UPDATE `html_content` + `updated_at` only.
- [ ] Never overwrite a `version_status` set by the assigned user.

## Transfer

- [ ] Send `html_content` as a bound driver parameter (psycopg), never inline SQL or MCP text.
- [ ] Credentials from environment variables only; never echoed or written to disk.

## Proof

- [ ] SHA-256 (`convert_to(html_content,'UTF8')`) and `length()` equal the source, per row.
- [ ] Commit only after every row verifies; otherwise roll back all.
- [ ] Separate read-only verification script, run after publishing.
- [ ] Console output saved to `06_EVIDENCE/` with the data timestamp.

## Repository

- [ ] Source, SQL, validation scripts and documentation in Git.
- [ ] Generated data files, per-user outputs and DB exports excluded when the repository is public.

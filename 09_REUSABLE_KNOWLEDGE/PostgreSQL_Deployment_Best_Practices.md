# PostgreSQL Deployment Best Practices

Lessons applied in REQ-07 when writing to production PostgreSQL.

1. **Read-only by default.** Discovery, validation and verification use SELECT only
   (`SET TRANSACTION READ ONLY` for ad-hoc checks). The only write is the intended UPDATE/INSERT.
2. **Credentials from the environment.** `psycopg.connect(os.environ["DATABASE_URL"])`. Print
   `current_database()` to confirm the target, never the URL.
3. **Bind large values.** Multi-megabyte text goes through driver parameters. Inline literals
   break quoting and exceed tool limits.
4. **Explicit transaction, verify inside it.** Run the UPDATE, then re-read in the same
   transaction and compare hashes. `commit()` only if everything matches, otherwise `rollback()`.
5. **Select before you write.** Check that the target row exists (UPDATE) or does not exist
   (INSERT) by business key, because `task_id` has no unique constraint.
6. **Change the minimum.** Update only the columns the release needs (`html_content`,
   `updated_at`). Leave `created_at`, versions and user-set statuses alone.
7. **Use `RETURNING`.** Capture `id` and `updated_at` from the write itself for the evidence log.
8. **Hash in the database.** `encode(sha256(convert_to(col,'UTF8')),'hex')` compares directly
   with Python `hashlib.sha256(text.encode('utf-8'))`.
9. **Watch `%` with psycopg.** When parameters are passed, a literal `%` in SQL (e.g. `LIKE '%x%'`)
   must be written `%%`, as in `verify_ph_task.py`.
10. **Plan the rollback before the write.** The table keeps no history, so keep the previous
    content (file or export) and its SHA-256 before updating.
11. **Reconcile against independent SQL.** Totals from a separately written query catch grain and
    join errors that a single query cannot reveal.

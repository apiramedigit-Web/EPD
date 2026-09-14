# Pattern — SHA-256 Content Validation (Python ↔ PostgreSQL)

## Purpose

Prove that a large text value stored in PostgreSQL is byte-for-byte the content that was built.

## Python side

```python
import hashlib
content = template.replace(PLACEHOLDER, user)          # exact string sent to the DB
src_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
src_len = len(content)                                  # characters, not bytes
```

## Database side

```sql
SELECT length(html_content)                                    AS char_len,
       encode(sha256(convert_to(html_content, 'UTF8')), 'hex') AS sha256
FROM tech_team_outputs.ph_task
WHERE id = %s;
```

## Rules

1. Hash the **string you send**, not a file re-read with different newline handling. Write files
   with `newline=""` and read them as UTF-8 text.
2. Compare **characters** with `length()`; `octet_length()` would give bytes.
3. Check **both** hash and length; a length mismatch explains a hash mismatch faster.
4. Verify **inside the write transaction** and commit only when all rows pass.
5. Afterwards, re-verify **read-only** from a separate script against the current on-disk build.
6. Record hashes in evidence so a future local file can be matched to a release.

## Worked result (REQ-07 D02, 2026-09-14)

| id | length | SHA-256 | match |
|---|---|---|---|
| 395 | 3,918,506 | `5b32a168…25b41c` | True |
| 396 | 3,918,506 | `e9f09143…68032` | True |
| 397 | 3,918,505 | `61530c64…998edb` | True |
| 398 | 3,918,508 | `a2505e15…159ca2` | True |

References: `Dashboard/update_ph_task.py`, `Dashboard/verify_ph_task.py`,
`05_VALIDATION/SHA256_Verification_Report.md`.

# Pattern — Assigned User Personalisation

**Problem:** several people receive the same dashboard through `ph_task`, one row each, and each
copy must show whose it is.

## Pattern

1. Build **one** base HTML with no user name.
2. Choose an **inject target** that occurs exactly once in the base, e.g.
   `<span>Reporting Period: <b id="hdr-month">—</b></span>`.
3. Make a template: replace the target with
   `<span>Assigned User : <b id="hdr-user">__ASSIGNED_USER__</b></span>` + newline + target.
4. Assert `count(target) == 1` in the base and `count(placeholder) == 1` in the template.
   Abort otherwise.
5. Per user: `content = template.replace(placeholder, user)`; publish; verify
   SHA-256(content) against the DB.

## Why it works

- Only one line differs between users, so every copy is provably the same dashboard: SHA
  differences come only from the name.
- The count assertions stop silent failures when the layout changes (0 matches) and double
  injection (2 matches).
- A stable element id (`hdr-user`) lets verification check the name with a simple `LIKE`.

## Watch out

- Keep the inject target in step with the layout. D01 used "Reporting Month"; D02 changed it to
  "Reporting Period", so each publisher carries its own target.
- Take the user list from the team roster (`assigned_user_team`), not from memory.

Reference implementation: `Dashboard/update_ph_task.py`, `Dashboard/publish_dashboards.py`.

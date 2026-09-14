# SHA-256 Verification Report

Checked 2026-09-14. Raw outputs: `06_EVIDENCE/SHA256_Results/`.

## Method

- Python: `hashlib.sha256(text.encode("utf-8"))` over the exact per-user HTML string.
- PostgreSQL: `encode(sha256(convert_to(html_content,'UTF8')),'hex')`.
- Per-user HTML = base `dashboard.html` with the Assigned User line inserted before
  `<span>Reporting Period: <b id="hdr-month">—</b></span>`.

## Stored rows

| id | User | char length | SHA-256 (database) | Matches per-user build |
|---|---|---|---|---|
| 395 | Thinesh | 3,918,506 | `5b32a1687170a320d48f8331f121fc26fe7daf9bda47c58e19c934c26525b41c` | True |
| 396 | Jarsini | 3,918,506 | `e9f09143c4a95fad966edf002c6d7a36d1c77cb9fc454e629eaf1c25bab68032` | True |
| 397 | kobiga | 3,918,505 | `61530c6473d90c9241aeeaf4f01c3fda19543320a2bc7e373a6d113328998edb` | True |
| 398 | powsteena | 3,918,508 | `a2505e152d86debb48de0ca769e416d474d149afe5474cd14cd3618e85159ca2` | True |

Lengths differ only by the user name's length (7, 7, 6, 9 characters).

## Local build files

| File | SHA-256 |
|---|---|
| `Dashboard/dashboard.html` | `5d5fc4134feea1e9d7e56be73c982ce0f2087d4043b155b23097b6bdf814b95f` |
| `Dashboard/data.js` | `94e0cf8c1d38c113000d9f6d0be7328a4a62320acf3612004297bda841ae9b69` |
| `Dashboard/dashboard.js` | `be6cb8fb12a34d757c06419ef6e4b1018a8f3a616a15d69fbe07d86c5a437f06` |
| `Dashboard/layout.html` | `225ac0cec99b15d8bc689680a4954a89e30b416dcb064564316fb5bfcbb40f6d` |
| `Dashboard/style.css` | `654274e9999e46cfe0b598d74f5cf2137f1a35d181cc6ae45ccf8116d7df2fb6` |

## Reproducibility

Re-assembling `style.css + layout.html + data.js + dashboard.js` with the `build_standalone.py`
template gives the same SHA-256 as `dashboard.html` (checked 2026-09-14: True). The deployed
content can be rebuilt exactly from source plus `data.js`.

Note: `data.js` and `dashboard.html` are not in Git (they contain production data). Their
hashes are recorded here so a local copy can be matched to this release.

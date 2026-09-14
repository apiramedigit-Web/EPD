# Screenshots

No screenshots were captured for REQ-07 / D02.

The dashboard's behaviour was validated by running its real JavaScript headless
(`Dashboard/validate_harness.js`, `Dashboard/validate_range.js`) and reconciling the output
with SQL. That proves the numbers, not the visual layout.

To add visual evidence, open `Dashboard/dashboard.html` locally (not in Git — rebuild it with
`build_standalone.py`). Save images here as `<view>_YYYY-MM-DD.png`, for example
`campaign_type_filter_2026-06.png`. Crop out anything beyond what the dashboard shows.

# Reusable Lessons

Short rules from REQ-07 that apply beyond this dashboard.

| Rule | Because |
|---|---|
| Export facts at the finest grain users will filter on | Pre-aggregated data cannot be re-sliced by date |
| Fix one metric grain per entity and reuse it in every query | Mixed campaign/ad rows double count |
| Derive ratios from summed totals, never average the ratios | Averaged ACOS/ROAS mislead on small campaigns |
| "Today" in a snapshot = latest data date | The viewer's clock does not match the data |
| Start/created dates are attributes, not period filters | Users ask about activity in a period |
| Validate the shipped JS, not a copy of its logic | Re-implementations hide front-end bugs |
| Choose an unchanged historical period as the regression baseline | Recent periods receive late data |
| Compare hashes, not "looks right" | Multi-MB HTML differences are invisible |
| Update in place for refreshes; insert only for new tasks/versions | Avoid duplicate cards for users |
| Save console output during the release | Reconstructing evidence later is slow and incomplete |
| Keep automation in step with every layout change | A stale pipeline silently breaks the next scheduled run |
| Set `PYTHONIOENCODING=utf-8` on Windows | Unicode arrows/dashes crash cp1252 consoles |
| Keep production data out of public repositories | Standalone dashboards embed the full dataset |

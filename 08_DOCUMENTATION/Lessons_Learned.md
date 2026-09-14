# Lessons Learned — REQ-07

1. **Aggregated exports cannot support date filters.** D01 stored one total per campaign, so a
   date filter could only hide rows. Exporting daily facts and re-aggregating in the browser made
   every KPI, chart and export correct for any period.

2. **Pick one metric grain per campaign.** `ppc_performance` holds both campaign- and ad-level
   rows. Summing both double counts. The "prefer campaign, else ad" rule has to be the same in
   the export, the totals SQL and every validation query.

3. **Validate the real front-end code, not a re-implementation.** Running `dashboard.js` headless
   in Node and reconciling its KPIs, charts and CSV with SQL caught behaviour that static checks
   cannot.

4. **Build-time reconciliation belongs in the exporter.** `export_data_daily.py` refuses to
   succeed unless daily facts equal independently queried totals. It still writes `data.js`
   before checking, though, so the order of operations matters.

5. **Update in place with verification, not insert.** Re-publishing D02 as new rows would have
   duplicated tasks for users. UPDATE by `task_id`, with SHA-256 comparison and a single commit,
   kept one row per user and made the change provable.

6. **Snapshots go stale — label them.** Five weeks after deployment, production had 147 more
   campaigns and late data for past months. Validation scripts that compare with live SQL then
   fail for reasons unrelated to code. Future evidence should be captured at deploy time and
   tagged with the data timestamp.

7. **Keep evidence as you go.** The deployment console output was not saved, so the timeline had
   to be reconstructed from file times and `updated_at`. Save script output into `06_EVIDENCE/`
   during the release.

8. **Keep automation in step with the front end.** `automation/` was written for the D01 layout
   and was not updated for D02. The monthly pipeline would fail on the current build.

9. **Windows console encoding.** Scripts that print `→` or `—` crash under cp1252. Set
   `PYTHONIOENCODING=utf-8`.

10. **Separate code from data in public repositories.** The dashboard HTML embeds the full
    production dataset. Only source, SQL and documentation belong in a public repository;
    generated data files stay local.

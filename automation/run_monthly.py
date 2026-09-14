#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_monthly.py — main orchestrator for the eBay PPC monthly dashboard pipeline.

Flow:  compute previous month -> connect PostgreSQL -> generate per-user dashboards
       -> validate -> (if PASS) publish ph_task -> archive -> log.

If validation FAILS the pipeline STOPS, writes an error log, and does NOT publish.

Usage:
  python run_monthly.py                 # normal monthly run (previous complete month)
  python run_monthly.py --dry-run       # generate+validate+archive, no DB writes
  python run_monthly.py --month 2026-07 # force a specific reporting month (back-fill/test)
"""
import os, sys, json, shutil, argparse, traceback
import datetime as dt

import config
import generate_dashboard as generate
import validate_dashboard as validate
import publish_ph_task as publish


class Logger:
    def __init__(self, path):
        self.path = path
        self.fh = open(path, "a", encoding="utf-8")
    def __call__(self, msg):
        # NOTE: real wall-clock time is fine here (standard Python, not a workflow script)
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts}  {msg}"
        print(line)
        self.fh.write(line + "\n"); self.fh.flush()
    def close(self):
        self.fh.close()


def archive(files, rep, log):
    dest = os.path.join(config.ARCHIVE_DIR, rep["window_start"])   # archive/<reporting-month-1st>/
    os.makedirs(dest, exist_ok=True)
    for f in files:
        shutil.copy2(f["path"], os.path.join(dest, f["name"]))
    log(f"Archived {len(files)} dashboards -> {dest}")
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="no DB writes; generate+validate+archive only")
    ap.add_argument("--month", help="force reporting month YYYY-MM (default: previous month)")
    args = ap.parse_args()

    config.ensure_dirs()
    run_dt = dt.date.today()
    rep = config.compute_reporting(run_dt, args.month)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = Logger(os.path.join(config.LOGS_DIR, f"run_{rep['reporting_month']}_{stamp}.log"))
    exit_code = 0
    try:
        log("Pipeline Started" + (" [DRY-RUN]" if args.dry_run else ""))
        log(f"Run date {rep['run_date']}  ->  Reporting Month {rep['reporting_label']} "
            f"({rep['window_start']} .. {rep['window_end']})")

        # 1) version (auto-increment) — needed for filenames
        with config.connect() as conn, conn.cursor() as cur:
            version = publish.get_next_version(cur)
        log(f"Connected PostgreSQL. Next version_level = {version} (V{version:03d})")

        # 2) generate
        manifest = generate.generate(rep, version, log=log)
        log("Generated Dashboard(s)")

        # 3) validate  ->  STOP on any failure
        ok, report = validate.validate(rep, manifest["files"], log=log)
        if not ok:
            log("VALIDATION FAILED — pipeline stopped, nothing published.")
            log("Failing checks: " + json.dumps([{f["file"]: f.get("failed")} for f in report["files"] if not f["ok"]]))
            log("Completed with ERRORS")
            exit_code = 2
            return
        log("Validation Passed")

        # 4) publish (skipped in dry-run)
        results = publish.publish(rep, manifest["files"], version, dry_run=args.dry_run, log=log)
        inserted = [r for r in results if r["status"].startswith("INSERTED OK")]
        log(f"Published {len(inserted)} Dashboards" + (" (dry-run: 0 written)" if args.dry_run else ""))

        # 5) archive
        archive(manifest["files"], rep, log)

        # 6) summary
        log("Completed Successfully")
        print("\n================ MONTHLY PIPELINE SUMMARY ================")
        print(f"Reporting Month : {rep['reporting_label']}  ({rep['reporting_month']})")
        print(f"Window          : {rep['window_start']} .. {rep['window_end']}")
        print(f"Version         : V{version:03d}")
        print(f"Validation      : PASS")
        print(f"{'Assigned User':<12} | {'File':<42} | {'Task ID':<44} | {'Row ID':<7} | Status")
        print("-"*130)
        for r in results:
            print(f"{r['user']:<12} | {next(f['name'] for f in manifest['files'] if f['user']==r['user']):<42} | "
                  f"{r['task_id']:<44} | {str(r.get('id','-')):<7} | {r['status']}")
    except Exception:
        log("PIPELINE ERROR:\n" + traceback.format_exc())
        log("Completed with ERRORS")
        exit_code = 1
    finally:
        log.close()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

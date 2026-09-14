#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
config.py — shared configuration and helpers for the eBay PPC monthly pipeline.

Nothing here is hardcoded business data: only structural constants (team roster,
project identifiers, paths) and pure date arithmetic. All metrics come from SQL.
"""
import os
import datetime as dt

import psycopg

# ---------------------------------------------------------------- paths
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR    = os.path.dirname(AUTOMATION_DIR)                 # ebay_ppc_dashboard/
TEMPLATE_HTML  = os.path.join(PROJECT_DIR, "dashboard.html")     # single frontend source of truth
OUTPUT_DIR     = os.path.join(AUTOMATION_DIR, "output")          # latest run's generated files
ARCHIVE_DIR    = os.path.join(PROJECT_DIR, "archive")
LOGS_DIR       = os.path.join(PROJECT_DIR, "logs")

# ---------------------------------------------------------------- constants
SOURCE_EBAY   = 2
PROJECT_NAME  = "eBay PPC Performance Dashboard"
PROJECT_CODE  = "epd"
TASK_PREFIX   = "REQ-07-D01 eBay PPC Performance Dashboard"      # + " — <Reporting Label>"
DEVELOPER     = "Apirame"
DEV_TEAM      = "Development"
ASSIGNED_TEAM = "ebay_priors"
USERS         = ["Thinesh", "Jarsini", "kobiga", "powsteena"]   # ebay_priors roster

DESCRIPTION_TMPL = (
    "eBay PPC Performance Dashboard ({label}) showing campaign-level advertising performance "
    "including Total Sales, Orders, Ad Spend, ACOS, ROAS, CPC, CTR, Conversion Rate, AOV, "
    "KPI Summary, Filters, Campaign Performance Table, Charts and CSV Export. Built entirely "
    "from live PostgreSQL production data. HTML is fully standalone with embedded CSS, "
    "JavaScript and production data.")

CURRENCY_NOTE = ("Values are in each marketplace's native currency (GBP/EUR/USD); not FX-normalised.")
SOURCE_TABLES = ["public.ppc", "public.ppc_performance", "public.listing_data"]


# ---------------------------------------------------------------- db
def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg.connect(url)


# ---------------------------------------------------------------- date logic
def _add_months(d: dt.date, n: int) -> dt.date:
    """First day of month d shifted by n months."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    return dt.date(y, m, 1)


def compute_reporting(run_date: dt.date, override_month: str | None = None) -> dict:
    """
    Given the run date (normally the 1st of the current month), return the PREVIOUS
    complete calendar month as the reporting window. override_month ('YYYY-MM')
    forces a specific reporting month (for testing / back-fill).
    """
    if override_month:
        y, m = map(int, override_month.split("-"))
        m_start = dt.date(y, m, 1)
    else:
        first_of_this = run_date.replace(day=1)
        m_start = _add_months(first_of_this, -1)          # first day of previous month
    m_end = _add_months(m_start, 1) - dt.timedelta(days=1)  # last day of that month
    trend_start = _add_months(m_start, -12)                 # 13-month trailing window

    return {
        "run_date":       run_date.isoformat(),
        "reporting_month": m_start.strftime("%Y-%m"),        # e.g. 2026-07
        "reporting_label": m_start.strftime("%B %Y"),        # e.g. July 2026
        "window_start":   m_start.isoformat(),               # 2026-07-01
        "window_end":     m_end.isoformat(),                 # 2026-07-31
        "trend_start":    trend_start.isoformat(),           # 12 months earlier
    }


def ensure_dirs():
    for p in (OUTPUT_DIR, ARCHIVE_DIR, LOGS_DIR):
        os.makedirs(p, exist_ok=True)


def filename_for(run_date: str, user: str, version: int) -> str:
    return f"{run_date}_{user}_dashboard_V{version:03d}.html"

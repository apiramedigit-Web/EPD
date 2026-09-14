#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
merge_standalone.py — embed data.js into dashboard.html so the dashboard is a
single, fully self-contained file with NO external dependencies.

- Reads dashboard.html and data.js exactly as they exist.
- Replaces the single line  <script src="data.js"></script>  with an inline
  <script> block containing the verbatim contents of data.js.
- Escapes any literal '</script' inside the data to '<\\/script' (JS-parses
  identically, so no data value changes) to keep the HTML valid.
- Adds a one-line alias  window.dashboardData = window.DASHBOARD_DATA;  so the
  data is reachable under both names (data itself is untouched).
- Saves dashboard.html and prints a validation report.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "dashboard.html")
DATA = os.path.join(HERE, "data.js")

MARKER = '<script src="data.js"></script>'

def main():
    html = open(HTML, encoding="utf-8").read()
    data = open(DATA, encoding="utf-8").read()

    # 1) marker must exist exactly once
    n = html.count(MARKER)
    if n != 1:
        print(f"ERROR: expected exactly 1 '{MARKER}', found {n}. Aborting.")
        sys.exit(1)

    # 2) make the data safe to sit inside an inline <script> (values unchanged)
    unsafe = data.count("</script")
    data_safe = data.replace("</script", "<\\/script")

    # 3) build the inline data block (verbatim data + name alias per spec)
    inline = (
        "<script>\n"
        "/* ---- Embedded production data — verbatim copy of data.js ---- */\n"
        + data_safe.rstrip("\n") + "\n"
        "window.dashboardData = window.DASHBOARD_DATA;  /* alias: same object, both names available */\n"
        "</script>"
    )

    # 4) replace ONLY that line
    new_html = html.replace(MARKER, inline)

    # 5) save
    open(HTML, "w", encoding="utf-8").write(new_html)

    # 6) validate
    checks = [
        ("no external data.js reference", 'src="data.js"' not in new_html),
        ("no external dashboard.js reference", 'src="dashboard.js"' not in new_html),
        ("no external style.css reference", 'href="style.css"' not in new_html),
        ("no stylesheet <link>", 'rel="stylesheet"' not in new_html),
        ("window.DASHBOARD_DATA present", "window.DASHBOARD_DATA" in new_html),
        ("window.dashboardData present", "window.dashboardData" in new_html),
        ("<style> balanced", new_html.count("<style>") == 1 and new_html.count("</style>") == 1),
        ("no leftover </script inside data", ("</script" not in data_safe)),
    ]
    print("=== MERGE COMPLETE ===")
    print("dashboard.html bytes :", os.path.getsize(HTML))
    print("data.js bytes        :", len(data))
    print("'</script' escaped   :", unsafe)
    print("script tags total    :", new_html.count("<script"))
    print("--- validation ---")
    ok = True
    for name, res in checks:
        print(("  PASS  " if res else "  FAIL  ") + name)
        ok = ok and res
    print("RESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
    sys.exit(0 if ok else 2)

if __name__ == "__main__":
    main()

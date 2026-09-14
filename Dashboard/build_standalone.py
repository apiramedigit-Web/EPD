#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
build_standalone.py — assemble the single standalone dashboard.html from the
source parts (style.css + layout.html + data.js + dashboard.js). No external files.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
def rd(name): return open(os.path.join(HERE, name), encoding="utf-8").read()

css    = rd("style.css")
layout = rd("layout.html").rstrip("\n")
data   = rd("data.js").rstrip("\n").replace("</script", "<\\/script")
logic  = rd("dashboard.js").rstrip("\n")
assert "</script" not in logic, "dashboard.js contains a literal </script"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>eBay PPC Performance Dashboard</title>
  <style>
{css}
  </style>
</head>
<body>
{layout}
  <!-- Embedded production data (per-campaign daily reporting facts) -->
  <script>
{data}
  </script>
  <!-- Dashboard logic -->
  <script>
{logic}
  </script>
</body>
</html>
"""

out = os.path.join(HERE, "dashboard.html")
with open(out, "w", encoding="utf-8", newline="") as f:
    f.write(html)

print("wrote", out, "bytes:", os.path.getsize(out))
for tok in ['rel="stylesheet"', 'src="data.js"', 'src="dashboard.js"', 'src="style.css"']:
    print(f"  external {tok:<22}: {'PRESENT (BAD)' if tok in html else 'none'}")
print("  <style> blocks :", html.count("<style>"), "/", html.count("</style>"))
print("  <script blocks :", html.count("<script"))
print("  window.DASHBOARD_DATA:", "window.DASHBOARD_DATA" in html)
print("  window.dashboardData :", "window.dashboardData" in html)

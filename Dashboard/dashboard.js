/* ============================================================================
   eBay PPC Performance Dashboard — dashboard.js
   Date Range filters the REPORTING PERIOD using public.ppc_performance.date.
   Each campaign's metrics are re-aggregated client-side from per-day facts over
   the selected reporting window, so KPIs, table, charts, pagination, CSV export,
   search results and performance counts all reflect the chosen reporting period.
   Campaign Start Date is a display-only dimension column (never used for filtering).
   All values come from window.DASHBOARD_DATA (rebuilt from production PostgreSQL).
   ========================================================================== */
(function () {
  "use strict";

  const DATA = window.DASHBOARD_DATA;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  if (!DATA || !Array.isArray(DATA.dim) || !Array.isArray(DATA.daily)) {
    $("#tbl-skeleton") && $("#tbl-skeleton").classList.add("hidden");
    $("#tbl-error") && $("#tbl-error").classList.remove("hidden");
    return;
  }

  // -------------------------------------------------- schema
  const COLS = DATA.columns, KEYS = COLS.map((c) => c.key);
  const TYPE = {}; COLS.forEach((c) => (TYPE[c.key] = c.type));
  const LABEL = {}; COLS.forEach((c) => (LABEL[c.key] = c.label));
  const NUMERIC = new Set(["daily_budget","total_sales","order_qty","ad_spend","acos","roas","avg_cpc","clicks","impressions","ctr","conversion_rate","aov"]);
  const DIM_COLS = DATA.dim_cols, DI = {}; DIM_COLS.forEach((k, i) => (DI[k] = i));
  const DATES = DATA.dates, NDATES = DATES.length, DIM = DATA.dim, DAILY = DATA.daily;
  const DMIN = DATA.meta.date_min, DMAX = DATA.meta.date_max, TODAY = DATA.meta.today_date;

  // -------------------------------------------------- formatting
  const nf = (v, dp) => Number(v).toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp });
  const money = (v) => (v == null ? "—" : "£" + nf(v, 2));
  const pct = (v) => (v == null ? "—" : nf(v, 2) + "%");
  const num2 = (v) => (v == null ? "—" : nf(v, 2));
  const int0 = (v) => (v == null ? "—" : nf(v, 0));
  const fmtByType = (t, v) => t === "money" ? money(v) : t === "pct" ? pct(v) : t === "num" ? num2(v)
      : t === "int" ? int0(v) : t === "date" ? (v || "—") : (v == null || v === "" || v === "N/A" ? "—" : String(v));
  function fmtDateTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso); if (isNaN(d)) return String(iso).slice(0, 16).replace("T", " ");
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
  }
  const shortMoney = (v) => { const a = Math.abs(v);
    return a >= 1e6 ? "£" + (v / 1e6).toFixed(1) + "M" : a >= 1e3 ? "£" + (v / 1e3).toFixed(1) + "k" : "£" + Math.round(v); };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const r2 = (v) => v == null ? null : Math.round(v * 100) / 100;

  const ICON = { campaigns:'<path d="M3 5h18v4H3zM3 13h12v6H3z"/>', active:'<path d="M20 6L9 17l-5-5"/>',
    pause:'<path d="M8 5v14M16 5v14"/>', spend:'<path d="M12 1v22M17 5H9a3 3 0 000 6h6a3 3 0 010 6H7"/>',
    sales:'<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>', orders:'<path d="M6 2l1.5 3h9L18 2M4 5h16l-1.5 12a2 2 0 01-2 1.7H7.5a2 2 0 01-2-1.7z"/>',
    acos:'<circle cx="12" cy="12" r="9"/><path d="M9 15l6-6M9 9h.01M15 15h.01"/>', roas:'<path d="M3 17l6-6 4 4 7-8"/><path d="M14 7h5v5"/>',
    cpc:'<path d="M9 11l3 3 8-8"/><path d="M20 12a8 8 0 11-4.5-7.2"/>', clicks:'<path d="M9 3v6l7 3-7 3v6"/>',
    impr:'<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    ctr:'<path d="M4 20l7-7 3 3 6-6"/>', cvr:'<path d="M12 2a10 10 0 100 20 10 10 0 000-20z"/><path d="M8 12l3 3 5-6"/>',
    aov:'<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2"/>',
    today:'<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    sync:'<path d="M21 12a9 9 0 11-3-6.7L21 8"/><path d="M21 3v5h-5"/>' };
  const icoSvg = (k) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${ICON[k] || ""}</svg>`;

  // -------------------------------------------------- date helpers (reporting date)
  function isoAddDays(iso, n) { const d = new Date(iso + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  const firstOfMonth = (iso) => iso.slice(0, 8) + "01";
  const clampFrom = (iso) => (iso < DMIN ? DMIN : iso > DMAX ? DMAX : iso);
  const clampTo = (iso) => (iso > DMAX ? DMAX : iso < DMIN ? DMIN : iso);
  function lowerIdx(iso) { let lo = 0, hi = NDATES; while (lo < hi) { const m = (lo + hi) >> 1; if (DATES[m] < iso) lo = m + 1; else hi = m; } return lo; }
  function upperIdx(iso) { let lo = 0, hi = NDATES; while (lo < hi) { const m = (lo + hi) >> 1; if (DATES[m] <= iso) lo = m + 1; else hi = m; } return lo - 1; }
  function presetRange(name) {
    const t = TODAY;
    switch (name) {
      case "today": return [t, t];
      case "yesterday": { const y = isoAddDays(t, -1); return [y, y]; }
      case "last7": return [isoAddDays(t, -6), t];
      case "last30": return [isoAddDays(t, -29), t];
      case "thismonth": return [firstOfMonth(t), t];
      case "lastmonth": { const prevLast = isoAddDays(firstOfMonth(t), -1); return [firstOfMonth(prevLast), prevLast]; }
      default: return null;   // custom
    }
  }
  const PRESETS = [["today","Today"],["yesterday","Yesterday"],["last7","Last 7 Days"],
    ["last30","Last 30 Days"],["thismonth","This Month"],["lastmonth","Last Month"],["custom","Custom Range"]];

  // -------------------------------------------------- state
  const RANGE = { from: null, to: null, preset: DATA.meta.default_preset || "last30" };
  function applyPreset(name) {
    const r = presetRange(name);
    if (r) { RANGE.from = clampFrom(r[0]); RANGE.to = clampTo(r[1]); RANGE.preset = name; }
    else { RANGE.preset = "custom"; }
  }
  applyPreset(RANGE.preset);

  const FILTERS = { account: "", marketplace: "", campaignType: "", status: "", performance: "", acosMin: null, acosMax: null, roasMin: null, roasMax: null, search: "" };
  let SORT = { key: "ad_spend", dir: "desc" };
  let PAGE = 1, PAGE_SIZE = 25;
  const SELECTED = new Set(), HIDDEN = new Set();
  let autoTimer = null;

  // -------------------------------------------------- Today's Spend (latest reporting date)
  let TODAY_SPEND = 0; const lastDi = NDATES - 1;
  for (const entries of DAILY) for (let k = entries.length - 1; k >= 0; k--) {
    if (entries[k][0] === lastDi) { TODAY_SPEND += entries[k][3]; break; } if (entries[k][0] < lastDi) break;
  }
  TODAY_SPEND = r2(TODAY_SPEND);

  // -------------------------------------------------- build rows for the reporting window
  let ROWS = [];
  function buildRows() {
    const lo = lowerIdx(RANGE.from), hi = upperIdx(RANGE.to), empty = lo > hi;
    const rows = new Array(DIM.length);
    for (let j = 0; j < DIM.length; j++) {
      let impr = 0, clk = 0, sp = 0, sa = 0, orr = 0; const e = DAILY[j];
      if (!empty) for (let k = 0; k < e.length; k++) { const di = e[k][0]; if (di < lo) continue; if (di > hi) break;
        impr += e[k][1]; clk += e[k][2]; sp += e[k][3]; sa += e[k][4]; orr += e[k][5]; }
      sp = r2(sp); sa = r2(sa);
      const acos = sa > 0 ? sp / sa * 100 : null, roas = sp > 0 ? sa / sp : null,
            cpc = clk > 0 ? sp / clk : null, ctr = impr > 0 ? clk / impr * 100 : null,
            cvr = clk > 0 ? orr / clk * 100 : null, aov = orr > 0 ? sa / orr : null;
      let perf;
      if (sp === 0 || sa === 0 || clk === 0) perf = "Low";
      else if (roas >= 8 && acos <= 12 && cvr >= 8) perf = "High";
      else if (roas >= 5 && roas < 8 && acos > 12 && acos <= 20) perf = "Medium";
      else if (roas < 5 || acos > 20) perf = "Low"; else perf = "Medium";
      const d = DIM[j];
      rows[j] = { _id: j, _entries: e, month: RANGE.to.slice(0, 7),
        account: d[DI.account], marketplace: d[DI.marketplace], campaign_name: d[DI.campaign_name],
        campaign_type: d[DI.campaign_type], campaign_status: d[DI.campaign_status],
        listing_id: d[DI.listing_id], sku: d[DI.sku], product_title: d[DI.product_title],
        daily_budget: d[DI.daily_budget], start_date: d[DI.start_date],
        total_sales: sa, order_qty: orr, ad_spend: sp, clicks: clk, impressions: impr,
        acos: r2(acos), roas: r2(roas), avg_cpc: r2(cpc), ctr: r2(ctr), conversion_rate: r2(cvr), aov: r2(aov),
        performance: perf };
    }
    ROWS = rows;
  }

  // -------------------------------------------------- filtering / sorting
  const distinct = (fn) => Array.from(new Set(DIM.map(fn).filter((v) => v != null && v !== ""))).sort();
  function fillSelect(el, values, allLabel) {
    el.innerHTML = `<option value="">${allLabel}</option>` + values.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  }
  function passRange(v, mn, mx) { if (mn != null && (v == null || v < mn)) return false; if (mx != null && (v == null || v > mx)) return false; return true; }
  function getFiltered() {
    const q = FILTERS.search.trim().toLowerCase();
    return ROWS.filter((r) => {
      if (FILTERS.account && r.account !== FILTERS.account) return false;
      if (FILTERS.marketplace && r.marketplace !== FILTERS.marketplace) return false;
      if (FILTERS.campaignType && r.campaign_type !== FILTERS.campaignType) return false;
      if (FILTERS.status && r.campaign_status !== FILTERS.status) return false;
      if (FILTERS.performance && r.performance !== FILTERS.performance) return false;
      if (!passRange(r.acos, FILTERS.acosMin, FILTERS.acosMax)) return false;
      if (!passRange(r.roas, FILTERS.roasMin, FILTERS.roasMax)) return false;
      if (q) { const h = (r.campaign_name + " " + r.listing_id + " " + r.sku + " " + r.product_title).toLowerCase();
        if (h.indexOf(q) === -1) return false; }
      return true;
    });
  }
  function getSorted(rows) {
    const k = SORT.key, dir = SORT.dir === "asc" ? 1 : -1, isNum = NUMERIC.has(k);
    return rows.slice().sort((a, b) => { let x = a[k], y = b[k];
      if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
      return (isNum ? (x - y) : String(x).localeCompare(String(y))) * dir; });
  }

  // -------------------------------------------------- KPIs
  function aggregate(rows) {
    const t = { campaigns: rows.length, active: 0, paused: 0, spend: 0, sales: 0, orders: 0, clicks: 0, impressions: 0 };
    for (const r of rows) { if (r.campaign_status === "running") t.active++; if (r.campaign_status === "paused") t.paused++;
      t.spend += r.ad_spend || 0; t.sales += r.total_sales || 0; t.orders += r.order_qty || 0; t.clicks += r.clicks || 0; t.impressions += r.impressions || 0; }
    t.spend = r2(t.spend); t.sales = r2(t.sales);
    t.acos = t.sales > 0 ? t.spend / t.sales * 100 : null; t.roas = t.spend > 0 ? t.sales / t.spend : null;
    t.cpc = t.clicks > 0 ? t.spend / t.clicks : null; t.ctr = t.impressions > 0 ? t.clicks / t.impressions * 100 : null;
    t.cvr = t.clicks > 0 ? t.orders / t.clicks * 100 : null; t.aov = t.orders > 0 ? t.sales / t.orders : null;
    return t;
  }
  function renderKPIs(t) {
    const cards = [
      ["Total Campaigns", int0(t.campaigns), "accent", "campaigns", null],
      ["Active Campaigns", int0(t.active), "green", "active", "status = running"],
      ["Paused Campaigns", int0(t.paused), "orange", "pause", "status = paused"],
      ["Total Ad Spend (£)", money(t.spend), "accent", "spend", null],
      ["Attributed Sales (£)", money(t.sales), "green", "sales", null],
      ["Orders", int0(t.orders), "accent", "orders", null],
      ["Average ACOS (%)", pct(t.acos), "orange", "acos", "spend / sales"],
      ["Average ROAS", num2(t.roas), "green", "roas", "sales / spend"],
      ["Average CPC (£)", money(t.cpc), "accent", "cpc", "spend / clicks"],
      ["Total Clicks", int0(t.clicks), "accent", "clicks", null],
      ["Total Impressions", int0(t.impressions), "accent", "impr", null],
      ["Average CTR (%)", pct(t.ctr), "accent", "ctr", "clicks / impressions"],
      ["Average Conversion Rate (%)", pct(t.cvr), "green", "cvr", "orders / clicks"],
      ["Average Order Value (£)", money(t.aov), "accent", "aov", "sales / orders"],
      ["Today's Spend (£)", money(TODAY_SPEND), "orange", "today", TODAY + " snapshot"],
      ["Last Sync Time", fmtDateTime(DATA.meta.generated_at), "accent", "sync", "from production DB"],
    ];
    $("#kpi-grid").innerHTML = cards.map(([label, value, tone, ico, foot]) => `
      <div class="kpi ${tone}">
        <div class="top"><span class="label">${label}</span><span class="icon">${icoSvg(ico)}</span></div>
        <div class="value ${String(value).length > 12 ? "small" : ""}">${esc(value)}</div>
        ${foot ? `<div class="foot">${esc(foot)}</div>` : ""}
      </div>`).join("");
  }

  // -------------------------------------------------- charts
  const PERF_COLORS = { High: "#16a34a", Medium: "#f59e0b", Low: "#dc2626" };
  const STATUS_COLORS = { running: "#16a34a", paused: "#9ca3af", ended: "#64748b", deleted: "#cbd5e1" };
  const STATUS_LABEL = { running: "Active", paused: "Paused", ended: "Ended", deleted: "Deleted" };
  function emptyChart(el, msg) { el.innerHTML = `<div class="chart-empty">${msg || "No data for current reporting period"}</div>`; }

  function donut(el, entries, colorFn, labelFn) {
    const total = entries.reduce((s, e) => s + e.value, 0); if (!total) return emptyChart(el);
    const cx = 110, cy = 110, r = 78, rin = 50; let ang = -Math.PI / 2; const arcs = [];
    for (const e of entries) { if (!e.value) continue;
      const f = e.value / total, a2 = ang + f * 2 * Math.PI, big = f > 0.5 ? 1 : 0;
      const x1 = cx + r * Math.cos(ang), y1 = cy + r * Math.sin(ang), x2 = cx + r * Math.cos(a2), y2 = cy + r * Math.sin(a2);
      const xi2 = cx + rin * Math.cos(a2), yi2 = cy + rin * Math.sin(a2), xi1 = cx + rin * Math.cos(ang), yi1 = cy + rin * Math.sin(ang);
      arcs.push(`<path d="M${x1} ${y1} A${r} ${r} 0 ${big} 1 ${x2} ${y2} L${xi2} ${yi2} A${rin} ${rin} 0 ${big} 0 ${xi1} ${yi1} Z" fill="${colorFn(e)}"/>`); ang = a2; }
    const legend = entries.filter((e) => e.value).map((e) =>
      `<span class="li"><span class="dot" style="background:${colorFn(e)}"></span>${esc(labelFn(e))} — <b>${int0(e.value)}</b> (${nf(e.value / total * 100, 1)}%)</span>`).join("");
    el.innerHTML = `<svg viewBox="0 0 220 220" style="max-width:260px;margin:0 auto">${arcs.join("")}
      <text x="110" y="106" text-anchor="middle" font-size="24" font-weight="700" fill="#1f2937">${int0(total)}</text>
      <text x="110" y="126" text-anchor="middle" font-size="11" fill="#6b7280">campaigns</text></svg><div class="legend">${legend}</div>`;
  }
  function hbar(el, items, colorFn) {
    if (!items.length) return emptyChart(el);
    const W = 480, rowH = 26, top = 6, H = top + items.length * rowH + 6, max = Math.max.apply(null, items.map((i) => i.value)) || 1, barMax = W - 150 - 68;
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}">` + items.map((it, i) => {
      const y = top + i * rowH, w = Math.max(2, it.value / max * barMax), name = it.label.length > 26 ? it.label.slice(0, 25) + "…" : it.label;
      return `<g transform="translate(0,${y})"><text x="8" y="15" font-size="11" fill="#374151">${esc(name)}</text>
        <rect x="150" y="4" width="${w}" height="15" rx="4" fill="${colorFn(it)}"/>
        <text x="${150 + w + 6}" y="15" font-size="11" font-weight="600" fill="#111827">${it.fmt(it.value)}</text></g>`; }).join("") + `</svg>`;
  }
  function scatter(el, rows) {
    const pts = rows.filter((r) => (r.ad_spend || 0) > 0 || (r.total_sales || 0) > 0); if (!pts.length) return emptyChart(el);
    const W = 480, H = 300, m = { l: 54, r: 14, t: 12, b: 40 }, maxX = Math.max.apply(null, pts.map((p) => p.ad_spend || 0)) || 1, maxY = Math.max.apply(null, pts.map((p) => p.total_sales || 0)) || 1;
    const sx = (v) => m.l + v / maxX * (W - m.l - m.r), sy = (v) => H - m.b - v / maxY * (H - m.t - m.b);
    const grid = [0, .25, .5, .75, 1].map((f) => { const y = sy(maxY * f), x = sx(maxX * f);
      return `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#eef1f5"/><text x="${m.l - 6}" y="${y + 3}" text-anchor="end" font-size="9" fill="#9ca3af">${shortMoney(maxY * f)}</text><text x="${x}" y="${H - m.b + 14}" text-anchor="middle" font-size="9" fill="#9ca3af">${shortMoney(maxX * f)}</text>`; }).join("");
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}
      <line x1="${m.l}" y1="${m.t}" x2="${m.l}" y2="${H - m.b}" stroke="#d1d5db"/><line x1="${m.l}" y1="${H - m.b}" x2="${W - m.r}" y2="${H - m.b}" stroke="#d1d5db"/>
      <text x="${W / 2}" y="${H - 4}" text-anchor="middle" font-size="10" fill="#6b7280">Ad Spend (£)</text>
      <text transform="translate(12,${H / 2}) rotate(-90)" text-anchor="middle" font-size="10" fill="#6b7280">Sales (£)</text>
      ${pts.map((p) => `<circle cx="${sx(p.ad_spend || 0).toFixed(1)}" cy="${sy(p.total_sales || 0).toFixed(1)}" r="3.4" fill="${PERF_COLORS[p.performance] || "#94a3b8"}" fill-opacity="0.72"/>`).join("")}</svg>
      <div class="legend"><span class="li"><span class="dot" style="background:#16a34a"></span>High</span><span class="li"><span class="dot" style="background:#f59e0b"></span>Medium</span><span class="li"><span class="dot" style="background:#dc2626"></span>Low</span></div>`;
  }
  function trend(el, rows) {
    const lo = lowerIdx(RANGE.from), hi = upperIdx(RANGE.to);
    if (lo > hi) return emptyChart(el);
    const bucket = {};
    for (const r of rows) for (let k = 0; k < r._entries.length; k++) { const e = r._entries[k]; if (e[0] < lo) continue; if (e[0] > hi) break;
      const mo = DATES[e[0]].slice(0, 7); (bucket[mo] || (bucket[mo] = [0, 0]))[0] += e[3]; bucket[mo][1] += e[4]; }
    const months = Object.keys(bucket).sort(); if (!months.length) return emptyChart(el);
    const spV = months.map((m) => bucket[m][0]), saV = months.map((m) => bucket[m][1]), max = Math.max(1, Math.max.apply(null, spV.concat(saV)));
    const W = 480, H = 280, m = { l: 52, r: 14, t: 12, b: 46 };
    const sx = (i) => m.l + (months.length === 1 ? (W - m.l - m.r) / 2 : i / (months.length - 1) * (W - m.l - m.r)), sy = (v) => H - m.b - v / max * (H - m.t - m.b);
    const grid = [0, .25, .5, .75, 1].map((f) => { const y = sy(max * f); return `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#eef1f5"/><text x="${m.l - 6}" y="${y + 3}" text-anchor="end" font-size="9" fill="#9ca3af">${shortMoney(max * f)}</text>`; }).join("");
    const path = (vals) => vals.map((v, i) => (i ? "L" : "M") + sx(i).toFixed(1) + " " + sy(v).toFixed(1)).join(" ");
    const xl = months.map((mo, i) => (months.length <= 12 || i % 2 === 0) ? `<text x="${sx(i)}" y="${H - m.b + 16}" text-anchor="middle" font-size="8.5" fill="#9ca3af" transform="rotate(35 ${sx(i)} ${H - m.b + 16})">${mo}</text>` : "").join("");
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}">${grid}<path d="${path(spV)}" fill="none" stroke="#dc2626" stroke-width="2"/><path d="${path(saV)}" fill="none" stroke="#16a34a" stroke-width="2"/>${xl}</svg>
      <div class="legend"><span class="li"><span class="dot" style="background:#dc2626"></span>Ad Spend</span><span class="li"><span class="dot" style="background:#16a34a"></span>Attributed Sales</span></div>`;
  }
  function renderCharts(rows) {
    scatter($("#chart-scatter"), rows);
    donut($("#chart-perf"), ["High", "Medium", "Low"].map((p) => ({ key: p, value: rows.filter((r) => r.performance === p).length })), (e) => PERF_COLORS[e.key], (e) => e.key);
    const order = ["running", "paused", "ended", "deleted"], extra = Array.from(new Set(rows.map((r) => r.campaign_status))).filter((s) => order.indexOf(s) === -1);
    donut($("#chart-status"), order.concat(extra).map((s) => ({ key: s, value: rows.filter((r) => r.campaign_status === s).length })).filter((e) => e.value), (e) => STATUS_COLORS[e.key] || "#94a3b8", (e) => STATUS_LABEL[e.key] || e.key);
    hbar($("#chart-top-sales"), rows.filter((r) => r.total_sales > 0).sort((a, b) => b.total_sales - a.total_sales).slice(0, 10).map((r) => ({ label: r.campaign_name, value: r.total_sales, fmt: money })), () => "#16a34a");
    hbar($("#chart-top-spend"), rows.filter((r) => r.ad_spend > 0).sort((a, b) => b.ad_spend - a.ad_spend).slice(0, 10).map((r) => ({ label: r.campaign_name, value: r.ad_spend, fmt: money })), () => "#2563eb");
    trend($("#chart-trend"), rows);
  }

  // -------------------------------------------------- table
  function buildHead() {
    const visible = KEYS.filter((k) => !HIDDEN.has(k));
    let ths = `<th class="sticky-col col-check"><input type="checkbox" id="chk-all" title="Select page"/></th>`;
    visible.forEach((k, idx) => { const right = NUMERIC.has(k) ? " num" : "", sticky = idx === 0 ? " sticky-col col-first" : "",
      arrow = SORT.key === k ? `<span class="arrow">${SORT.dir === "asc" ? "▲" : "▼"}</span>` : "";
      ths += `<th class="sortable${right}${sticky}" data-key="${k}"><span class="th-in">${esc(LABEL[k])}${arrow}</span><span class="th-resize" data-key="${k}"></span></th>`; });
    $("#tbl-head").innerHTML = "<tr>" + ths + "</tr>";
    $("#chk-all").addEventListener("change", onSelectAll);
    $$("#tbl-head th.sortable").forEach((th) => th.addEventListener("click", (e) => { if (e.target.classList.contains("th-resize")) return;
      const k = th.dataset.key; if (SORT.key === k) SORT.dir = SORT.dir === "asc" ? "desc" : "asc"; else { SORT.key = k; SORT.dir = NUMERIC.has(k) ? "desc" : "asc"; } render(); }));
    initResize();
  }
  const statusBadge = (s) => `<span class="badge ${{ running: "active", paused: "paused", ended: "ended", deleted: "deleted" }[s] || "ended"}">${esc(STATUS_LABEL[s] || s)}</span>`;
  const perfBadge = (p) => `<span class="badge ${p === "High" ? "high" : p === "Medium" ? "medium" : "low"}">${esc(p)}</span>`;

  let VIEW = [];
  function renderBody() {
    const visible = KEYS.filter((k) => !HIDDEN.has(k)), start = (PAGE - 1) * PAGE_SIZE, pageRows = VIEW.slice(start, start + PAGE_SIZE), body = $("#tbl-body");
    if (!VIEW.length) { body.innerHTML = ""; return; }
    body.innerHTML = pageRows.map((r) => {
      let tds = `<td class="sticky-col col-check"><input type="checkbox" class="row-chk" data-id="${r._id}" ${SELECTED.has(r._id) ? "checked" : ""}/></td>`;
      visible.forEach((k, idx) => { const t = TYPE[k], right = NUMERIC.has(k) ? " num" : "", sticky = idx === 0 ? " sticky-col col-first" : "";
        let cell = t === "status" ? statusBadge(r[k]) : t === "perf" ? perfBadge(r[k]) : esc(fmtByType(t, r[k]));
        const cls = (t === "text" && (r[k] === "N/A" || r[k] == null)) ? " muted" : "";
        tds += `<td class="copyable${right}${sticky}${cls}" data-raw="${esc(r[k] == null ? "" : r[k])}">${cell}</td>`; });
      return `<tr class="${SELECTED.has(r._id) ? "selected" : ""}" data-id="${r._id}">${tds}</tr>`;
    }).join("");
    $$(".row-chk", body).forEach((c) => c.addEventListener("change", (e) => { const id = +e.target.dataset.id;
      if (e.target.checked) SELECTED.add(id); else SELECTED.delete(id); e.target.closest("tr").classList.toggle("selected", e.target.checked); updateSelCount(); }));
    $$("td.copyable", body).forEach((td) => td.addEventListener("click", () => copyText(td.dataset.raw || td.textContent)));
    const ca = $("#chk-all"); if (ca) ca.checked = pageRows.length > 0 && pageRows.every((r) => SELECTED.has(r._id));
  }
  function onSelectAll(e) { const start = (PAGE - 1) * PAGE_SIZE; VIEW.slice(start, start + PAGE_SIZE).forEach((r) => { if (e.target.checked) SELECTED.add(r._id); else SELECTED.delete(r._id); }); renderBody(); updateSelCount(); }
  function updateSelCount() { $("#sel-count").textContent = SELECTED.size ? `${SELECTED.size} selected` : ""; }

  function renderPagination() {
    const total = VIEW.length, pages = Math.max(1, Math.ceil(total / PAGE_SIZE)); if (PAGE > pages) PAGE = pages;
    const start = total ? (PAGE - 1) * PAGE_SIZE + 1 : 0, end = Math.min(total, PAGE * PAGE_SIZE);
    $("#page-info").textContent = `Showing ${int0(start)}–${int0(end)} of ${int0(total)} campaigns`;
    const btn = (l, p, dis, act) => `<button class="page-btn ${act ? "active" : ""}" ${dis ? "disabled" : ""} data-page="${p}">${l}</button>`;
    let html = btn("«", 1, PAGE === 1) + btn("‹", PAGE - 1, PAGE === 1); const win = 2, from = Math.max(1, PAGE - win), to = Math.min(pages, PAGE + win);
    if (from > 1) html += `<span class="page-info">…</span>`; for (let p = from; p <= to; p++) html += btn(p, p, false, p === PAGE);
    if (to < pages) html += `<span class="page-info">…</span>`; html += btn("›", PAGE + 1, PAGE === pages) + btn("»", pages, PAGE === pages);
    $("#page-controls").innerHTML = html;
    $$("#page-controls .page-btn").forEach((b) => b.addEventListener("click", () => { PAGE = +b.dataset.page; renderBody(); renderPagination(); }));
  }
  function initResize() {
    $$("#tbl-head .th-resize").forEach((grip) => grip.addEventListener("mousedown", (e) => { e.preventDefault(); e.stopPropagation();
      const th = grip.parentElement, sx = e.pageX, sw = th.offsetWidth;
      const mv = (ev) => { th.style.width = Math.max(60, sw + ev.pageX - sx) + "px"; th.style.minWidth = th.style.width; };
      const up = () => { document.removeEventListener("mousemove", mv); document.removeEventListener("mouseup", up); };
      document.addEventListener("mousemove", mv); document.addEventListener("mouseup", up); }));
  }
  function buildColsMenu() {
    const menu = $("#cols-menu");
    menu.innerHTML = COLS.map((c) => `<label><input type="checkbox" data-key="${c.key}" ${HIDDEN.has(c.key) ? "" : "checked"} ${c.key === "month" ? "disabled" : ""}/> ${esc(c.label)}</label>`).join("");
    $$("#cols-menu input").forEach((cb) => cb.addEventListener("change", (e) => { const k = e.target.dataset.key; if (e.target.checked) HIDDEN.delete(k); else HIDDEN.add(k); buildHead(); renderBody(); }));
    $("#btn-cols").addEventListener("click", (e) => { e.stopPropagation(); menu.classList.toggle("open"); });
    document.addEventListener("click", () => menu.classList.remove("open")); menu.addEventListener("click", (e) => e.stopPropagation());
  }

  // -------------------------------------------------- CSV export (respects reporting period + filters + sort)
  function toCSV(rows, keys) {
    const lines = [keys.map((k) => LABEL[k]).join(",")];
    for (const r of rows) lines.push(keys.map((k) => { let v = r[k]; if (v == null) v = ""; v = String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(","));
    return lines.join("\r\n");
  }
  function download(name, text) { const b = new Blob([text], { type: "text/csv;charset=utf-8;" }), a = document.createElement("a");
    a.href = URL.createObjectURL(b); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1500); }
  function periodTag() { return `${RANGE.from}_to_${RANGE.to}`; }
  function exportAll() { download(`ebay_ppc_${periodTag()}_filtered.csv`, toCSV(VIEW, KEYS)); toast(`Exported ${VIEW.length} rows (${RANGE.from} → ${RANGE.to})`); }
  function exportView() { const start = (PAGE - 1) * PAGE_SIZE, pr = VIEW.slice(start, start + PAGE_SIZE);
    download(`ebay_ppc_${periodTag()}_page${PAGE}.csv`, toCSV(pr, KEYS.filter((k) => !HIDDEN.has(k)))); toast(`Exported current view — ${pr.length} rows`); }

  function copyText(t) { const done = () => toast("Copied: " + (String(t).length > 40 ? String(t).slice(0, 39) + "…" : t));
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(String(t)).then(done, fb); else fb();
    function fb() { const ta = document.createElement("textarea"); ta.value = String(t); document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) {} document.body.removeChild(ta); } }
  let toastTimer; function toast(msg) { const el = $("#toast"); el.textContent = msg; el.classList.add("show"); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 1900); }

  // -------------------------------------------------- reconciliation (full-window integrity, independent of view)
  function reconcile() {
    let sp = 0, sa = 0, orr = 0, clk = 0, impr = 0, active = 0, paused = 0;
    for (let j = 0; j < DIM.length; j++) { const d = DIM[j]; if (d[DI.campaign_status] === "running") active++; if (d[DI.campaign_status] === "paused") paused++;
      for (const e of DAILY[j]) { impr += e[1]; clk += e[2]; sp += e[3]; sa += e[4]; orr += e[5]; } }
    const t = { campaigns: DIM.length, active, paused, spend: r2(sp), sales: r2(sa), orders: orr, clicks: clk, impressions: impr };
    const s = DATA.sql_totals, el = $("#recon"), eq = (a, b) => Math.abs((a || 0) - (b || 0)) < 0.02;
    const checks = [["Campaigns", t.campaigns, s.campaigns], ["Active", t.active, s.active], ["Paused", t.paused, s.paused],
      ["Spend", t.spend, s.spend], ["Sales", t.sales, s.sales], ["Orders", t.orders, s.orders], ["Clicks", t.clicks, s.clicks], ["Impressions", t.impressions, s.impressions]];
    const ok = checks.every((c) => eq(c[1], c[2]));
    el.className = "recon " + (ok ? "ok" : "bad");
    el.innerHTML = ok
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>
         <span><b>Data validation passed.</b> Full-history daily facts reconcile exactly with the SQL dataset —
         ${int0(s.campaigns)} campaigns · Spend ${money(s.spend)} · Sales ${money(s.sales)} · Orders ${int0(s.orders)} · Clicks ${int0(s.clicks)} · Impressions ${int0(s.impressions)}.
         Reporting date field: <b>${esc(DATA.meta.reporting_date_field)}</b>.</span>`
      : `<span><b>Reconciliation mismatch:</b> ${checks.filter((c) => !eq(c[1], c[2])).map((c) => `${c[0]} (calc ${c[1]} vs SQL ${c[2]})`).join("; ")}</span>`;
  }

  // -------------------------------------------------- reporting-period UI
  function syncRangeUI() {
    $("#f-date-from").value = RANGE.from; $("#f-date-to").value = RANGE.to;
    $$(".preset-btn").forEach((b) => b.classList.toggle("active", b.dataset.preset === RANGE.preset));
    const lbl = `${RANGE.from} → ${RANGE.to}` + (RANGE.from === RANGE.to ? "" : "");
    if ($("#report-period")) $("#report-period").textContent = lbl;
    if ($("#hdr-month")) $("#hdr-month").textContent = lbl;
  }

  // -------------------------------------------------- main render
  function render() {
    VIEW = getSorted(getFiltered());
    renderKPIs(aggregate(VIEW));
    renderCharts(VIEW);
    buildHead();
    const empty = VIEW.length === 0;
    $("#tbl-empty").classList.toggle("hidden", !empty);
    $("#tbl-scroll").classList.toggle("hidden", empty);
    renderBody(); renderPagination(); updateSelCount(); syncRangeUI();
    $("#tbl-updated").textContent = "Reporting period: " + RANGE.from + " → " + RANGE.to +
      "  ·  updated " + fmtDateTime(new Date().toISOString()) + "  ·  data synced " + fmtDateTime(DATA.meta.generated_at);
  }
  function rebuildAndRender() { buildRows(); PAGE = 1; render(); }

  // -------------------------------------------------- wire
  function wire() {
    fillSelect($("#f-account"), distinct((d) => d[DI.account]), "All Accounts");
    fillSelect($("#f-marketplace"), distinct((d) => d[DI.marketplace]), "All Marketplaces");
    fillSelect($("#f-campaign-type"), distinct((d) => d[DI.campaign_type]), "All Campaign Types");
    fillSelect($("#f-status"), distinct((d) => d[DI.campaign_status]), "All Statuses");
    fillSelect($("#f-performance"), ["High", "Medium", "Low"], "All Performance");

    // preset buttons
    $("#preset-group").innerHTML = PRESETS.map(([k, l]) => `<button class="preset-btn" data-preset="${k}">${l}</button>`).join("");
    $$(".preset-btn").forEach((b) => b.addEventListener("click", () => {
      const name = b.dataset.preset;
      if (name === "custom") { RANGE.preset = "custom"; syncRangeUI(); return; }
      applyPreset(name); rebuildAndRender();
    }));

    // custom date inputs (reporting date)
    const df = $("#f-date-from"), dtt = $("#f-date-to");
    df.min = DMIN; df.max = DMAX; dtt.min = DMIN; dtt.max = DMAX;
    const onDate = () => { if (df.value) RANGE.from = clampFrom(df.value); if (dtt.value) RANGE.to = clampTo(dtt.value);
      if (RANGE.from > RANGE.to) { const t = RANGE.from; RANGE.from = RANGE.to; RANGE.to = t; } RANGE.preset = "custom"; rebuildAndRender(); };
    df.addEventListener("change", onDate); dtt.addEventListener("change", onDate);

    const reRender = () => { PAGE = 1; render(); };
    $("#f-account").addEventListener("change", (e) => { FILTERS.account = e.target.value; reRender(); });
    $("#f-marketplace").addEventListener("change", (e) => { FILTERS.marketplace = e.target.value; reRender(); });
    $("#f-campaign-type").addEventListener("change", (e) => { FILTERS.campaignType = e.target.value; reRender(); });
    $("#f-status").addEventListener("change", (e) => { FILTERS.status = e.target.value; reRender(); });
    $("#f-performance").addEventListener("change", (e) => { FILTERS.performance = e.target.value; reRender(); });
    $("#f-acos-min").addEventListener("input", (e) => { FILTERS.acosMin = e.target.value === "" ? null : +e.target.value; reRender(); });
    $("#f-acos-max").addEventListener("input", (e) => { FILTERS.acosMax = e.target.value === "" ? null : +e.target.value; reRender(); });
    $("#f-roas-min").addEventListener("input", (e) => { FILTERS.roasMin = e.target.value === "" ? null : +e.target.value; reRender(); });
    $("#f-roas-max").addEventListener("input", (e) => { FILTERS.roasMax = e.target.value === "" ? null : +e.target.value; reRender(); });
    let st; const onSearch = (v) => { clearTimeout(st); st = setTimeout(() => { FILTERS.search = v; reRender(); }, 180); };
    $("#f-search").addEventListener("input", (e) => { $("#tbl-search").value = e.target.value; onSearch(e.target.value); });
    $("#tbl-search").addEventListener("input", (e) => { $("#f-search").value = e.target.value; onSearch(e.target.value); });

    $("#btn-reset").addEventListener("click", () => {
      Object.assign(FILTERS, { account: "", marketplace: "", campaignType: "", status: "", performance: "", acosMin: null, acosMax: null, roasMin: null, roasMax: null, search: "" });
      ["f-account","f-marketplace","f-campaign-type","f-status","f-performance"].forEach((id) => ($("#" + id).value = ""));
      ["f-acos-min","f-acos-max","f-roas-min","f-roas-max","f-search","tbl-search"].forEach((id) => ($("#" + id).value = ""));
      SELECTED.clear(); applyPreset(DATA.meta.default_preset || "last30"); rebuildAndRender(); toast("Filters reset");
    });

    $("#page-size").addEventListener("change", (e) => { PAGE_SIZE = +e.target.value; PAGE = 1; renderBody(); renderPagination(); });
    $("#btn-export-all").addEventListener("click", exportAll);
    $("#btn-export-view").addEventListener("click", exportView);
    $("#btn-refresh").addEventListener("click", () => location.reload());
    $("#auto-refresh").addEventListener("change", (e) => {
      if (e.target.checked) { autoTimer = setInterval(() => { render(); toast("Auto-refreshed view"); }, 60000); toast("Auto-refresh on (60s)"); }
      else { clearInterval(autoTimer); autoTimer = null; toast("Auto-refresh off"); } });
    buildColsMenu();
  }

  // -------------------------------------------------- header + footnote
  $("#hdr-sync").textContent = fmtDateTime(DATA.meta.generated_at);
  $("#hdr-count").textContent = int0(DIM.length);
  $("#footnote").innerHTML =
    `Source tables: <b>${DATA.meta.source_tables.join(", ")}</b>. Reporting date field: <b>${esc(DATA.meta.reporting_date_field)}</b>. ` +
    `${esc(DATA.meta.currency_note)} The Date Range filters the reporting period (per-day facts re-aggregated per campaign); ` +
    `“Campaign Start Date” is a display-only column and is never used for filtering. ` +
    `“Today’s Spend” = spend on the latest reporting date (${TODAY}). “Average” KPIs are portfolio (spend-weighted) figures.`;

  function init() { wire(); reconcile(); buildRows(); render(); $("#tbl-skeleton").classList.add("hidden"); }
  (function skeleton() { const sk = $("#tbl-skeleton");
    sk.innerHTML = Array.from({ length: 8 }).map(() => `<div class="skeleton-row">${Array.from({ length: 8 }).map(() => `<div class="skeleton-cell"></div>`).join("")}</div>`).join("");
    setTimeout(init, 220); })();
})();

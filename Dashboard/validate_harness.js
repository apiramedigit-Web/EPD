/* Headless harness: runs the REAL data.js + dashboard.js in a minimal DOM shim,
   drives every Date Range preset, and extracts the actual KPI + chart output so we
   can verify charts are driven by the filtered reporting-date dataset. */
const fs = require("fs");

// ------------------------------------------------------------------ DOM shim
const collections = new Map();
const byId = new Map();
const setColl = (n, arr) => collections.set(n, arr);
const coll = (n) => collections.get(n) || [];

class El {
  constructor(tag, id) { this.tag = tag; this.id = id || null; this._html = ""; this._text = "";
    this._list = {}; this.dataset = {}; this.style = {}; this.value = ""; this.checked = false;
    this.min = ""; this.max = "";
    const s = new Set();
    this.classList = { add:(...c)=>c.forEach(x=>s.add(x)), remove:(...c)=>c.forEach(x=>s.delete(x)),
      contains:(c)=>s.has(c), toggle:(c,f)=> (f===undefined?(s.has(c)?(s.delete(c),false):(s.add(c),true)):(f?(s.add(c),true):(s.delete(c),false))) };
  }
  set innerHTML(v){ this._html = String(v); parseHooks(this); }
  get innerHTML(){ return this._html; }
  set textContent(v){ this._text = String(v); }
  get textContent(){ return this._text; }
  addEventListener(t, fn){ (this._list[t] || (this._list[t] = [])).push(fn); }
  fire(t, ev){ (this._list[t]||[]).forEach(fn=>fn(ev||{target:this})); }
  closest(){ return new El("tr"); }
  querySelector(s){ return qs(s); }
  querySelectorAll(s){ return qsa(s); }
  appendChild(){} removeChild(){} click(){} select(){} remove(){}
  get offsetWidth(){ return 100; }
}

function parseHooks(el){
  const h = el._html;
  if (el.id === "preset-group") {
    const arr=[]; const re=/data-preset="([^"]+)"/g; let m;
    while((m=re.exec(h))){ const b=new El("button"); b.dataset.preset=m[1]; b.classList.add("preset-btn"); arr.push(b); }
    setColl("preset-btn", arr);
  } else if (el.id === "tbl-head") {
    const sort=[]; let m; const r1=/<th class="(sortable[^"]*)" data-key="([^"]+)">/g;
    while((m=r1.exec(h))){ const t=new El("th"); m[1].split(" ").forEach(c=>c&&t.classList.add(c)); t.dataset.key=m[2]; sort.push(t); }
    setColl("th-sortable", sort);
    const res=[]; const r2=/<span class="th-resize" data-key="([^"]+)">/g;
    while((m=r2.exec(h))){ const t=new El("span"); t.classList.add("th-resize"); t.dataset.key=m[1]; res.push(t); }
    setColl("th-resize", res);
  } else if (el.id === "cols-menu") {
    const arr=[]; const re=/<input type="checkbox" data-key="([^"]+)"([^>]*)\/>/g; let m;
    while((m=re.exec(h))){ const i=new El("input"); i.dataset.key=m[1]; i.checked=/checked/.test(m[2]); arr.push(i); }
    setColl("cols-input", arr);
  } else if (el.id === "page-controls") {
    const arr=[]; const re=/<button class="page-btn[^"]*"([^>]*?)data-page="([^"]+)"[^>]*>/g; let m;
    while((m=re.exec(h))){ const b=new El("button"); b.dataset.page=m[2]; b.disabled=/disabled/.test(m[1]); arr.push(b); }
    setColl("page-btn", arr);
  } else if (el.id === "tbl-body") {
    const rc=[]; const re=/class="row-chk" data-id="([^"]+)"/g; let m;
    while((m=re.exec(h))){ const i=new El("input"); i.classList.add("row-chk"); i.dataset.id=m[1]; rc.push(i); }
    setColl("row-chk", rc);
    const cp=[]; const r2=/<td class="copyable[^"]*"[^>]*data-raw="([^"]*)"/g;
    while((m=r2.exec(h))){ const t=new El("td"); t.classList.add("copyable"); t.dataset.raw=m[1]; cp.push(t); }
    setColl("td-copyable", cp);
  }
}

function getId(id){ if(!byId.has(id)) byId.set(id, new El("div", id)); return byId.get(id); }
function qs(sel, root){
  sel = sel.trim();
  if (sel[0] === "#" && !/[ .>]/.test(sel.slice(1))) return getId(sel.slice(1));
  const a = qsa(sel, root); return a.length ? a[0] : null;
}
function qsa(sel){
  sel = sel.trim();
  const map = { ".preset-btn":"preset-btn", "#tbl-head th.sortable":"th-sortable",
    "#tbl-head .th-resize":"th-resize", "#cols-menu input":"cols-input",
    "#page-controls .page-btn":"page-btn", ".row-chk":"row-chk", "td.copyable":"td-copyable" };
  return map[sel] ? coll(map[sel]) : [];
}

const document = {
  querySelector: (s, r)=>qs(s, r), querySelectorAll: (s, r)=>qsa(s, r),
  createElement: (t)=>new El(t), addEventListener: ()=>{},
  body: Object.assign(new El("body"), { appendChild(){}, removeChild(){} }),
};
const window = {};
global.window = window; global.document = document;
global.navigator = { clipboard: { writeText: ()=>Promise.resolve() } };
global.setTimeout = (fn)=>{ fn(); return 0; };
global.setInterval = ()=>0; global.clearTimeout=()=>{}; global.clearInterval=()=>{};
global.__lastBlob = null;
global.Blob = class { constructor(parts){ this.parts = parts; global.__lastBlob = this; } };
global.URL = { createObjectURL: ()=>"blob:x", revokeObjectURL: ()=>{} };

// ------------------------------------------------------------------ load real code
const HERE = __dirname;
const dataJs = fs.readFileSync(HERE + "/data.js", "utf8");
const logicJs = fs.readFileSync(HERE + "/dashboard.js", "utf8");
// eval data.js (assigns window.DASHBOARD_DATA) then dashboard.js (runs, inits synchronously)
eval(dataJs);
eval(logicJs);

// ------------------------------------------------------------------ extractors
const money = (s)=> s==null?null : Number(String(s).replace(/[£,]/g,"")) ;
function parseKPI(){
  const h = getId("kpi-grid").innerHTML, out = {};
  const re = /<span class="label">([^<]+)<\/span>.*?<div class="value[^"]*">([^<]+)<\/div>/gs; let m;
  while((m=re.exec(h))) out[m[1].trim()] = m[2].trim();
  return out;
}
function donutCounts(id){
  const h = getId(id).innerHTML, out = {}; const re = /<\/span>([^<]+?) — <b>([\d,]+)<\/b>/g; let m;
  while((m=re.exec(h))) out[m[1].trim()] = Number(m[2].replace(/,/g,""));
  return out;
}
function barValues(id){
  const h = getId(id).innerHTML, out = []; const re = /font-weight="600"[^>]*>£([\d,\.]+)<\/text>/g; let m;
  while((m=re.exec(h))) out.push(Number(m[1].replace(/,/g,"")));
  return out;
}
function scatterPoints(id){ return (getId(id).innerHTML.match(/<circle /g)||[]).length; }
function trendMonths(id){ const s=new Set(); const re=/>(\d{4}-\d{2})<\/text>/g; let m; const h=getId(id).innerHTML; while((m=re.exec(h))) s.add(m[1]); return [...s].sort(); }
function chartHash(id){ const h=getId(id).innerHTML; let x=0; for(let i=0;i<h.length;i++){x=(x*31+h.charCodeAt(i))>>>0;} return h.length+":"+x; }
function tableInfo(){
  const rows=(getId("tbl-body").innerHTML.match(/<tr /g)||[]).length;
  return { pageRows: rows, pageInfo: getId("page-info").textContent };
}
function snapshot(){
  const k = parseKPI();
  return {
    window: [getId("f-date-from").value, getId("f-date-to").value],
    reportPeriod: getId("report-period").textContent,
    kpi: {
      campaigns: money(k["Total Campaigns"]), active: money(k["Active Campaigns"]), paused: money(k["Paused Campaigns"]),
      spend: money(k["Total Ad Spend (£)"]), sales: money(k["Attributed Sales (£)"]), orders: money(k["Orders"]),
      clicks: money(k["Total Clicks"]), impressions: money(k["Total Impressions"]),
      acos: k["Average ACOS (%)"], roas: k["Average ROAS"], cpc: k["Average CPC (£)"],
      ctr: k["Average CTR (%)"], cvr: k["Average Conversion Rate (%)"], aov: k["Average Order Value (£)"],
      todaySpend: k["Today's Spend (£)"],
    },
    charts: {
      scatterPoints: scatterPoints("chart-scatter"),
      perf: donutCounts("chart-perf"),
      status: donutCounts("chart-status"),
      topSales: barValues("chart-top-sales"),
      topSpend: barValues("chart-top-spend"),
      trendMonths: trendMonths("chart-trend"),
      hash: { scatter: chartHash("chart-scatter"), perf: chartHash("chart-perf"), status: chartHash("chart-status"),
              topSales: chartHash("chart-top-sales"), topSpend: chartHash("chart-top-spend"), trend: chartHash("chart-trend") },
    },
    table: tableInfo(),
  };
}
function firePreset(name){ const b = coll("preset-btn").find(x=>x.dataset.preset===name); if(!b) throw new Error("no preset "+name); b.fire("click"); }
function setCustom(from,to){ const df=getId("f-date-from"), dt=getId("f-date-to"); df.value=from; df.fire("change"); dt.value=to; dt.fire("change"); }

const META = window.DASHBOARD_DATA.meta;
const OUT = { meta: { today: META.today_date, date_min: META.date_min, date_max: META.date_max,
                      reporting_date_field: META.reporting_date_field, default_preset: META.default_preset },
              sql_totals: window.DASHBOARD_DATA.sql_totals, presets: {}, table_tests: {}, stale: {} };

// initial (default preset)
OUT.presets["_default_" + META.default_preset] = snapshot();
for (const p of ["today","yesterday","last7","last30","thismonth","lastmonth"]) { firePreset(p); OUT.presets[p] = snapshot(); }
// Custom range (arbitrary reporting period) and FULL history via custom inputs
setCustom("2025-03-01","2025-03-31"); OUT.presets["custom_2025-03"] = snapshot();
setCustom(META.date_min, META.date_max); OUT.presets["custom_FULL"] = snapshot();

// ---- stale-data check: Full vs Last 7 Days per chart (hashes must differ) ----
firePreset("last7"); const s7 = snapshot();
setCustom(META.date_min, META.date_max); const sFull = snapshot();
OUT.stale = {};
for (const c of ["scatter","perf","status","topSales","topSpend","trend"])
  OUT.stale[c] = { last7: s7.charts.hash[c], full: sFull.charts.hash[c], differ: s7.charts.hash[c] !== sFull.charts.hash[c] };

// ---- table feature tests (on FULL view) ----
// search
const ts = getId("tbl-search"); ts.value = "transformer"; ts.fire("input"); const searched = tableInfo();
ts.value = ""; ts.fire("input");
// pagination -> page 2
getId("page-size"); // default 25
const p2 = coll("page-btn").find(x=>x.dataset.page==="2"); if(p2) p2.fire("click");
const pageTwo = tableInfo();
// reset to page 1
const p1 = coll("page-btn").find(x=>x.dataset.page==="1"); if(p1) p1.fire("click");
// sorting -> click Campaign Name header (asc)
const th = coll("th-sortable").find(x=>x.dataset.key==="campaign_name"); if(th) th.fire("click");
function firstColRaws(colIndex, n){
  const body = getId("tbl-body").innerHTML; const rows = body.split("<tr ").slice(1); const out=[];
  for (const r of rows.slice(0,n)) { const raws=[]; const re=/data-raw="([^"]*)"/g; let m; while((m=re.exec(r))) raws.push(m[1]); out.push(raws[colIndex]); }
  return out;
}
const sortedNames = firstColRaws(3, 8); // campaign_name is KEYS index 3
// column visibility: hide SKU
const skuInput = coll("cols-input").find(x=>x.dataset.key==="sku"); let skuHidden=null;
if (skuInput) { skuInput.checked=false; skuInput.fire("change"); skuHidden = getId("tbl-head").innerHTML.indexOf(">SKU<")===-1; skuInput.checked=true; skuInput.fire("change"); }
// export CSV (respects current view = FULL + filters + sort)
getId("btn-export-all").fire("click");
const csvText = global.__lastBlob ? global.__lastBlob.parts.join("") : "";   // raw CSV; Python parses it correctly
OUT.table_tests = {
  search: { term:"transformer", pageRows: searched.pageRows, pageInfo: searched.pageInfo },
  pagination: { page2: pageTwo.pageInfo },
  sorting: { firstNamesAsc: sortedNames, isAscending: sortedNames.every((v,i,a)=> i===0 || (v||"").toLowerCase() >= (a[i-1]||"").toLowerCase()) },
  colVisibility: { skuHiddenThenRestored: skuHidden },
  export: { csvText: csvText },
};

process.stdout.write(JSON.stringify(OUT));

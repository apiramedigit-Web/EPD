/* Runs the REAL data.js + dashboard.js in a DOM shim and applies the two custom
   reporting-date ranges, capturing real KPI + chart output + exported CSV + the
   export filename + Start Date values, for reconciliation against production SQL. */
const fs = require("fs");
const collections = new Map(); const byId = new Map();
const setColl=(n,a)=>collections.set(n,a); const coll=(n)=>collections.get(n)||[];
class El {
  constructor(t,id){ this.tag=t; this.id=id||null; this._html=""; this._text=""; this._list={}; this.dataset={}; this.style={}; this.value=""; this.checked=false; this.min=""; this.max=""; this.download="";
    const s=new Set(); this.classList={add:(...c)=>c.forEach(x=>s.add(x)),remove:(...c)=>c.forEach(x=>s.delete(x)),contains:(c)=>s.has(c),toggle:(c,f)=>(f===undefined?(s.has(c)?(s.delete(c),false):(s.add(c),true)):(f?(s.add(c),true):(s.delete(c),false)))}; }
  set innerHTML(v){ this._html=String(v); parseHooks(this); } get innerHTML(){ return this._html; }
  set textContent(v){ this._text=String(v); } get textContent(){ return this._text; }
  addEventListener(t,fn){ (this._list[t]||(this._list[t]=[])).push(fn); }
  fire(t,ev){ (this._list[t]||[]).forEach(fn=>fn(ev||{target:this})); }
  closest(){ return new El("tr"); } querySelector(s){ return qs(s); } querySelectorAll(s){ return qsa(s); }
  appendChild(){} removeChild(){} click(){} select(){} remove(){} get offsetWidth(){ return 100; }
}
function parseHooks(el){ const h=el._html; let m;
  if(el.id==="preset-group"){ const a=[]; const re=/data-preset="([^"]+)"/g; while((m=re.exec(h))){ const b=new El("button"); b.dataset.preset=m[1]; b.classList.add("preset-btn"); a.push(b);} setColl("preset-btn",a); }
  else if(el.id==="tbl-head"){ const s=[]; const r1=/<th class="(sortable[^"]*)" data-key="([^"]+)">/g; while((m=r1.exec(h))){ const t=new El("th"); m[1].split(" ").forEach(c=>c&&t.classList.add(c)); t.dataset.key=m[2]; s.push(t);} setColl("th-sortable",s);
    const rs=[]; const r2=/<span class="th-resize" data-key="([^"]+)">/g; while((m=r2.exec(h))){ const t=new El("span"); t.classList.add("th-resize"); t.dataset.key=m[1]; rs.push(t);} setColl("th-resize",rs); }
  else if(el.id==="cols-menu"){ const a=[]; const re=/<input type="checkbox" data-key="([^"]+)"([^>]*)\/>/g; while((m=re.exec(h))){ const i=new El("input"); i.dataset.key=m[1]; i.checked=/checked/.test(m[2]); a.push(i);} setColl("cols-input",a); }
  else if(el.id==="page-controls"){ const a=[]; const re=/<button class="page-btn[^"]*"([^>]*?)data-page="([^"]+)"[^>]*>/g; while((m=re.exec(h))){ const b=new El("button"); b.dataset.page=m[2]; a.push(b);} setColl("page-btn",a); }
  else if(el.id==="tbl-body"){ const rc=[]; const re=/class="row-chk" data-id="([^"]+)"/g; while((m=re.exec(h))){ const i=new El("input"); i.classList.add("row-chk"); i.dataset.id=m[1]; rc.push(i);} setColl("row-chk",rc);
    const cp=[]; const r2=/<td class="copyable[^"]*"[^>]*data-raw="([^"]*)"/g; while((m=r2.exec(h))){ const t=new El("td"); t.classList.add("copyable"); t.dataset.raw=m[1]; cp.push(t);} setColl("td-copyable",cp); } }
function getId(id){ if(!byId.has(id)) byId.set(id,new El("div",id)); return byId.get(id); }
function qs(s,r){ s=s.trim(); if(s[0]==="#"&&!/[ .>]/.test(s.slice(1))) return getId(s.slice(1)); const a=qsa(s,r); return a.length?a[0]:null; }
function qsa(s){ s=s.trim(); const map={".preset-btn":"preset-btn","#tbl-head th.sortable":"th-sortable","#tbl-head .th-resize":"th-resize","#cols-menu input":"cols-input","#page-controls .page-btn":"page-btn",".row-chk":"row-chk","td.copyable":"td-copyable"}; return map[s]?coll(map[s]):[]; }
global.__anchors=[];
const document={ querySelector:(s,r)=>qs(s,r), querySelectorAll:(s,r)=>qsa(s,r), addEventListener:()=>{},
  createElement:(t)=>{ const e=new El(t); if(t==="a") global.__anchors.push(e); return e; },
  body:Object.assign(new El("body"),{appendChild(){},removeChild(){}}) };
global.window={}; global.document=document; global.navigator={clipboard:{writeText:()=>Promise.resolve()}};
global.setTimeout=(fn)=>{fn();return 0;}; global.setInterval=()=>0; global.clearTimeout=()=>{}; global.clearInterval=()=>{};
global.__lastBlob=null; global.Blob=class{constructor(p){this.parts=p; global.__lastBlob=this;}}; global.URL={createObjectURL:()=>"blob:x",revokeObjectURL:()=>{}};

const HERE=__dirname;
eval(fs.readFileSync(HERE+"/data.js","utf8"));
eval(fs.readFileSync(HERE+"/dashboard.js","utf8"));

const money=(s)=> s==null?null:Number(String(s).replace(/[£,]/g,""));
function parseKPI(){ const h=getId("kpi-grid").innerHTML,o={}; const re=/<span class="label">([^<]+)<\/span>.*?<div class="value[^"]*">([^<]+)<\/div>/gs; let m; while((m=re.exec(h))) o[m[1].trim()]=m[2].trim(); return o; }
function donut(id){ const h=getId(id).innerHTML,o={}; const re=/<\/span>([^<]+?) — <b>([\d,]+)<\/b>/g; let m; while((m=re.exec(h))) o[m[1].trim()]=Number(m[2].replace(/,/g,"")); return o; }
function bars(id){ const h=getId(id).innerHTML,o=[]; const re=/font-weight="600"[^>]*>£([\d,\.]+)<\/text>/g; let m; while((m=re.exec(h))) o.push(Number(m[1].replace(/,/g,""))); return o; }
function pts(id){ return (getId(id).innerHTML.match(/<circle /g)||[]).length; }
function months(id){ const s=new Set(); const re=/>(\d{4}-\d{2})<\/text>/g; let m; const h=getId(id).innerHTML; while((m=re.exec(h))) s.add(m[1]); return [...s].sort(); }
function hash(id){ const h=getId(id).innerHTML; let x=0; for(let i=0;i<h.length;i++) x=(x*31+h.charCodeAt(i))>>>0; return h.length+":"+x; }
function setCustom(from,to){ const df=getId("f-date-from"),dt=getId("f-date-to"); df.value=from; df.fire("change"); dt.value=to; dt.fire("change"); }
function snap(){ const k=parseKPI(); return {
  window:[getId("f-date-from").value,getId("f-date-to").value], reportPeriod:getId("report-period").textContent,
  kpi:{campaigns:money(k["Total Campaigns"]),active:money(k["Active Campaigns"]),paused:money(k["Paused Campaigns"]),
    spend:money(k["Total Ad Spend (£)"]),sales:money(k["Attributed Sales (£)"]),orders:money(k["Orders"]),
    clicks:money(k["Total Clicks"]),impressions:money(k["Total Impressions"]),
    acos:k["Average ACOS (%)"],roas:k["Average ROAS"],cpc:k["Average CPC (£)"],ctr:k["Average CTR (%)"],cvr:k["Average Conversion Rate (%)"],aov:k["Average Order Value (£)"]},
  charts:{scatterPts:pts("chart-scatter"),perf:donut("chart-perf"),status:donut("chart-status"),
    topSales:bars("chart-top-sales"),topSpend:bars("chart-top-spend"),trendMonths:months("chart-trend"),
    hash:{scatter:hash("chart-scatter"),perf:hash("chart-perf"),status:hash("chart-status"),topSales:hash("chart-top-sales"),topSpend:hash("chart-top-spend"),trend:hash("chart-trend")}},
  table:{pageInfo:getId("page-info").textContent} }; }
function measure(from,to){ setCustom(from,to); global.__lastBlob=null; global.__anchors=[]; getId("btn-export-all").fire("click");
  const csv=global.__lastBlob?global.__lastBlob.parts.join(""):""; const name=global.__anchors.length?global.__anchors[global.__anchors.length-1].download:"";
  const s=snap(); s.csvText=csv; s.downloadName=name; return s; }

const META=window.DASHBOARD_DATA.meta;
const OUT={ meta:{reporting_date_field:META.reporting_date_field, today:META.today_date, default_preset:META.default_preset},
  baseline:snap(),                         // default view (last30) BEFORE custom ranges
  range1:measure("2025-10-17","2026-06-30"),
  range2:measure("2026-06-01","2026-06-30") };
process.stdout.write(JSON.stringify(OUT));

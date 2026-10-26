"""Visual layer for the Engine Health Monitor.

Style: achromatic ledger (light). The chrome is ink on a blue-grey ground; the one hue,
#1d5fbf, marks the prediction. Status colours appear only on status.
Signature element: a 3D cutaway of the turbofan, each station tinted by how far its own
sensors have drifted from a healthy engine.
"""
import base64
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_HERE, 'static')

INK, MUTED, HUE = '#0a0a0a', '#5f6368', '#1d5fbf'
GROUND, SURFACE, BORDER, RULE, RAISED = '#f2f4f7', '#ffffff', '#e3e6ea', '#eef0f3', '#eceef1'
NEGATIVE = '#c4242a'
STATUS = {'Critical': '#c4242a', 'Plan maintenance': '#b45309', 'Healthy': '#2e7d32'}
PILL = {'Critical': ('#ffedea', '#831c1e'), 'Plan maintenance': ('#fffbeb', '#92400e'),
        'Healthy': ('#dcfae5', '#04250e')}


def _read(rel, mode='rb'):
    try:
        with open(os.path.join(_STATIC, rel), mode) as f:
            return f.read()
    except OSError:
        return b'' if 'b' in mode else ''


def _faces():
    out = []
    for w in (400, 500, 600):
        data = _read(f'fonts/geist-sans-latin-{w}-normal.woff2')
        if data:
            out.append("@font-face{font-family:'Geist';font-style:normal;font-weight:%d;font-display:swap;"
                       "src:url(data:font/woff2;base64,%s) format('woff2');}" % (w, base64.b64encode(data).decode()))
    return ''.join(out)


FONT_FACES = _faces()
THREE_JS = _read('vendor/three.min.js', 'r')
FONT_STACK = "'Geist', 'Segoe UI', system-ui, sans-serif"

CSS = """
<style>
__FACES__
:root { --ink:#0a0a0a; --muted:#5f6368; --hue:#1d5fbf; --ground:#f2f4f7; --surface:#fff;
        --border:#e3e6ea; --rule:#eef0f3; --raised:#eceef1; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  font-family: __STACK__; color: var(--ink); font-variant-numeric: tabular-nums; }
[data-testid="stAppViewContainer"] :is(p, li, label, input, textarea, td, th, button, div[data-baseweb], span) {
  font-family: __STACK__; }
[data-testid="stAppViewContainer"] *:not([data-testid="stIconMaterial"]):not([class*="material"]) { font-family: __STACK__; }
span[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: var(--ground); }
.block-container { padding: 3.6rem 2rem 4rem; max-width: 1320px; }

h1, h2, h3, [data-testid="stHeading"] * { font-family: __STACK__ !important; color: var(--ink); letter-spacing: 0; }
h1 { font-size: 24px !important; font-weight: 600 !important; line-height: 32px !important; padding: 0 !important; }
h2 { font-size: 20px !important; font-weight: 600 !important; padding: 0 !important; }
h3 { font-size: 16px !important; font-weight: 600 !important; padding: 0 0 4px !important; }
p, li { font-size: 14px; }
[data-testid="stCaptionContainer"] p { color: var(--muted); font-size: 13px; }

/* Sidebar sits on the page ground, one hairline from the canvas */
[data-testid="stSidebar"] { background: var(--ground); border-right: 1px solid var(--border); }
.ehm-mark { display: flex; align-items: center; gap: 10px; margin: 0 0 22px; }
.ehm-mark svg { width: 28px; height: 28px; flex: none; }
.ehm-mark b { font-size: 15px; font-weight: 600; display: block; line-height: 18px; }
.ehm-mark span { font-size: 12px; color: var(--muted); }
[data-testid="stSidebar"] p.ehm-side-note { font-size: 12px; color: var(--muted); line-height: 18px; }

/* Cards: white on the ground, 1px edge, no shadow */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) { background: var(--surface); }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--border) !important; border-radius: 8px !important; }

/* Underline tabs on a full-width rule */
.stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { padding: 10px 0; background: none; color: var(--muted); font-size: 14px; }
.stTabs [data-baseweb="tab"] p { font-size: 14px; font-weight: 500; }
.stTabs [aria-selected="true"] { color: var(--ink); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--ink); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* Title row */
.ehm-title p { margin: 4px 0 0; color: var(--muted); font-size: 15px; line-height: 22px; max-width: 78ch; }
.ehm-title p b { color: var(--ink); font-weight: 500; }

/* KPI strip: one container split by dividers */
.ehm-kpis { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px; }
.ehm-kpis > div { padding: 14px 20px 16px; border-left: 1px solid var(--border); min-width: 0; }
.ehm-kpis > div:first-child { border-left: 0; }
.ehm-kpis label { display: block; font-size: 13px; color: var(--muted); }
.ehm-kpis strong { display: block; font-size: 24px; line-height: 32px; font-weight: 500; margin-top: 2px; }
.ehm-kpis strong small { font-size: 14px; color: var(--muted); font-weight: 400; margin-left: 3px; }
.ehm-kpis em { display: block; font-style: normal; font-size: 12px; color: var(--muted); margin-top: 2px; }
.ehm-kpis .lead strong { font-size: 30px; line-height: 36px; color: var(--hue); }

/* Key-value rows inside a card */
.ehm-kv { margin: 6px 0 0; }
.ehm-kv div { display: flex; justify-content: space-between; align-items: baseline; padding: 9px 0; border-top: 1px solid var(--rule); font-size: 14px; }
.ehm-kv dt { color: var(--muted); } .ehm-kv dd { margin: 0; font-weight: 500; }
.ehm-kv dd small { color: var(--muted); font-weight: 400; font-size: 12px; margin-left: 3px; }

.ehm-pill { display: inline-flex; align-items: center; height: 22px; padding: 0 9px; border-radius: 4px;
  font-size: 12px; font-weight: 500; white-space: nowrap; flex: none; }

/* Buttons: near-black primary, white secondary */
.stDownloadButton button, .stButton button { border-radius: 6px; min-height: 36px; font-weight: 500; }
.stDownloadButton button[kind="primary"] { background: #141414; border-color: #141414; color: #fff; }
.stDownloadButton button[kind="primary"]:hover { background: #2b2b2b; border-color: #2b2b2b; }
.stDownloadButton button:active { transform: translateY(1px); }

:is(button, input, [role="slider"], [role="tab"], [data-baseweb="select"] > div):focus-visible {
  outline: 2px solid var(--hue) !important; outline-offset: 2px; }

[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }

@media (max-width: 640px) {
  .block-container { padding: 4.2rem 1rem 3rem; }
  .ehm-kpis { grid-auto-flow: row; grid-template-columns: 1fr 1fr; }
  .ehm-kpis > div { border-left: 0; border-top: 1px solid var(--border); }
  .ehm-kpis > div:nth-child(-n+2) { border-top: 0; }
  .ehm-kpis > div:nth-child(even) { border-left: 1px solid var(--border); }
}
</style>
""".replace('__FACES__', FONT_FACES).replace('__STACK__', FONT_STACK)


MARK = ('<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14.5" fill="#fff" stroke="#0a0a0a" stroke-width="1.6"/>'
        + ''.join(f'<path d="M16 16 C 17.6 12, 18.6 7.5, 16.6 3.4 C 15.4 7, 15 11.5, 16 16Z" fill="#0a0a0a" transform="rotate({i * 45} 16 16)"/>'
                  for i in range(8))
        + '<circle cx="16" cy="16" r="3.2" fill="#1d5fbf"/></svg>')


def mark_html(fleet):
    return (f'<div class="ehm-mark">{MARK}<div><b>Engine Health Monitor</b>'
            f'<span>C-MAPSS fleet {fleet}</span></div></div>')


def pill(label):
    bg, ink = PILL[label]
    return f'<span class="ehm-pill" style="background:{bg};color:{ink}">{label}</span>'


def kpis(cells):
    """cells: list of (label, value, unit, caption, lead)."""
    out = []
    for label, value, unit, caption, lead in cells:
        u = f'<small>{unit}</small>' if unit else ''
        c = f'<em>{caption}</em>' if caption else ''
        out.append(f'<div class="{"lead" if lead else ""}"><label>{label}</label><strong>{value}{u}</strong>{c}</div>')
    return f'<div class="ehm-kpis">{"".join(out)}</div>'


def kv(rows):
    return '<dl class="ehm-kv">' + ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows) + '</dl>'


# ------------------------------------------------------------------ RUL dial
DIAL = r"""<!doctype html><html><head><meta charset="utf-8"><style>
__FACES__
html,body{margin:0;background:#fff;font-family:__STACK__;color:#0a0a0a;font-variant-numeric:tabular-nums}
svg{display:block;width:100%;height:auto;max-width:300px;margin:0 auto}
</style></head><body>
<svg id="g" viewBox="0 0 280 196" role="img"></svg>
<script>
const c = __DATA__;
const NS='http://www.w3.org/2000/svg', svg=document.getElementById('g');
svg.setAttribute('aria-label', `Predicted ${Math.round(c.pred)} cycles left of ${c.cap}; actual ${Math.round(c.actual)}`);
const cx=140, cy=140, R=112, A0=-200, A1=20;
const ang=v=>A0+(A1-A0)*(c.cap-Math.min(Math.max(v,0),c.cap))/c.cap;
const pt=(a,r)=>[cx+r*Math.cos(a*Math.PI/180), cy+r*Math.sin(a*Math.PI/180)];
const el=(t,a,p=svg)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e;};
const arc=(v0,v1,r)=>{const[x0,y0]=pt(ang(v0),r),[x1,y1]=pt(ang(v1),r);const L=Math.abs(ang(v1)-ang(v0))>180?1:0;return `M${x0} ${y0} A${r} ${r} 0 ${L} 1 ${x1} ${y1}`;};
el('path',{d:arc(c.cap,0,R),stroke:'#eceef1','stroke-width':10,fill:'none'});
[[c.amber,c.red,c.st['Plan maintenance']],[c.red,0,c.st['Critical']]].forEach(([a,b,col])=>
  el('path',{d:arc(a,b,R+9),stroke:col,'stroke-width':3,fill:'none'}));
for(let v=0;v<=c.cap;v+=25){const[x0,y0]=pt(ang(v),R-9),[x1,y1]=pt(ang(v),R-16);
  el('line',{x1:x0,y1:y0,x2:x1,y2:y1,stroke:'#5f6368','stroke-width':1.2});
  const[tx,ty]=pt(ang(v),R-28);const t=el('text',{x:tx,y:ty+4,'text-anchor':'middle',fill:'#5f6368','font-size':11});t.textContent=v;}
const fill=el('path',{stroke:'#1d5fbf','stroke-width':10,fill:'none'});
const[mx,my]=pt(ang(c.actual),R+8),[mx2,my2]=pt(ang(c.actual),R-8);
el('line',{x1:mx,y1:my,x2:mx2,y2:my2,stroke:'#0a0a0a','stroke-width':2});
const read=el('text',{x:cx,y:cy-2,'text-anchor':'middle','font-size':40,'font-weight':500,fill:'#1d5fbf'});
const lab=el('text',{x:cx,y:cy+20,'text-anchor':'middle','font-size':13,fill:'#5f6368'});lab.textContent='cycles left';
const set=v=>{fill.setAttribute('d',v<c.cap-0.5?arc(c.cap,v,R):'');read.textContent=Math.round(v);};
if(matchMedia('(prefers-reduced-motion: reduce)').matches) set(c.pred); else {
  const t0=performance.now(),D=650; (function step(n){const t=Math.min((n-t0)/D,1),k=1-Math.pow(1-t,3);
  set(c.cap+(c.pred-c.cap)*k); if(t<1)requestAnimationFrame(step);})(t0);}
</script></body></html>"""


def dial_html(pred, actual, red, amber, cap=125):
    data = json.dumps({'pred': float(pred), 'actual': float(min(actual, cap)), 'red': red, 'amber': amber,
                       'cap': cap, 'st': STATUS})
    return DIAL.replace('__FACES__', FONT_FACES).replace('__STACK__', FONT_STACK).replace('__DATA__', data)


# ------------------------------------------------------------------ 3D engine
ENGINE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
__FACES__
*{box-sizing:border-box}
html,body{margin:0;background:#fff;font-family:__STACK__;color:#0a0a0a;font-variant-numeric:tabular-nums}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;align-items:start}
.stage{position:relative;height:398px;border-radius:6px;background:#f7f8fa;outline:none;cursor:grab;touch-action:none}
.stage:active{cursor:grabbing}
.stage:focus-visible{box-shadow:0 0 0 2px #1d5fbf}
canvas{display:block;width:100%;height:100%;border-radius:6px}
.tools{position:absolute;left:12px;bottom:12px;display:flex;gap:8px}
button{font:500 13px __STACK__;height:32px;padding:0 12px;border-radius:6px;border:1px solid #d4d7dc;background:#fff;color:#0a0a0a;cursor:pointer}
button:hover{border-color:#9aa0a6} button:active{transform:translateY(1px)}
button[aria-pressed="true"]{background:#141414;border-color:#141414;color:#fff}
button:focus-visible{outline:2px solid #1d5fbf;outline-offset:2px}
.hint{position:absolute;right:12px;top:12px;font-size:12px;color:#5f6368}
#tip{position:absolute;pointer-events:none;background:#fff;border:1px solid #d4d7dc;border-radius:6px;padding:8px 10px;
  font-size:13px;line-height:18px;opacity:0;transition:opacity .12s;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,.08)}
#tip b{font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}
th{font-weight:400;color:#5f6368;text-align:left;padding:0 0 8px;font-size:12px}
th.n,td.n{text-align:right}
td{padding:9px 0;border-top:1px solid #eef0f3;vertical-align:top}
tr.row{cursor:default;outline:none}
tr.row td:first-child{padding-left:8px;border-left:2px solid transparent}
tr.row.on td:first-child{border-left-color:#1d5fbf}
tr.row.on td{background:#f7f8fa}
td small{display:block;color:#5f6368;font-size:12px;margin-top:2px}
.sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:7px;vertical-align:0}
.key{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:12px;color:#5f6368}
.ramp{display:flex;gap:2px}.ramp i{width:18px;height:8px;border-radius:2px}
@media (max-width:700px){.wrap{grid-template-columns:1fr}.stage{height:300px}.hint{display:none}}
</style></head><body>
<div class="wrap">
  <div class="stage" id="stage" tabindex="0" role="img" aria-label="">
    <canvas id="c"></canvas>
    <div class="tools"><button id="explode" aria-pressed="false">Exploded view</button><button id="reset">Reset view</button></div>
    <div class="hint">Drag or use the arrow keys to turn</div>
    <div id="tip" role="tooltip"></div>
  </div>
  <div>
    <table id="tbl"><thead><tr><th>Station</th><th class="n">Drift</th></tr></thead><tbody></tbody></table>
    <div class="key"><span>Under 1.5σ</span><span class="ramp" id="ramp"></span><span>4σ or more</span></div>
  </div>
</div>
<script>__THREE__</script>
<script>
const D = __DATA__;
const ORDER = ['Fan','LPC','HPC','Combustor','HPT','LPT'];
const NAMES = {Fan:'Fan',LPC:'Low-pressure compressor',HPC:'High-pressure compressor',Combustor:'Combustor',HPT:'High-pressure turbine',LPT:'Low-pressure turbine'};
const METAL = new THREE.Color('#aeb5bd'), BAD = new THREE.Color('#c4242a'), HUE = new THREE.Color('#1d5fbf');
const sevOf = z => Math.min(Math.max((Math.abs(z) - 1.5) / 2.5, 0), 1);   // tint starts at 1.5σ, full at 4σ
const tintOf = z => METAL.clone().lerp(BAD, sevOf(z) * 0.85);
const tint = s => tintOf(D.stations[s].drift);
document.getElementById('ramp').innerHTML = [1.5, 2.1, 2.8, 3.4, 4].map(z => `<i style="background:#${tintOf(z).getHexString()}"></i>`).join('');

// ---------- scene
const stage = document.getElementById('stage'), canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
camera.position.set(0, 0.6, 12.5); camera.lookAt(0, 0, 0);
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a9099, 0.85));
const key = new THREE.DirectionalLight(0xffffff, 1.35); key.position.set(4, 6, 7); scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, 0.55); rim.position.set(-6, -2, -5); scene.add(rim);

const pivot = new THREE.Group(); scene.add(pivot);
const engine = new THREE.Group(); engine.rotation.z = -Math.PI / 2; pivot.add(engine);  // engine axis = model Y -> world X
const groups = {}, mats = {}, pickables = [];
ORDER.forEach(s => { groups[s] = new THREE.Group(); engine.add(groups[s]);
  mats[s] = new THREE.MeshStandardMaterial({color: tint(s), metalness: 0.45, roughness: 0.42, side: THREE.DoubleSide}); });
const neutral = new THREE.MeshStandardMaterial({color: '#c9ced4', metalness: 0.3, roughness: 0.55, side: THREE.DoubleSide});
const shell = new THREE.MeshStandardMaterial({color: '#dfe3e8', metalness: 0.15, roughness: 0.6, side: THREE.DoubleSide, transparent: true, opacity: 1});
const V = (r, y) => new THREE.Vector2(r, y);
const CUT = Math.PI * 1.5;   // leaves the upper front quarter open

function lathe(pts, mat, parent, full, station) {
  const m = new THREE.Mesh(new THREE.LatheGeometry(pts, 96, 0, full ? Math.PI * 2 : CUT), mat);
  parent.add(m); if (station) { m.userData.station = station; pickables.push(m); } return m;
}
function ring(s, y, r0, r1, n, chord, twist) {
  const geo = new THREE.BoxGeometry(r1 - r0, chord, 0.028);
  const mesh = new THREE.InstancedMesh(geo, mats[s], n), d = new THREE.Object3D();
  for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, rm = (r0 + r1) / 2;
    d.position.set(Math.cos(a) * rm, y, Math.sin(a) * rm); d.rotation.set(twist, -a, 0, 'YXZ'); d.updateMatrix(); mesh.setMatrixAt(i, d.matrix); }
  mesh.userData.station = s; groups[s].add(mesh); pickables.push(mesh);
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(r0, r0, chord * 1.15, 48), mats[s]);
  hub.position.y = y; hub.userData.station = s; groups[s].add(hub); pickables.push(hub);
}

lathe([V(0,-3.25),V(0.16,-3.12),V(0.28,-2.9),V(0.36,-2.62),V(0.37,-2.3)], mats.Fan, groups.Fan, true, 'Fan');
ring('Fan', -2.45, 0.36, 1.66, 22, 0.42, 0.62);
[-1.95,-1.78,-1.61].forEach((y,i) => ring('LPC', y, 0.4, 0.74 - i*0.02, 34, 0.11, 0.45));
for (let i = 0; i < 7; i++) ring('HPC', -1.3 + i*0.18, 0.33, 0.64 - i*0.035, 40, 0.1, 0.4);
const comb = new THREE.Mesh(new THREE.TorusGeometry(0.47, 0.13, 24, 96), mats.Combustor);
comb.rotation.x = Math.PI / 2; comb.position.y = 0.2; comb.scale.set(1, 1, 2.2);
comb.userData.station = 'Combustor'; groups.Combustor.add(comb); pickables.push(comb);
lathe([V(0.36,-0.05),V(0.62,0.02),V(0.66,0.45),V(0.4,0.48)], mats.Combustor, groups.Combustor, false, 'Combustor');
[0.66, 0.84].forEach(y => ring('HPT', y, 0.34, 0.6, 38, 0.11, -0.5));
for (let i = 0; i < 4; i++) ring('LPT', 1.08 + i*0.19, 0.38, 0.72 + i*0.05, 42, 0.12, -0.45);
const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 4.8, 24), neutral); shaft.position.y = -0.2; engine.add(shaft);
lathe([V(0.38,1.75),V(0.33,2.2),V(0.16,2.62),V(0,2.8)], neutral, engine, true);
lathe([V(0.84,-2.15),V(0.95,-1.7),V(0.94,0.5),V(0.82,1.9),V(0.86,1.9),V(0.99,0.5),V(1.0,-1.7),V(0.9,-2.15)], shell, engine);
lathe([V(1.72,-2.95),V(1.84,-3.02),V(1.98,-2.7),V(2.04,-1.6),V(1.96,-0.2),V(1.8,0.55),V(1.74,0.55),V(1.76,-1.6),V(1.74,-2.7),V(1.72,-2.95)], shell, engine);

// ---------- table
const tbody = document.querySelector('#tbl tbody'), rows = {};
const fmt = z => (z >= 0 ? '+' : '−') + Math.abs(z).toFixed(1) + 'σ';
ORDER.forEach(s => { const st = D.stations[s], tr = document.createElement('tr');
  tr.className = 'row'; tr.tabIndex = 0; rows[s] = tr;
  const worst = st.sensors[0];
  tr.innerHTML = `<td><span class="sw" style="background:#${tint(s).getHexString()}"></span>${NAMES[s]}
      <small>${st.sensors.map(x => x.code).join(', ')}</small></td>
    <td class="n">${fmt(st.drift)}<small>${worst.label}</small></td>`;
  tr.setAttribute('aria-label', `${NAMES[s]}: drift ${fmt(st.drift)}, largest on ${worst.label}`);
  ['mouseenter','focus'].forEach(e => tr.addEventListener(e, () => highlight(s, null)));
  ['mouseleave','blur'].forEach(e => tr.addEventListener(e, () => highlight(null, null)));
  tbody.appendChild(tr); });
const worstStation = ORDER.slice().sort((a,b) => Math.abs(D.stations[b].drift) - Math.abs(D.stations[a].drift))[0];
stage.setAttribute('aria-label', `3D cutaway of engine ${D.engine}. Largest drift at the ${NAMES[worstStation]}, ` +
  `${fmt(D.stations[worstStation].drift)} from the healthy baseline.`);

// ---------- highlight + tooltip
const tip = document.getElementById('tip');
let current = null;
function highlight(s, at) {
  if (current !== s) {
    ORDER.forEach(k => { mats[k].emissive.set(k === s ? HUE : 0x000000); mats[k].emissiveIntensity = k === s ? 0.55 : 0; rows[k].classList.toggle('on', k === s); });
    current = s; render();
  }
  if (s && at) { const st = D.stations[s];
    tip.innerHTML = `<b>${NAMES[s]}</b><br>` + st.sensors.map(x => `${x.label}: ${x.value} ${x.unit} <span style="color:#5f6368">(${fmt(x.z)})</span>`).join('<br>');
    const r = stage.getBoundingClientRect();
    tip.style.left = Math.max(8, Math.min(at[0] - r.left + 14, r.width - tip.offsetWidth - 8)) + 'px';
    tip.style.top = Math.max(8, at[1] - r.top - tip.offsetHeight - 10) + 'px'; tip.style.opacity = 1;
  } else tip.style.opacity = 0;
}

// ---------- interaction
const HOME = {yaw: -0.62, pitch: 0.2};
let yaw = HOME.yaw, pitch = HOME.pitch, drag = null, explode = 0, target = 0;
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
function pick(x, y) { const r = canvas.getBoundingClientRect(); ndc.set((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ndc, camera); const hit = ray.intersectObjects(pickables, false)[0]; return hit ? hit.object.userData.station : null; }
stage.addEventListener('pointerdown', e => { if (e.target.closest('button')) return; drag = [e.clientX, e.clientY, yaw, pitch]; stage.setPointerCapture(e.pointerId); });
stage.addEventListener('pointermove', e => {
  if (drag) { yaw = drag[2] + (e.clientX - drag[0]) * 0.008; pitch = Math.max(-0.9, Math.min(0.9, drag[3] + (e.clientY - drag[1]) * 0.006)); render(); highlight(null); return; }
  if (e.target.closest('button')) { highlight(null); return; } highlight(pick(e.clientX, e.clientY), [e.clientX, e.clientY]); });
stage.addEventListener('pointerup', () => drag = null);
stage.addEventListener('pointerleave', () => { drag = null; highlight(null); });
stage.addEventListener('keydown', e => { const k = {ArrowLeft:[-.12,0],ArrowRight:[.12,0],ArrowUp:[0,-.1],ArrowDown:[0,.1]}[e.key];
  if (k) { yaw += k[0]; pitch = Math.max(-0.9, Math.min(0.9, pitch + k[1])); render(); e.preventDefault(); } });
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const exBtn = document.getElementById('explode');
exBtn.addEventListener('click', () => { target = target ? 0 : 1; exBtn.setAttribute('aria-pressed', target ? 'true' : 'false'); animate(); });
document.getElementById('reset').addEventListener('click', () => { yaw = HOME.yaw; pitch = HOME.pitch; target = 0; exBtn.setAttribute('aria-pressed','false'); animate(); });
const OFF = {Fan:-0.75, LPC:-0.42, HPC:-0.1, Combustor:0.25, HPT:0.6, LPT:1.0};
function applyExplode() { ORDER.forEach(s => groups[s].position.y = OFF[s] * explode);
  shell.opacity = 1 - 0.82 * explode; shell.depthWrite = explode < 0.5; }
function animate() { const t0 = performance.now(), e0 = explode, D2 = reduce ? 0 : 520;
  (function step(n) { const t = D2 ? Math.min((n - t0) / D2, 1) : 1, k = t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
    explode = e0 + (target - e0) * k; applyExplode(); render(); if (t < 1) requestAnimationFrame(step); })(t0); }

function size() { const r = stage.getBoundingClientRect(); if (!r.width) return; renderer.setSize(r.width, r.height, false);
  camera.aspect = r.width / r.height; camera.position.z = r.width < 520 ? 15.5 : 12.5; camera.updateProjectionMatrix(); render(); }
function render() { pivot.rotation.set(pitch, yaw, 0, 'XYZ'); renderer.render(scene, camera); }
new ResizeObserver(size).observe(stage); applyExplode(); size();
</script></body></html>"""


def engine_html(engine_id, stations):
    data = json.dumps({'engine': int(engine_id), 'stations': stations})
    return (ENGINE.replace('__FACES__', FONT_FACES).replace('__STACK__', FONT_STACK)
            .replace('__THREE__', THREE_JS).replace('__DATA__', data))


# ------------------------------------------------------------------ hangar board
HANGAR = r"""<!doctype html><html><head><meta charset="utf-8"><style>
__FACES__
html,body{margin:0;font-family:__STACK__;color:#0a0a0a;background:#fff;font-variant-numeric:tabular-nums}
.board{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px}
@media (max-width:600px){.board{grid-template-columns:repeat(4,minmax(0,1fr))}}
.t{position:relative;height:54px;border:1px solid #e3e6ea;border-radius:6px;padding:6px 8px;outline:none;background:#fff}
.t:hover,.t:focus-visible{border-color:#0a0a0a}
.t .n{font-size:12px;color:#5f6368;line-height:14px}
.t .r{font-size:17px;font-weight:500;line-height:22px}
.t .bar{position:absolute;left:8px;right:8px;bottom:6px;height:3px;background:#eef0f3;border-radius:2px}
.t .bar i{display:block;height:100%;border-radius:2px}
#tip{position:fixed;pointer-events:none;background:#fff;border:1px solid #d4d7dc;border-radius:6px;padding:7px 10px;
  font-size:13px;line-height:18px;opacity:0;z-index:9;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,.08)}
</style></head><body>
<div class="board" id="b" role="list"></div><div id="tip" role="tooltip"></div>
<script>
const rows = __DATA__, col = __STATUS__, b = document.getElementById('b'), tip = document.getElementById('tip');
rows.forEach(r => {
  const d = document.createElement('div'); d.className = 't'; d.tabIndex = 0; d.setAttribute('role','listitem');
  d.setAttribute('aria-label', `Engine ${r.Engine}, ${r.Status}, ${r.Predicted} cycles predicted, ${r.Actual} actual`);
  d.innerHTML = `<div class="n">Engine ${r.Engine}</div><div class="r">${r.Predicted}</div>
    <div class="bar"><i style="width:${Math.min(r.Predicted,125)/125*100}%;background:${col[r.Status]}"></i></div>`;
  const show = (x,y) => { tip.innerHTML = `<b>Engine ${r.Engine}</b>, ${r.Status.toLowerCase()}<br>Predicted ${r.Predicted} cycles, actual ${r.Actual}`;
    tip.style.left = Math.min(x + 14, innerWidth - tip.offsetWidth - 8) + 'px'; tip.style.top = Math.max(8, y - 54) + 'px'; tip.style.opacity = 1; };
  d.addEventListener('mousemove', e => show(e.clientX, e.clientY));
  d.addEventListener('focus', () => { const q = d.getBoundingClientRect(); show(q.right, q.top + 50); });
  ['mouseleave','blur'].forEach(ev => d.addEventListener(ev, () => tip.style.opacity = 0));
  b.appendChild(d);
});
</script></body></html>"""


def hangar_html(rows):
    return (HANGAR.replace('__FACES__', FONT_FACES).replace('__STACK__', FONT_STACK)
            .replace('__DATA__', json.dumps(rows)).replace('__STATUS__', json.dumps(STATUS)))


def styled(chart):
    f = 'Geist, Segoe UI, sans-serif'
    return (chart.configure(font=f)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, titleFont=f, labelFont=f, titleFontWeight=400,
                            titleFontSize=12, labelFontSize=12, gridColor='#e8eaed', domain=False, tickColor='#e8eaed')
            .configure_axisX(domain=True, domainColor='#9aa0a6')
            .configure_legend(labelColor=INK, titleColor=MUTED, labelFontSize=12, labelFont=f, titleFont=f, orient='top')
            .configure_title(font=f, fontSize=14, fontWeight=500, color=INK, anchor='start')
            .configure_view(stroke=None))

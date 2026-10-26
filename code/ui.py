"""Visual layer for the Engine Health Monitor.

Style: achromatic ledger. The chrome is neutral ink; the one hue marks the prediction and
status colours appear only on status. Three looks share every token name: Light, Graphite
and Black. Signature element: a 3D cutaway of the turbofan, each station tinted by how far
its own sensors have drifted from a healthy engine.

Motion follows one set of curves: --ease-out for anything that responds to the user,
--ease-in-out for things that move on screen. Nothing animates on its own.
"""
import base64
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_HERE, 'static')
LOOKS = ['Light', 'Graphite', 'Black']

_STATUS_LIGHT = {'Critical': '#c4242a', 'Plan maintenance': '#b45309', 'Healthy': '#2e7d32'}
_STATUS_DARK = {'Critical': '#f0616d', 'Plan maintenance': '#e0a63a', 'Healthy': '#3fc07a'}

THEMES = {
    'Light': dict(
        dark=False, ground='#f2f4f7', surface='#ffffff', stage='#f6f7f9', raised='#eceef1', border='#e3e6ea',
        rule='#eef0f3', control='#d4d7dc', text='#0a0a0a', muted='#5f6368', hue='#1d5fbf', comp='#8a8f96',
        grid='#e8eaed', axis='#9aa0a6', primary_bg='#141414', primary_ink='#ffffff', primary_hover='#2b2b2b',
        negative='#c4242a', status=_STATUS_LIGHT,
        pill={'Critical': ('#ffedea', '#831c1e'), 'Plan maintenance': ('#fffbeb', '#92400e'), 'Healthy': ('#dcfae5', '#04250e')},
        metal='#aeb5bd', shell='#dfe3e8', neutral='#c9ced4', env=0.55, shadow=0.16, tip_shadow='rgba(0,0,0,.08)'),
    'Graphite': dict(
        dark=True, ground='#141414', surface='#1b1b1b', stage='#202020', raised='#242424', border='#2c2c2c',
        rule='#252525', control='#3d3d3d', text='#f4f4f4', muted='#a8a8a8', hue='#6ea1f7', comp='#8c8c8c',
        grid='#2a2a2a', axis='#5c5c5c', primary_bg='#f4f4f4', primary_ink='#111111', primary_hover='#ffffff',
        negative='#f0616d', status=_STATUS_DARK,
        pill={'Critical': ('#2c1a1d', '#f08a96'), 'Plan maintenance': ('#2a2112', '#e9b45a'), 'Healthy': ('#172a1d', '#4fd18b')},
        metal='#8d949c', shell='#3a3e43', neutral='#5b6067', env=0.8, shadow=0.45, tip_shadow='rgba(0,0,0,.4)'),
    'Black': dict(
        dark=True, ground='#000000', surface='#0e0e0e', stage='#121212', raised='#181818', border='#1f1f1f',
        rule='#181818', control='#3a3a3a', text='#ffffff', muted='#a3a3a3', hue='#6ea1f7', comp='#8a8a8a',
        grid='#1f1f1f', axis='#4c4c4c', primary_bg='#ffffff', primary_ink='#000000', primary_hover='#e6e6e6',
        negative='#f0616d', status=_STATUS_DARK,
        pill={'Critical': ('#2c1a1d', '#f08a96'), 'Plan maintenance': ('#2a2112', '#e9b45a'), 'Healthy': ('#172a1d', '#4fd18b')},
        metal='#8d949c', shell='#2f3236', neutral='#55595f', env=0.9, shadow=0.6, tip_shadow='rgba(0,0,0,.5)'),
}


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
EASE_OUT, EASE_IN_OUT = 'cubic-bezier(0.23, 1, 0.32, 1)', 'cubic-bezier(0.77, 0, 0.175, 1)'


def _vars(t):
    keys = ['ground', 'surface', 'stage', 'raised', 'border', 'rule', 'control', 'text', 'muted', 'hue',
            'primary_bg', 'primary_ink', 'primary_hover', 'negative', 'tip_shadow']
    v = ''.join(f'--{k.replace("_", "-")}:{t[k]};' for k in keys)
    return (f':root{{{v}--ease-out:{EASE_OUT};--ease-in-out:{EASE_IN_OUT};'
            f'color-scheme:{"dark" if t["dark"] else "light"};}}')


def _frame(t, css, body):
    """A self-contained page for a components.html iframe, themed with the same tokens."""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONT_FACES}{_vars(t)}'
            f'*{{box-sizing:border-box}}html,body{{margin:0;background:var(--surface);color:var(--text);'
            f'font-family:{FONT_STACK};font-variant-numeric:tabular-nums}}{css}</style></head><body>{body}</body></html>')


# ------------------------------------------------------------------ page CSS
def css(t):
    s = """
<style>
__FACES__ __VARS__
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  font-family: __STACK__; color: var(--text); font-variant-numeric: tabular-nums; }
[data-testid="stAppViewContainer"] *:not([data-testid="stIconMaterial"]):not([class*="material"]) { font-family: __STACK__; }
span[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] { background: var(--ground); }
.block-container { padding: 3.6rem 2rem 4rem; max-width: 1320px; }

h1, h2, h3, [data-testid="stHeading"] * { font-family: __STACK__ !important; color: var(--text); letter-spacing: 0; }
h1 { font-size: 24px !important; font-weight: 600 !important; line-height: 32px !important; padding: 0 !important; letter-spacing: -0.01em; }
h2 { font-size: 20px !important; font-weight: 600 !important; padding: 0 !important; }
h3 { font-size: 16px !important; font-weight: 600 !important; padding: 0 0 4px !important; }
p, li { font-size: 14px; }
[data-testid="stCaptionContainer"] p { color: var(--muted); font-size: 13px; }

[data-testid="stSidebar"] { background: var(--ground); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] p.ehm-side-note { font-size: 12px; color: var(--muted); line-height: 18px; }
.ehm-mark { display: flex; align-items: center; gap: 10px; margin: 0 0 22px; }
.ehm-mark svg { width: 28px; height: 28px; flex: none; }
.ehm-mark b { font-size: 15px; font-weight: 600; display: block; line-height: 18px; color: var(--text); }
.ehm-mark span { font-size: 12px; color: var(--muted); }

[class*="st-key-card-"] { background: var(--surface); border-color: var(--border) !important; border-radius: 12px !important; }

.stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--border); background: transparent; }
.stTabs [data-baseweb="tab"] { padding: 10px 0; background: none; color: var(--muted); transition: color 150ms ease; }
.stTabs [data-baseweb="tab"] p { font-size: 14px; font-weight: 500; }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { color: var(--text); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--text); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

.ehm-title p { margin: 4px 0 0; color: var(--muted); font-size: 15px; line-height: 22px; max-width: 78ch; }
.ehm-title p b { color: var(--text); font-weight: 500; }

.ehm-kpis { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; background: var(--surface);
  border: 1px solid var(--border); border-radius: 10px; }
.ehm-kpis > div { padding: 14px 20px 16px; border-left: 1px solid var(--border); min-width: 0; }
.ehm-kpis > div:first-child { border-left: 0; }
.ehm-kpis label { display: block; font-size: 13px; color: var(--muted); }
.ehm-kpis strong { display: block; font-size: 24px; line-height: 32px; font-weight: 500; margin-top: 2px; color: var(--text); }
.ehm-kpis strong small { font-size: 14px; color: var(--muted); font-weight: 400; margin-left: 3px; }
.ehm-kpis em { display: block; font-style: normal; font-size: 12px; color: var(--muted); margin-top: 2px; }

.ehm-kv { margin: 6px 0 0; }
.ehm-kv div { display: flex; justify-content: space-between; align-items: baseline; padding: 9px 0; border-top: 1px solid var(--rule); font-size: 14px; }
.ehm-kv dt { color: var(--muted); } .ehm-kv dd { margin: 0; font-weight: 500; color: var(--text); }
.ehm-kv dd small { color: var(--muted); font-weight: 400; font-size: 12px; margin-left: 3px; }

.ehm-pill { display: inline-flex; align-items: center; height: 22px; padding: 0 9px; border-radius: 5px;
  font-size: 12px; font-weight: 500; white-space: nowrap; flex: none; vertical-align: 3px; }

/* Buttons: one filled primary, pressed state on everything pressable */
.stDownloadButton button, .stButton button { border-radius: 8px; min-height: 36px; font-weight: 500;
  transition: transform 160ms var(--ease-out), background-color 150ms ease, border-color 150ms ease; }
.stDownloadButton button:active, .stButton button:active { transform: scale(0.97); }
.stDownloadButton button[kind="primary"] { background: var(--primary-bg); border-color: var(--primary-bg); color: var(--primary-ink); }
.stDownloadButton button[kind="primary"] p { color: var(--primary-ink); }
@media (hover: hover) and (pointer: fine) {
  .stDownloadButton button[kind="primary"]:hover { background: var(--primary-hover); border-color: var(--primary-hover); }
}
[data-testid="stSegmentedControl"] button { transition: transform 160ms var(--ease-out), background-color 150ms ease; }
[data-testid="stSegmentedControl"] button:active { transform: scale(0.97); }

:is(button, input, [role="slider"], [role="tab"], [data-baseweb="select"] > div):focus-visible {
  outline: 2px solid var(--hue) !important; outline-offset: 2px; }

[data-testid="stElementContainer"]:has(> div > iframe[height="0"]),
[data-testid="stElementContainer"]:has(iframe[height="0"]) { display: none; }

@media (max-width: 640px) {
  .block-container { padding: 4.2rem 1rem 3rem; }
  .ehm-kpis { grid-auto-flow: row; grid-template-columns: 1fr 1fr; }
  .ehm-kpis > div { border-left: 0; border-top: 1px solid var(--border); }
  .ehm-kpis > div:nth-child(-n+2) { border-top: 0; }
  .ehm-kpis > div:nth-child(even) { border-left: 1px solid var(--border); }
  .ehm-kpis > div:last-child:nth-child(odd) { grid-column: 1 / -1; }
}
</style>
"""
    return s.replace('__FACES__', FONT_FACES).replace('__VARS__', _vars(t)).replace('__STACK__', FONT_STACK)


def theme_sync_html(dark):
    """Keeps Streamlit's own widgets (selects, sliders, tables) on the same light or dark base."""
    want = 'Dark' if dark else 'Light'
    return f"""<script>
try {{
  const P = window.parent, key = `stActiveTheme-${{P.location.pathname}}-v2`, want = JSON.stringify('{want}');
  if (P.localStorage.getItem(key) !== want) {{
    const n = +(P.sessionStorage.getItem('ehm-theme-sync') || 0);
    if (n < 2) {{ P.sessionStorage.setItem('ehm-theme-sync', n + 1); P.localStorage.setItem(key, want); P.location.reload(); }}
  }} else P.sessionStorage.removeItem('ehm-theme-sync');
}} catch (e) {{}}
</script>"""


def mark_html(t, fleet):
    blades = ''.join(f'<path d="M16 16 C 17.6 12, 18.6 7.5, 16.6 3.4 C 15.4 7, 15 11.5, 16 16Z" fill="{t["text"]}" '
                     f'transform="rotate({i * 45} 16 16)"/>' for i in range(8))
    svg = (f'<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14.5" fill="{t["surface"]}" '
           f'stroke="{t["text"]}" stroke-width="1.6"/>{blades}<circle cx="16" cy="16" r="3.2" fill="{t["hue"]}"/></svg>')
    return (f'<div class="ehm-mark">{svg}<div><b>Engine Health Monitor</b>'
            f'<span>C-MAPSS fleet {fleet}</span></div></div>')


def pill(t, label):
    bg, ink = t['pill'][label]
    return f'<span class="ehm-pill" style="background:{bg};color:{ink}">{label}</span>'


def kpis(cells):
    out = []
    for label, value, unit, caption in cells:
        u = f'<small>{unit}</small>' if unit else ''
        c = f'<em>{caption}</em>' if caption else ''
        out.append(f'<div><label>{label}</label><strong>{value}{u}</strong>{c}</div>')
    return f'<div class="ehm-kpis">{"".join(out)}</div>'


def kv(rows):
    return '<dl class="ehm-kv">' + ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows) + '</dl>'


# ------------------------------------------------------------------ shared JS: cubic-bezier easing
BEZIER = """
function bezier(x1, y1, x2, y2) {            // CSS cubic-bezier as a JS easing function
  const cx = 3*x1, bx = 3*(x2-x1)-cx, ax = 1-cx-bx, cy = 3*y1, by = 3*(y2-y1)-cy, ay = 1-cy-by;
  const X = t => ((ax*t+bx)*t+cx)*t, Y = t => ((ay*t+by)*t+cy)*t, dX = t => (3*ax*t+2*bx)*t+cx;
  return x => { let t = x; for (let i = 0; i < 6; i++) { const d = dX(t); if (Math.abs(d) < 1e-6) break; t -= (X(t)-x)/d; }
    return Y(Math.min(Math.max(t, 0), 1)); };
}
const easeOut = bezier(0.23, 1, 0.32, 1), easeInOut = bezier(0.77, 0, 0.175, 1);
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
"""


# ------------------------------------------------------------------ RUL dial
def dial_html(t, pred, actual, red, amber, cap=125):
    data = json.dumps({'pred': float(pred), 'actual': float(min(actual, cap)), 'red': red, 'amber': amber,
                       'cap': cap, 'st': t['status'], 'track': t['raised'], 'tick': t['muted'], 'hue': t['hue'],
                       'ink': t['text']})
    body = """<svg id="g" viewBox="0 0 280 196" role="img"></svg>
<script>""" + BEZIER + """
const c = __DATA__;
const NS='http://www.w3.org/2000/svg', svg=document.getElementById('g');
svg.setAttribute('aria-label', `Predicted ${Math.round(c.pred)} cycles left of ${c.cap}; actual ${Math.round(c.actual)}`);
const cx=140, cy=140, R=112, A0=-200, A1=20;
const ang=v=>A0+(A1-A0)*(c.cap-Math.min(Math.max(v,0),c.cap))/c.cap;
const pt=(a,r)=>[cx+r*Math.cos(a*Math.PI/180), cy+r*Math.sin(a*Math.PI/180)];
const el=(n,a,p=svg)=>{const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);p.appendChild(e);return e;};
const arc=(v0,v1,r)=>{const[x0,y0]=pt(ang(v0),r),[x1,y1]=pt(ang(v1),r);const L=Math.abs(ang(v1)-ang(v0))>180?1:0;return `M${x0} ${y0} A${r} ${r} 0 ${L} 1 ${x1} ${y1}`;};
el('path',{d:arc(c.cap,0,R),stroke:c.track,'stroke-width':10,fill:'none','stroke-linecap':'butt'});
[[c.amber,c.red,c.st['Plan maintenance']],[c.red,0,c.st['Critical']]].forEach(([a,b,col])=>
  el('path',{d:arc(a,b,R+9),stroke:col,'stroke-width':3,fill:'none'}));
for(let v=0;v<=c.cap;v+=25){const[x0,y0]=pt(ang(v),R-9),[x1,y1]=pt(ang(v),R-16);
  el('line',{x1:x0,y1:y0,x2:x1,y2:y1,stroke:c.tick,'stroke-width':1.2});
  const[tx,ty]=pt(ang(v),R-28);const t=el('text',{x:tx,y:ty+4,'text-anchor':'middle',fill:c.tick,'font-size':11});t.textContent=v;}
const fill=el('path',{stroke:c.hue,'stroke-width':10,fill:'none'});
const[mx,my]=pt(ang(c.actual),R+8),[mx2,my2]=pt(ang(c.actual),R-8);
el('line',{x1:mx,y1:my,x2:mx2,y2:my2,stroke:c.ink,'stroke-width':2});
const read=el('text',{x:cx,y:cy-2,'text-anchor':'middle','font-size':40,'font-weight':500,fill:c.hue,'letter-spacing':'-0.02em'});
const lab=el('text',{x:cx,y:cy+20,'text-anchor':'middle','font-size':13,fill:c.tick});lab.textContent='cycles left';
const set=v=>{fill.setAttribute('d',v<c.cap-0.5?arc(c.cap,v,R):'');read.textContent=Math.round(v);};
if (reduce) set(c.pred); else { const t0=performance.now(), D=620;
  (function step(n){const t=Math.min((n-t0)/D,1); set(c.cap+(c.pred-c.cap)*easeOut(t)); if(t<1)requestAnimationFrame(step);})(t0); }
</script>""".replace('__DATA__', data)
    return _frame(t, 'svg{display:block;width:100%;height:auto;max-width:300px;margin:0 auto}', body)


# ------------------------------------------------------------------ 3D engine
ENGINE_CSS = """
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;align-items:start}
.stage{position:relative;height:398px;border-radius:8px;background:var(--stage);outline:none;cursor:grab;touch-action:none;overflow:hidden}
.stage.dragging{cursor:grabbing}
.stage:focus-visible{box-shadow:0 0 0 2px var(--hue)}
canvas{display:block;width:100%;height:100%}
.tools{position:absolute;left:12px;bottom:12px;display:flex;gap:8px}
button{font-family:inherit;font-weight:500;font-size:13px;height:32px;padding:0 12px;border-radius:8px;border:1px solid var(--control);
  background:var(--surface);color:var(--text);cursor:pointer;
  transition:transform 160ms var(--ease-out),background-color 150ms ease,border-color 150ms ease,color 150ms ease}
button:active{transform:scale(0.97)}
button[aria-pressed="true"]{background:var(--primary-bg);border-color:var(--primary-bg);color:var(--primary-ink)}
button:focus-visible{outline:2px solid var(--hue);outline-offset:2px}
@media (hover:hover) and (pointer:fine){button:hover{border-color:var(--muted)}}
.hint{position:absolute;right:12px;top:12px;font-size:12px;color:var(--muted)}
#tip{position:absolute;left:0;top:0;pointer-events:none;background:var(--surface);border:1px solid var(--control);border-radius:8px;
  padding:8px 10px;font-size:13px;line-height:18px;white-space:nowrap;box-shadow:0 6px 20px var(--tip-shadow);
  opacity:0;transform:scale(0.97);transform-origin:left bottom;transition:opacity 150ms var(--ease-out),transform 150ms var(--ease-out)}
#tip.on{opacity:1;transform:scale(1)}
#tip b{font-weight:600} #tip span{color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{font-weight:400;color:var(--muted);text-align:left;padding:0 0 8px;font-size:12px}
th.n,td.n{text-align:right}
td{padding:9px 0;border-top:1px solid var(--rule);vertical-align:top}
tr.row{cursor:default;outline:none}
tr.row td{transition:background-color 150ms ease}
tr.row td:first-child{padding-left:8px;border-left:2px solid transparent;transition:border-color 150ms ease,background-color 150ms ease}
tr.row.on td{background:var(--stage)} tr.row.on td:first-child{border-left-color:var(--hue)}
td small{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:7px}
.key{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:12px;color:var(--muted)}
.ramp{display:flex;gap:2px}.ramp i{width:18px;height:8px;border-radius:2px}
@media (max-width:700px){.wrap{grid-template-columns:1fr}.stage{height:300px}.hint{display:none}}
"""

ENGINE_BODY = """
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
<script>__BEZIER__
const D = __DATA__, T = D.theme;
const ORDER = ['Fan','LPC','HPC','Combustor','HPT','LPT'];
const NAMES = {Fan:'Fan',LPC:'Low-pressure compressor',HPC:'High-pressure compressor',Combustor:'Combustor',HPT:'High-pressure turbine',LPT:'Low-pressure turbine'};
const METAL = new THREE.Color(T.metal), BAD = new THREE.Color(T.bad), HUE = new THREE.Color(T.hue);
const sevOf = z => Math.min(Math.max((Math.abs(z) - 1.5) / 2.5, 0), 1);
const tintOf = z => METAL.clone().lerp(BAD, sevOf(z) * 0.85);
const tint = s => tintOf(D.stations[s].drift);
document.getElementById('ramp').innerHTML = [1.5, 2.1, 2.8, 3.4, 4].map(z => `<i style="background:#${tintOf(z).getHexString()}"></i>`).join('');

// ---------- renderer, studio light and reflections
const stage = document.getElementById('stage'), canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = T.dark ? 1.15 : 1.0;
const scene = new THREE.Scene();
(function studio() {                         // a small softbox room, baked into a reflection map
  const room = new THREE.Scene(), box = new THREE.BoxGeometry(1, 1, 1);
  const walls = new THREE.Mesh(box, new THREE.MeshBasicMaterial({color: T.dark ? 0x1a1a1a : 0x9aa0a8, side: THREE.BackSide}));
  walls.scale.set(20, 12, 20); room.add(walls);
  [[0, 5.5, 0, 9, 0.2, 5, 3.2], [-9.5, 2, 1, 0.2, 4, 7, 2.2], [9.5, 1, -2, 0.2, 3, 5, 1.4], [0, 0, 9.5, 8, 3, 0.2, 0.9]]
    .forEach(([x, y, z, sx, sy, sz, k]) => { const m = new THREE.Mesh(box, new THREE.MeshBasicMaterial({color: new THREE.Color(k, k, k)}));
      m.position.set(x, y, z); m.scale.set(sx, sy, sz); room.add(m); });
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(room, 0.035).texture; pm.dispose();
})();
const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
camera.position.set(0, 0.6, 12.5); camera.lookAt(0, 0, 0);
const key = new THREE.DirectionalLight(0xffffff, T.dark ? 0.9 : 0.8); key.position.set(4, 6, 7); scene.add(key);
const rim = new THREE.DirectionalLight(0xffffff, T.dark ? 0.9 : 0.35); rim.position.set(-6, 2, -6); scene.add(rim);

// soft contact shadow, drawn once into a canvas
(function contactShadow() {
  const cv = document.createElement('canvas'); cv.width = cv.height = 128; const g = cv.getContext('2d');
  const rg = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  rg.addColorStop(0, `rgba(0,0,0,${T.shadow})`); rg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = rg; g.fillRect(0, 0, 128, 128);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(9, 2.2), new THREE.MeshBasicMaterial({map: new THREE.CanvasTexture(cv), transparent: true, depthWrite: false}));
  m.rotation.x = -Math.PI / 2; m.position.y = -2.35; scene.add(m);
})();

const pivot = new THREE.Group(); scene.add(pivot);
const engine = new THREE.Group(); engine.rotation.z = -Math.PI / 2; pivot.add(engine);
const groups = {}, mats = {}, pickables = [];
ORDER.forEach(s => { groups[s] = new THREE.Group(); engine.add(groups[s]);
  mats[s] = new THREE.MeshStandardMaterial({color: tint(s), metalness: 0.72, roughness: 0.34, envMapIntensity: T.env, side: THREE.DoubleSide}); });
const neutral = new THREE.MeshStandardMaterial({color: T.neutral, metalness: 0.6, roughness: 0.4, envMapIntensity: T.env, side: THREE.DoubleSide});
const shell = new THREE.MeshStandardMaterial({color: T.shell, metalness: 0.35, roughness: 0.5, envMapIntensity: T.env, side: THREE.DoubleSide, transparent: true, opacity: 1});
const V = (r, y) => new THREE.Vector2(r, y), CUT = Math.PI * 1.5;
function lathe(pts, mat, parent, full, station) {
  const m = new THREE.Mesh(new THREE.LatheGeometry(pts, 96, 0, full ? Math.PI * 2 : CUT), mat);
  parent.add(m); if (station) { m.userData.station = station; pickables.push(m); } return m;
}
function ring(s, y, r0, r1, n, chord, twist) {
  const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(r1 - r0, chord, 0.028), mats[s], n), d = new THREE.Object3D();
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
  tr.className = 'row'; tr.tabIndex = 0; rows[s] = tr; const worst = st.sensors[0];
  tr.innerHTML = `<td><span class="sw" style="background:#${tint(s).getHexString()}"></span>${NAMES[s]}
      <small>${st.sensors.map(x => x.code).join(', ')}</small></td><td class="n">${fmt(st.drift)}<small>${worst.label}</small></td>`;
  tr.setAttribute('aria-label', `${NAMES[s]}: drift ${fmt(st.drift)}, largest on ${worst.label}`);
  ['mouseenter','focus'].forEach(e => tr.addEventListener(e, () => highlight(s, null)));
  ['mouseleave','blur'].forEach(e => tr.addEventListener(e, () => highlight(null, null)));
  tbody.appendChild(tr); });
const worstStation = ORDER.slice().sort((a,b) => Math.abs(D.stations[b].drift) - Math.abs(D.stations[a].drift))[0];
stage.setAttribute('aria-label', `3D cutaway of engine ${D.engine}. Largest drift at the ${NAMES[worstStation]}, ${fmt(D.stations[worstStation].drift)} from a healthy engine.`);

// ---------- highlight + tooltip (instant once open, eased on first show)
const tip = document.getElementById('tip'); let current = null;
function highlight(s, at) {
  if (current !== s) {
    ORDER.forEach(k => { mats[k].emissive.set(k === s ? HUE : 0x000000); mats[k].emissiveIntensity = k === s ? (T.dark ? 0.35 : 0.5) : 0; rows[k].classList.toggle('on', k === s); });
    current = s; if (s && at) tip.innerHTML = `<b>${NAMES[s]}</b><br>` + D.stations[s].sensors.map(x => `${x.label}: ${x.value} ${x.unit} <span>(${fmt(x.z)})</span>`).join('<br>');
    render();
  }
  if (s && at) { const r = stage.getBoundingClientRect();
    const x = Math.max(8, Math.min(at[0] - r.left + 14, r.width - tip.offsetWidth - 8)), y = Math.max(8, at[1] - r.top - tip.offsetHeight - 10);
    tip.style.left = x + 'px'; tip.style.top = y + 'px'; tip.classList.add('on');
  } else tip.classList.remove('on');
}

// ---------- orbit with momentum, rubber-band at the pitch limits, eased reset
const HOME = {yaw: -0.62, pitch: 0.2}, LIM = 0.85;
let yaw = HOME.yaw, pitch = HOME.pitch, drag = null, vel = [0, 0], anim = 0, explode = 0, target = 0;
const band = p => Math.abs(p) <= LIM ? p : Math.sign(p) * (LIM + (Math.abs(p) - LIM) * 0.3);
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
function pick(x, y) { const r = canvas.getBoundingClientRect(); ndc.set((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1);
  ray.setFromCamera(ndc, camera); const hit = ray.intersectObjects(pickables, false)[0]; return hit ? hit.object.userData.station : null; }
function stop() { anim++; }
stage.addEventListener('pointerdown', e => { if (e.target.closest('button') || drag || !e.isPrimary) return; stop();
  drag = {x: e.clientX, y: e.clientY, yaw, raw: pitch, t: performance.now()}; vel = [0, 0];
  stage.setPointerCapture(e.pointerId); stage.classList.add('dragging'); highlight(null); });
stage.addEventListener('pointermove', e => {
  if (drag) { const now = performance.now(), dt = Math.max(now - drag.t, 1);
    const dyaw = (e.clientX - drag.x) * 0.008, dp = (e.clientY - drag.y) * 0.006;
    vel = [dyaw / dt, dp / dt]; yaw += dyaw; drag.raw += dp; pitch = band(drag.raw);
    drag.x = e.clientX; drag.y = e.clientY; drag.t = now; render(); return; }
  if (e.target.closest('button')) { highlight(null); return; } highlight(pick(e.clientX, e.clientY), [e.clientX, e.clientY]); });
function release() { if (!drag) return; stage.classList.remove('dragging');
  const quiet = performance.now() - drag.t > 80; drag = null; if (reduce) { pitch = Math.max(-LIM, Math.min(LIM, pitch)); render(); return; }
  let [vy, vp] = quiet ? [0, 0] : vel; const id = ++anim; let last = performance.now();
  (function coast(n) { if (id !== anim) return; const dt = Math.min(n - last, 32); last = n;
    const f = Math.pow(0.0025, dt / 1000);                          // friction: velocity decays smoothly
    yaw += vy * dt; pitch += vp * dt * 0.4; vy *= f; vp *= f;
    if (Math.abs(pitch) > LIM) { pitch += (Math.sign(pitch) * LIM - pitch) * Math.min(1, dt / 90); vp = 0; }   // spring back
    render(); if (Math.abs(vy) > 1e-5 || Math.abs(pitch) > LIM + 1e-3) requestAnimationFrame(coast); })(last); }
stage.addEventListener('pointerup', release); stage.addEventListener('pointercancel', release);
stage.addEventListener('pointerleave', () => { if (!drag) highlight(null); });
stage.addEventListener('keydown', e => { const k = {ArrowLeft:[-.12,0],ArrowRight:[.12,0],ArrowUp:[0,-.1],ArrowDown:[0,.1]}[e.key];
  if (k) { stop(); yaw += k[0]; pitch = Math.max(-LIM, Math.min(LIM, pitch + k[1])); render(); e.preventDefault(); } });   // keys: no animation
function tween(dur, ease, fn) { const id = ++anim, t0 = performance.now();
  if (reduce || !dur) { fn(1); render(); return; }
  (function step(n) { if (id !== anim) return; const t = Math.min((n - t0) / dur, 1); fn(ease(t)); render(); if (t < 1) requestAnimationFrame(step); })(t0); }
const exBtn = document.getElementById('explode');
const OFF = {Fan:-0.75, LPC:-0.42, HPC:-0.1, Combustor:0.25, HPT:0.6, LPT:1.0};
function applyExplode() { ORDER.forEach(s => groups[s].position.y = OFF[s] * explode); shell.opacity = 1 - 0.84 * explode; shell.depthWrite = explode < 0.5; }
exBtn.addEventListener('click', () => { target = target ? 0 : 1; exBtn.setAttribute('aria-pressed', target ? 'true' : 'false');
  const e0 = explode, e1 = target; tween(440, easeInOut, k => { explode = e0 + (e1 - e0) * k; applyExplode(); }); });
document.getElementById('reset').addEventListener('click', () => { const y0 = yaw, p0 = pitch, e0 = explode; target = 0;
  exBtn.setAttribute('aria-pressed', 'false');
  const dy = ((HOME.yaw - y0 + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;   // shortest way round
  tween(380, easeOut, k => { yaw = y0 + dy * k; pitch = p0 + (HOME.pitch - p0) * k; explode = e0 * (1 - k); applyExplode(); }); });

function size() { const r = stage.getBoundingClientRect(); if (!r.width) return; renderer.setSize(r.width, r.height, false);
  camera.aspect = r.width / r.height; camera.position.z = r.width < 520 ? 15.5 : 12.5; camera.updateProjectionMatrix(); render(); }
function render() { pivot.rotation.set(pitch, yaw, 0, 'XYZ'); renderer.render(scene, camera); }
new ResizeObserver(size).observe(stage); applyExplode(); size();
</script>"""


def engine_html(t, engine_id, stations):
    data = json.dumps({'engine': int(engine_id), 'stations': stations,
                       'theme': {'dark': t['dark'], 'metal': t['metal'], 'bad': t['negative'], 'hue': t['hue'],
                                 'shell': t['shell'], 'neutral': t['neutral'], 'env': t['env'], 'shadow': t['shadow']}})
    body = ENGINE_BODY.replace('__THREE__', THREE_JS).replace('__BEZIER__', BEZIER).replace('__DATA__', data)
    return _frame(t, ENGINE_CSS, body)


# ------------------------------------------------------------------ fleet board
HANGAR_CSS = """
.board{display:grid;grid-template-columns:repeat(10,minmax(0,1fr));gap:6px}
@media (max-width:600px){.board{grid-template-columns:repeat(4,minmax(0,1fr))}}
.t{position:relative;height:54px;border:1px solid var(--border);border-radius:8px;padding:6px 8px;outline:none;background:var(--surface);
  transition:border-color 150ms ease,background-color 150ms ease}
@media (hover:hover) and (pointer:fine){.t:hover{border-color:var(--muted);background:var(--stage)}}
.t:focus-visible{border-color:var(--hue);box-shadow:0 0 0 1px var(--hue)}
.t .n{font-size:12px;color:var(--muted);line-height:14px}
.t .r{font-size:17px;font-weight:500;line-height:22px}
.t .bar{position:absolute;left:8px;right:8px;bottom:6px;height:3px;background:var(--raised);border-radius:2px}
.t .bar i{display:block;height:100%;border-radius:2px}
#tip{position:fixed;left:0;top:0;pointer-events:none;background:var(--surface);border:1px solid var(--control);border-radius:8px;padding:7px 10px;
  font-size:13px;line-height:18px;z-index:9;white-space:nowrap;box-shadow:0 6px 20px var(--tip-shadow);
  opacity:0;transform:scale(0.97);transform-origin:left bottom;transition:opacity 150ms var(--ease-out),transform 150ms var(--ease-out)}
#tip.on{opacity:1;transform:scale(1)}
"""


def hangar_html(t, rows):
    body = """<div class="board" id="b" role="list"></div><div id="tip" role="tooltip"></div>
<script>
const rows = __DATA__, col = __STATUS__, b = document.getElementById('b'), tip = document.getElementById('tip');
rows.forEach(r => {
  const d = document.createElement('div'); d.className = 't'; d.tabIndex = 0; d.setAttribute('role','listitem');
  d.setAttribute('aria-label', `Engine ${r.Engine}, ${r.Status}, ${r.Predicted} cycles predicted, ${r.Actual} actual`);
  d.innerHTML = `<div class="n">Engine ${r.Engine}</div><div class="r">${r.Predicted}</div>
    <div class="bar"><i style="width:${Math.min(r.Predicted,125)/125*100}%;background:${col[r.Status]}"></i></div>`;
  const show = (x,y) => { tip.innerHTML = `<b>Engine ${r.Engine}</b>, ${r.Status.toLowerCase()}<br>Predicted ${r.Predicted} cycles, actual ${r.Actual}`;
    tip.style.left = Math.min(x + 14, innerWidth - tip.offsetWidth - 8) + 'px'; tip.style.top = Math.max(8, y - 54) + 'px'; tip.classList.add('on'); };
  d.addEventListener('mousemove', e => show(e.clientX, e.clientY));
  d.addEventListener('focus', () => { const q = d.getBoundingClientRect(); show(q.right, q.top + 50); });
  ['mouseleave','blur'].forEach(ev => d.addEventListener(ev, () => tip.classList.remove('on')));
  b.appendChild(d);
});
</script>""".replace('__DATA__', json.dumps(rows)).replace('__STATUS__', json.dumps(t['status']))
    return _frame(t, HANGAR_CSS, body)


def styled(t, chart):
    f = 'Geist, Segoe UI, sans-serif'
    return (chart.configure(font=f, background='transparent')
            .configure_axis(labelColor=t['muted'], titleColor=t['muted'], titleFont=f, labelFont=f, titleFontWeight=400,
                            titleFontSize=12, labelFontSize=12, gridColor=t['grid'], domain=False, tickColor=t['grid'])
            .configure_axisX(domain=True, domainColor=t['axis'])
            .configure_legend(labelColor=t['text'], titleColor=t['muted'], labelFontSize=12, labelFont=f, titleFont=f, orient='top')
            .configure_title(font=f, fontSize=14, fontWeight=500, color=t['text'], anchor='start')
            .configure_view(stroke=None))

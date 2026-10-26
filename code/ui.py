"""Visual layer for the Engine Health Monitor: theme CSS, the RUL dial and the hangar board."""
import json

import altair as alt

INK, SLATE, TEAL = '#1B2B3A', '#5D6B78', '#0E7C86'
FUSELAGE, PANEL, RULE = '#E8ECEF', '#F7F9FA', '#CBD3DA'
STATUS = {'Critical': '#C8371D', 'Plan maintenance': '#D99A0B', 'Healthy': '#2E8B57'}

# Fonts ship with the app (code/static/fonts, SIL Open Font License) so it works offline.
FONT_FACES = ''.join(
    f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;"
    f"src:url('/app/static/fonts/{file}-latin-{w}-normal.woff2') format('woff2');}}"
    for fam, file, weights in [('Barlow', 'barlow', (400, 500, 600)),
                               ('Barlow Condensed', 'barlow-condensed', (500, 600, 700))]
    for w in weights)

CSS = f"""
<style>
{FONT_FACES}

:root {{
  --ink: {INK}; --slate: {SLATE}; --teal: {TEAL};
  --fuselage: {FUSELAGE}; --panel: {PANEL}; --rule: {RULE};
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
  font-family: 'Barlow', system-ui, sans-serif;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}}
[data-testid="stAppViewContainer"] :is(p, li, label, input, textarea, td, th, button, div[data-baseweb]) {{
  font-family: 'Barlow', system-ui, sans-serif;
}}
span[data-testid="stIconMaterial"] {{ font-family: 'Material Symbols Rounded' !important; }}

h1, h2, h3, [data-testid="stHeading"] * {{
  font-family: 'Barlow Condensed', 'Barlow', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: 0.005em;
  color: var(--ink);
}}
h2 {{ font-size: 1.85rem !important; }}
h3 {{ font-size: 1.45rem !important; margin-top: .4rem; }}

[data-testid="stAppViewContainer"] {{ background: var(--fuselage); }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.2rem; max-width: 1240px; }}

/* Sidebar reads as the engine-room panel */
[data-testid="stSidebar"] {{ background: var(--ink); }}
[data-testid="stSidebar"] * {{ color: #E4EAEF; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {{ color: #9FB0BE !important; }}
[data-testid="stSidebar"] hr {{ border-color: #33475A; }}
[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {{ background: var(--teal); box-shadow: 0 0 0 4px rgba(14,124,134,.25); }}

/* Tabs: placard style, active tab underlined in teal */
.stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid var(--rule); }}
.stTabs [data-baseweb="tab"] {{
  font-family: 'Barlow Condensed', sans-serif; font-size: 1.15rem; font-weight: 600;
  color: var(--slate); padding: .4rem 0; background: none;
}}
.stTabs [data-baseweb="tab"] p {{ font-family: inherit; font-size: inherit; }}
.stTabs [aria-selected="true"] {{ color: var(--ink); }}
.stTabs [data-baseweb="tab-highlight"] {{ background: var(--teal); height: 3px; }}

/* Readouts */
[data-testid="stMetric"] {{
  background: var(--panel); border: 1px solid var(--rule); border-radius: 6px;
  padding: .7rem 1rem .6rem;
}}
[data-testid="stMetricLabel"] p {{ color: var(--slate); font-size: .9rem; font-weight: 500; }}
[data-testid="stMetricValue"] {{
  font-family: 'Barlow Condensed', sans-serif; font-weight: 600; font-size: 2.3rem; line-height: 1.1;
}}

/* Focus that is easy to see on every control */
:is(button, input, [role="slider"], [role="tab"], [data-baseweb="select"] > div):focus-visible {{
  outline: 3px solid var(--teal) !important; outline-offset: 2px;
}}

/* Header */
.ehm-head {{ display: flex; align-items: center; gap: 1.1rem; margin-bottom: 1.4rem; }}
.ehm-head h1 {{ font-size: 2.6rem !important; line-height: 1; margin: 0; padding: 0; font-weight: 700 !important; }}
.ehm-head p {{ margin: .35rem 0 0; color: var(--slate); font-size: 1.02rem; max-width: 62ch; }}
.ehm-fan {{ width: 64px; height: 64px; flex: none; }}
.ehm-fan .rotor {{
  transform-origin: 50px 50px;
  animation: spinup 2.6s cubic-bezier(.2,.7,.2,1) 1 both, idle 7s linear 2.6s infinite;
}}
@keyframes spinup {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(1080deg); }} }}
@keyframes idle {{ from {{ transform: rotate(1080deg); }} to {{ transform: rotate(1440deg); }} }}

/* Status placard */
.ehm-status {{
  border-radius: 6px; padding: .9rem 1.1rem; border: 1px solid var(--rule);
  background: var(--panel); display: flex; gap: .9rem; align-items: center; margin-bottom: .9rem;
}}
.ehm-status .lamp {{ width: 14px; height: 14px; border-radius: 50%; flex: none; }}
.ehm-status b {{ font-family: 'Barlow Condensed', sans-serif; font-size: 1.5rem; font-weight: 600; display: block; line-height: 1.1; }}
.ehm-status span {{ color: var(--slate); }}
.ehm-status.Critical .lamp {{ animation: blink 1.1s steps(1) 3; }}
@keyframes blink {{ 50% {{ opacity: .15; }} }}

@media (prefers-reduced-motion: reduce) {{
  .ehm-fan .rotor, .ehm-status .lamp {{ animation: none !important; }}
}}
@media (max-width: 640px) {{
  .ehm-head h1 {{ font-size: 2rem !important; }}
  .ehm-fan {{ width: 48px; height: 48px; }}
}}
</style>
"""


def fan_svg():
    blades = ''.join(
        f'<path d="M50 50 C 54 40, 60 22, 52 8 C 47 16, 45 34, 50 50Z" transform="rotate({i * 360 / 14} 50 50)"/>'
        for i in range(14))
    return (f'<svg class="ehm-fan" viewBox="0 0 100 100" aria-hidden="true">'
            f'<circle cx="50" cy="50" r="47" fill="{PANEL}" stroke="{INK}" stroke-width="3"/>'
            f'<g class="rotor" fill="{INK}">{blades}'
            f'<circle cx="50" cy="50" r="9" fill="{TEAL}"/><circle cx="50" cy="50" r="3" fill="{PANEL}"/></g></svg>')


def header_html():
    return (f'<div class="ehm-head">{fan_svg()}<div><h1>Engine Health Monitor</h1>'
            '<p>How many flights each turbofan engine has left before it needs maintenance, '
            'predicted from its sensor history.</p></div></div>')


def status_html(label, advice):
    return (f'<div class="ehm-status {label.split()[0]}" role="status">'
            f'<i class="lamp" style="background:{STATUS[label]}"></i>'
            f'<div><b style="color:{STATUS[label]}">{label}</b><span>{advice}</span></div></div>')


def gauge_html(pred, actual, red, amber, cap=125):
    """Cockpit-style dial. The needle sweeps from full life down to the prediction."""
    cfg = json.dumps({'pred': float(pred), 'actual': float(min(actual, cap)), 'red': red,
                      'amber': amber, 'cap': cap, 'status': STATUS, 'ink': INK, 'teal': TEAL,
                      'slate': SLATE, 'panel': PANEL, 'rule': RULE})
    return f"""
<style>
  {FONT_FACES}
  html,body {{ margin:0; background:transparent; font-family:'Barlow',sans-serif; }}
  svg {{ display:block; width:100%; height:auto; max-width:340px; margin:0 auto; }}
  .num {{ font-family:'Barlow Condensed',sans-serif; font-weight:700; font-variant-numeric:tabular-nums; }}
</style>
<svg id="g" viewBox="0 0 300 304" role="img" aria-label="Predicted remaining life dial"></svg>
<script>
const c = {cfg};
const NS = 'http://www.w3.org/2000/svg', svg = document.getElementById('g');
const cx = 150, cy = 150, R = 118, A0 = -210, A1 = 30;            // 240 degree sweep
const ang = v => A0 + (A1 - A0) * (c.cap - Math.min(Math.max(v,0),c.cap)) / c.cap;  // full life on the left
const pt = (a, r) => [cx + r*Math.cos(a*Math.PI/180), cy + r*Math.sin(a*Math.PI/180)];
const el = (t, a, p=svg) => {{ const e=document.createElementNS(NS,t); for (const k in a) e.setAttribute(k,a[k]); p.appendChild(e); return e; }};
const arc = (v0, v1, r) => {{ const [x0,y0]=pt(ang(v0),r), [x1,y1]=pt(ang(v1),r);
  const large = Math.abs(ang(v1)-ang(v0)) > 180 ? 1 : 0; return `M${{x0}} ${{y0}} A${{r}} ${{r}} 0 ${{large}} 1 ${{x1}} ${{y1}}`; }};

el('circle', {{cx, cy, r:R+16, fill:c.ink}});
el('circle', {{cx, cy, r:R+10, fill:'#24384B'}});
[[c.cap, c.amber, c.status['Healthy']], [c.amber, c.red, c.status['Plan maintenance']], [c.red, 0, c.status['Critical']]]
  .forEach(([a,b,col]) => el('path', {{d:arc(a,b,R-6), stroke:col, 'stroke-width':10, fill:'none', opacity:.9}}));
for (let v=0; v<=c.cap; v+=5) {{
  const major = v % 25 === 0, [x0,y0]=pt(ang(v),R-14), [x1,y1]=pt(ang(v), major?R-30:R-21);
  el('line', {{x1:x0,y1:y0,x2:x1,y2:y1, stroke:'#E4EAEF', 'stroke-width': major?2.4:1.2}});
  if (major) {{ const [tx,ty]=pt(ang(v),R-44); const t=el('text', {{x:tx,y:ty+5,'text-anchor':'middle',fill:'#C9D4DD','font-size':14,class:'num'}}); t.textContent=v; }}
}}
// true answer marker
const [mx,my]=pt(ang(c.actual),R+4), [mx2,my2]=pt(ang(c.actual),R-16);
el('line', {{x1:mx,y1:my,x2:mx2,y2:my2, stroke:'#FFFFFF','stroke-width':3,'stroke-linecap':'round'}});

const label = el('text', {{x:cx,y:cy+52,'text-anchor':'middle',fill:'#9FB0BE','font-size':13}}); label.textContent='cycles left';
const read = el('text', {{x:cx,y:cy+36,'text-anchor':'middle',fill:'#FFFFFF','font-size':44,class:'num'}});
const needle = el('g', {{}});
el('path', {{d:`M${{cx-5}} ${{cy}} L${{cx}} ${{cy-R+20}} L${{cx+5}} ${{cy}} Z`, fill:c.teal}}, needle);
el('circle', {{cx, cy, r:11, fill:c.teal}}, needle); el('circle', {{cx, cy, r:4, fill:c.ink}}, needle);
const key = el('text', {{x:cx,y:298,'text-anchor':'middle',fill:c.slate,'font-size':12.5}});
key.textContent = 'Teal needle: prediction.  White mark: actual.';

const set = v => {{ needle.setAttribute('transform', `rotate(${{ang(v)+90}} ${{cx}} ${{cy}})`); read.textContent = Math.round(v); }};
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reduce) set(c.pred); else {{
  const t0 = performance.now(), D = 1400, from = c.cap;
  const ease = t => 1 - Math.pow(1 - t, 3) * Math.cos(t * 9) ;  // settles with a slight overshoot like a real needle
  (function step(now) {{ const t=Math.min((now-t0)/D,1), k = t<1 ? ease(t) : 1;
    set(from + (c.pred - from) * k); if (t<1) requestAnimationFrame(step); }})(t0);
}}
</script>"""


def hangar_html(rows):
    """Board of every test engine, most urgent first. rows: list of dicts with Engine, Predicted, Actual, Status."""
    data = json.dumps(rows)
    return f"""
<style>
  {FONT_FACES}
  html,body {{ margin:0; font-family:'Barlow',sans-serif; color:{INK}; background:transparent; }}
  .board {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(54px,1fr)); gap:6px; }}
  .t {{ position:relative; height:62px; border-radius:5px; background:{PANEL}; border:1px solid {RULE};
        overflow:hidden; cursor:default; outline:none; transition:transform .12s ease, box-shadow .12s ease; }}
  .t .fill {{ position:absolute; left:0; right:0; bottom:0; opacity:.9; }}
  .t .n {{ position:absolute; top:4px; left:6px; font-family:'Barlow Condensed',sans-serif; font-weight:600; font-size:15px; }}
  .t .r {{ position:absolute; bottom:3px; right:6px; font-family:'Barlow Condensed',sans-serif; font-weight:700;
           font-size:17px; color:{INK}; font-variant-numeric:tabular-nums; }}
  .t.tall .r {{ color:#fff; }}
  .t.full .n {{ color:#fff; }}
  .t:hover, .t:focus-visible {{ transform:translateY(-2px); box-shadow:0 0 0 2px {TEAL}; }}
  .t.on {{ animation:lamp .5s ease-out both; }}
  @keyframes lamp {{ from {{ opacity:.15; }} to {{ opacity:1; }} }}
  #tip {{ position:fixed; pointer-events:none; background:{INK}; color:#fff; padding:7px 10px; border-radius:5px;
          font-size:13.5px; line-height:1.35; opacity:0; transition:opacity .1s; z-index:9; white-space:nowrap; }}
  #tip b {{ font-family:'Barlow Condensed',sans-serif; font-size:16px; font-weight:600; }}
  @media (prefers-reduced-motion: reduce) {{ .t.on {{ animation:none; }} .t {{ transition:none; }} }}
</style>
<div class="board" id="b" role="list"></div><div id="tip" role="tooltip"></div>
<script>
const rows = {data}, col = {json.dumps(STATUS)}, b = document.getElementById('b'), tip = document.getElementById('tip');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
rows.forEach((r,i) => {{
  const d = document.createElement('div'); const hh = Math.min(r.Predicted,125)/125*100; d.className='t' + (hh>=30?' tall':'') + (hh>=66?' full':''); d.tabIndex=0; d.setAttribute('role','listitem');
  d.setAttribute('aria-label', `Engine ${{r.Engine}}, ${{r.Status}}, ${{r.Predicted}} cycles predicted, ${{r.Actual}} actual`);
  const h = Math.max(8, Math.min(r.Predicted,125)/125*100);
  d.innerHTML = `<div class="fill" style="height:${{h}}%;background:${{col[r.Status]}}"></div><span class="n">${{r.Engine}}</span><span class="r">${{r.Predicted}}</span>`;
  if (!reduce) {{ d.classList.add('on'); d.style.animationDelay = (i*6)+'ms'; }}
  const show = (x,y) => {{ tip.innerHTML = `<b>Engine ${{r.Engine}}</b><br>${{r.Status}}<br>Predicted ${{r.Predicted}} · actual ${{r.Actual}} cycles`;
    tip.style.left = Math.min(x+14, innerWidth-tip.offsetWidth-8)+'px'; tip.style.top = Math.max(8,y-70)+'px'; tip.style.opacity=1; }};
  d.addEventListener('mousemove', e => show(e.clientX, e.clientY));
  d.addEventListener('focus', () => {{ const q=d.getBoundingClientRect(); show(q.right, q.top+60); }});
  ['mouseleave','blur'].forEach(ev => d.addEventListener(ev, () => tip.style.opacity=0));
  b.appendChild(d);
}});
</script>"""


def styled(chart):
    return (chart.configure(font='Barlow, sans-serif')
            .configure_axis(labelColor=SLATE, titleColor=INK, titleFont='Barlow, sans-serif', titleFontWeight=500,
                            titleFontSize=13, labelFontSize=12, gridColor='#DCE2E7', domainColor=RULE, tickColor=RULE)
            .configure_legend(labelColor=INK, titleColor=SLATE, labelFontSize=13)
            .configure_title(font='Barlow Condensed, Barlow, sans-serif', fontSize=17, fontWeight=600, color=INK, anchor='start')
            .configure_view(stroke=None))

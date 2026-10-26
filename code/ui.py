"""Visual layer for EnginePulse.

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
        metal='#aeb5bd', shell='#dfe3e8', neutral='#c9ced4', env=0.55, shadow=0.16, tip_shadow='rgba(0,0,0,.08)',
        band='#0f1b26', band_text='#ffffff', band_muted='#b4bfca', plate='#0a1119', plate_ring='#22303d'),
    'Graphite': dict(
        dark=True, ground='#141414', surface='#1b1b1b', stage='#202020', raised='#242424', border='#2c2c2c',
        rule='#252525', control='#3d3d3d', text='#f4f4f4', muted='#a8a8a8', hue='#6ea1f7', comp='#8c8c8c',
        grid='#2a2a2a', axis='#5c5c5c', primary_bg='#f4f4f4', primary_ink='#111111', primary_hover='#ffffff',
        negative='#f0616d', status=_STATUS_DARK,
        pill={'Critical': ('#2c1a1d', '#f08a96'), 'Plan maintenance': ('#2a2112', '#e9b45a'), 'Healthy': ('#172a1d', '#4fd18b')},
        metal='#8d949c', shell='#3a3e43', neutral='#5b6067', env=0.8, shadow=0.45, tip_shadow='rgba(0,0,0,.4)',
        band='#1f1f1f', band_text='#ffffff', band_muted='#b0b0b0', plate='#0e0e0e', plate_ring='#333333'),
    'Black': dict(
        dark=True, ground='#000000', surface='#0e0e0e', stage='#121212', raised='#181818', border='#1f1f1f',
        rule='#181818', control='#3a3a3a', text='#ffffff', muted='#a3a3a3', hue='#6ea1f7', comp='#8a8a8a',
        grid='#1f1f1f', axis='#4c4c4c', primary_bg='#ffffff', primary_ink='#000000', primary_hover='#e6e6e6',
        negative='#f0616d', status=_STATUS_DARK,
        pill={'Critical': ('#2c1a1d', '#f08a96'), 'Plan maintenance': ('#2a2112', '#e9b45a'), 'Healthy': ('#172a1d', '#4fd18b')},
        metal='#8d949c', shell='#2f3236', neutral='#55595f', env=0.9, shadow=0.6, tip_shadow='rgba(0,0,0,.5)',
        band='#111111', band_text='#ffffff', band_muted='#a8a8a8', plate='#000000', plate_ring='#2a2a2a'),
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
    for w, style, name in [(400, 'normal', 'normal'), (500, 'normal', 'normal'), (400, 'italic', 'italic')]:
        data = _read(f'fonts/playfair-display-latin-{w}-{name}.woff2')
        if data:
            out.append("@font-face{font-family:'Playfair Display';font-style:%s;font-weight:%d;font-display:swap;"
                       "src:url(data:font/woff2;base64,%s) format('woff2');}" % (style, w, base64.b64encode(data).decode()))
    return ''.join(out)


FONT_FACES = _faces()
SERIF = "'Playfair Display', Georgia, serif"
THREE_JS = _read('vendor/three.min.js', 'r')
FONT_STACK = "'Geist', 'Segoe UI', system-ui, sans-serif"
EASE_OUT, EASE_IN_OUT = 'cubic-bezier(0.23, 1, 0.32, 1)', 'cubic-bezier(0.77, 0, 0.175, 1)'


def _vars(t):
    keys = ['ground', 'surface', 'stage', 'raised', 'border', 'rule', 'control', 'text', 'muted', 'hue',
            'primary_bg', 'primary_ink', 'primary_hover', 'negative', 'tip_shadow', 'band', 'band_text', 'band_muted',
            'plate', 'plate_ring']
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
:is(.ehm-hero-text h1, .ehm-section h2, .ehm-features h3, .ehm-features .fig, [class*="st-key-card-"] h3, .st-key-nav .ehm-mark b, .ehm-hero-text .kicker span:last-child), :is(.ehm-hero-text h1, .ehm-section h2, .ehm-features h3, [class*="st-key-card-"] h3) * { font-family: 'Playfair Display', Georgia, serif !important; }
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


/* Title card */
.ehm-hero { margin: 0 0 14px; }
.ehm-hero .top { display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; }
.ehm-hero h1 { margin: 0; }
.ehm-hero p.lede { margin: 6px 0 0; color: var(--muted); font-size: 15px; line-height: 22px; max-width: 70ch; }
.ehm-hero .meta { text-align: right; font-size: 12px; line-height: 18px; color: var(--muted); white-space: nowrap; padding-top: 4px; }
.ehm-hbar { display: flex; gap: 2px; height: 10px; margin: 6px 0 14px; border-radius: 5px; overflow: hidden; background: var(--raised); }
.ehm-hbar i { display: block; height: 100%; transition: opacity 150ms ease; }
.ehm-hlegend { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.ehm-hlegend div { transition: opacity 150ms ease; }
.ehm-hlegend b { display: block; font-size: 24px; line-height: 30px; font-weight: 500; color: var(--text); letter-spacing: -0.01em; }
.ehm-hlegend span { display: block; font-size: 13px; color: var(--text); }
.ehm-hlegend span::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 7px;
  background: var(--dot); vertical-align: 1px; }
.ehm-hlegend em { display: block; font-style: normal; font-size: 12px; color: var(--muted); margin-top: 1px; }
@media (hover: hover) and (pointer: fine) {
  .ehm-health:has(.ehm-hbar i:hover) .ehm-hbar i:not(:hover) { opacity: .35; }
  .ehm-health:has(.ehm-hlegend div:hover) .ehm-hlegend div:not(:hover) { opacity: .45; }
  .ehm-health:has(.ehm-hlegend div:nth-child(1):hover) .ehm-hbar i:not(:nth-child(1)),
  .ehm-health:has(.ehm-hlegend div:nth-child(2):hover) .ehm-hbar i:not(:nth-child(2)),
  .ehm-health:has(.ehm-hlegend div:nth-child(3):hover) .ehm-hbar i:not(:nth-child(3)),
  .ehm-health:has(.ehm-hbar i:nth-child(1):hover) .ehm-hlegend div:not(:nth-child(1)),
  .ehm-health:has(.ehm-hbar i:nth-child(2):hover) .ehm-hlegend div:not(:nth-child(2)),
  .ehm-health:has(.ehm-hbar i:nth-child(3):hover) .ehm-hlegend div:not(:nth-child(3)) { opacity: .35; }
}
.ehm-health { margin-bottom: 18px; }
.st-key-card-summary .ehm-sum { margin-top: 4px; }

/* Sidebar: grouped, collapsible sections */
[data-testid="stSidebar"] > div:first-child { padding-top: 6px; }
[data-testid="stSidebarUserContent"] { padding: 0 20px 28px; }
[data-testid="stSidebar"] .ehm-mark { padding: 4px 0 18px; margin: 0; border-bottom: 1px solid var(--border); }
[data-testid="stSidebar"] [data-testid="stExpander"] details { border: 0 !important; border-bottom: 1px solid var(--border) !important;
  border-radius: 0 !important; background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { padding: 16px 0 !important; background: transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary p { font-size: 13px; font-weight: 600; color: var(--text); }
[data-testid="stSidebar"] [data-testid="stExpander"] summary svg { color: var(--muted); transition: transform 200ms var(--ease-out); }
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] { padding: 0 0 18px !important; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size: 12px; font-weight: 500; color: var(--muted); }
[data-testid="stSidebar"] { min-width: 300px !important; max-width: 300px !important; }
[data-testid="stSidebar"] .react-aria-ComboBox > [role="group"] { background: var(--surface) !important; border: 1px solid var(--control) !important;
  border-radius: 8px !important; min-height: 38px; transition: border-color 150ms ease; box-shadow: none !important; }
[data-testid="stSidebar"] .react-aria-ComboBox > [role="group"]:focus-within { border-color: var(--text) !important; }
[data-testid="stSidebar"] .react-aria-ComboBox input { font-size: 14px; color: var(--text); background: transparent !important; cursor: pointer; }
[data-testid="stSidebar"] .react-aria-ComboBox button svg { color: var(--muted); transition: transform 200ms var(--ease-out); }
[data-testid="stSidebar"] .react-aria-ComboBox button[aria-expanded="true"] svg { transform: rotate(180deg); }
@media (hover: hover) and (pointer: fine) {
  [data-testid="stSidebar"] .react-aria-ComboBox > [role="group"]:hover { border-color: var(--muted) !important; }
}
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] { border: 0 !important; }
[data-testid="stSidebar"] .stButtonGroup > div { flex-wrap: nowrap !important; background: var(--raised); border-radius: 9px;
  padding: 3px; gap: 2px; width: 100%; }
[data-testid="stSidebar"] .stButtonGroup button[role="radio"] { flex: 1 1 0; min-width: 0; border: 0 !important; border-radius: 7px !important;
  background: transparent !important; min-height: 30px; padding: 0 6px;
  transition: transform 160ms var(--ease-out), background-color 150ms ease, box-shadow 150ms ease; }
[data-testid="stSidebar"] .stButtonGroup button[role="radio"]:active { transform: scale(0.97); }
[data-testid="stSidebar"] .stButtonGroup button[role="radio"] p { font-size: 13px; color: var(--muted); }
[data-testid="stSidebar"] .stButtonGroup button[aria-checked="true"] { background: var(--surface) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.14), 0 0 0 1px var(--border); }
[data-testid="stSidebar"] .stButtonGroup button[aria-checked="true"] p { color: var(--text); font-weight: 500; }
[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] { width: 16px; height: 16px; background: var(--surface);
  border: 2px solid var(--text); box-shadow: none; transition: transform 160ms var(--ease-out); }
[data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"]:active { transform: scale(1.12); }
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"] p, [data-testid="stSidebar"] [data-testid="stSliderThumbValue"] {
  font-size: 12px; color: var(--text); font-weight: 500; font-family: inherit; }
[data-testid="stSidebar"] [data-testid="stSliderTickBar"] { display: none; }
[data-testid="stSidebar"] p.ehm-side-note { margin: 0 0 8px; }

/* Plain-words summary */
[data-testid="stMarkdownContainer"] table.ehm-sum, [data-testid="stMarkdownContainer"] table.ehm-sum :is(tr, th, td) {
  border-left: 0 !important; border-right: 0 !important; border-bottom: 0 !important; background: transparent; }
[data-testid="stMarkdownContainer"] table.ehm-sum { border: 0 !important; margin: 0; }
[data-testid="stMarkdownContainer"] table.ehm-sum thead th { border-top: 0 !important; }
.ehm-sum { width: 100%; border-collapse: collapse; font-size: 14px; line-height: 21px; }
.ehm-sum th { font-weight: 400; font-size: 12px; color: var(--muted); text-align: left; padding: 4px 20px 8px 0; }
.ehm-sum td { padding: 12px 20px 12px 0; border-top: 1px solid var(--rule); vertical-align: top; }
.ehm-sum td.q { color: var(--muted); width: 24%; }
.ehm-sum td.a { color: var(--text); width: 46%; }
.ehm-sum td.n { color: var(--muted); font-size: 13px; padding-right: 0; }
.ehm-sum tr { transition: background-color 150ms ease; }
@media (hover: hover) and (pointer: fine) { .ehm-sum tbody tr:hover { background: var(--stage); } }
/* ---------- Layout after the reference: top bar, dark band, serif sections ---------- */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stHeader"] { display: none !important; }
[data-testid="stMain"] { overflow-x: hidden; }
.block-container { padding: 0 2.5rem 5rem !important; max-width: 1240px; }

/* top bar */
.st-key-nav { position: sticky; top: 0; z-index: 50; background: var(--ground); padding: 14px 0 12px;
  border-bottom: 1px solid var(--border); margin-bottom: 0; }
.st-key-nav [data-testid="stHorizontalBlock"] { align-items: center; gap: 12px; }
.st-key-nav .ehm-mark { margin: 0; white-space: nowrap; }
.st-key-nav .ehm-mark span { display: none; }
.st-key-nav .ehm-mark b { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 500; letter-spacing: 0; }
.st-key-nav .stButtonGroup > div { justify-content: center; gap: 28px; flex-wrap: nowrap !important; }
.st-key-nav .stButtonGroup button[role="radio"] { border: 0 !important; background: transparent !important; padding: 6px 0;
  min-height: 32px; border-radius: 0 !important; box-shadow: none !important; transition: box-shadow 200ms var(--ease-out); }
.st-key-nav .stButtonGroup button[role="radio"] p { font-size: 14px; color: var(--muted); font-weight: 500; transition: color 150ms ease; }
.st-key-nav .stButtonGroup button[aria-checked="true"] { box-shadow: inset 0 -2px 0 var(--text) !important; }
.st-key-nav .stButtonGroup button[aria-checked="true"] p { color: var(--text); }
@media (hover: hover) and (pointer: fine) { .st-key-nav .stButtonGroup button[role="radio"]:hover p { color: var(--text); } }
.st-key-nav .react-aria-ComboBox > [role="group"], .st-key-nav [data-testid="stPopover"] button {
  background: var(--surface) !important; border: 1px solid var(--control) !important; border-radius: 8px !important;
  min-height: 36px; box-shadow: none !important; transition: border-color 150ms ease, transform 160ms var(--ease-out); }
.st-key-nav .react-aria-ComboBox input { font-size: 13px; color: var(--text); cursor: pointer; }
.st-key-nav [data-testid="stPopover"] button:active { transform: scale(0.97); }
@media (hover: hover) and (pointer: fine) {
  .st-key-nav .react-aria-ComboBox > [role="group"]:hover, .st-key-nav [data-testid="stPopover"] button:hover { border-color: var(--muted) !important; }
}
[data-testid="stPopoverBody"] { border-radius: 12px !important; border: 1px solid var(--border) !important; min-width: 300px;
  box-shadow: 0 16px 40px var(--tip-shadow) !important; }
[data-testid="stPopoverBody"] [data-testid="stWidgetLabel"] p { font-size: 12px; font-weight: 500; color: var(--muted); }
[data-testid="stPopoverBody"] .stButtonGroup > div { flex-wrap: nowrap !important; background: var(--raised); border-radius: 9px; padding: 3px; gap: 2px; }
[data-testid="stPopoverBody"] .stButtonGroup button[role="radio"] { flex: 1 1 0; border: 0 !important; border-radius: 7px !important;
  background: transparent !important; min-height: 30px; transition: transform 160ms var(--ease-out), background-color 150ms ease; }
[data-testid="stPopoverBody"] .stButtonGroup button[role="radio"]:active { transform: scale(0.97); }
[data-testid="stPopoverBody"] .stButtonGroup button[aria-checked="true"] { background: var(--surface) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,.14), 0 0 0 1px var(--border); }
[data-testid="stPopoverBody"] .stButtonGroup button p { font-size: 13px; }
[data-testid="stPopoverBody"] [role="slider"] { background: var(--surface) !important; border: 2px solid var(--text); width: 16px; height: 16px; }
[data-testid="stPopoverBody"] [data-testid="stSliderTickBar"] { display: none; }

/* full-width dark band */
.st-key-hero, .st-key-band { position: relative; width: 100vw !important; max-width: 100vw !important; left: 50%; margin-left: -50vw !important; background: var(--band);
  padding: 0 max(2.5rem, calc((100vw - 1240px) / 2 + 2.5rem)); }
.st-key-hero { margin-top: 76px !important; margin-bottom: 104px !important; }
.st-key-band { margin-top: 0; margin-bottom: 40px; padding-top: 56px; padding-bottom: 56px; }
.st-key-hero [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-hero [data-testid="stColumn"]:first-child [data-testid="stElementContainer"]:has(iframe) { margin: -72px 0 -92px !important; }
.ehm-hero-text { color: var(--band-text); max-width: 34rem; }
.ehm-hero-text .kicker { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
.ehm-hero-text .kicker span:last-child { font-family: 'Playfair Display', Georgia, serif; font-style: italic; font-size: 18px; color: var(--band-muted); }
.ehm-hero-text h1 { font-family: 'Playfair Display', Georgia, serif !important; font-weight: 400 !important; font-size: 46px !important; line-height: 1.08 !important;
  letter-spacing: -0.01em; color: var(--band-text) !important; margin: 0 !important; padding: 0 !important; }
.ehm-hero-text p { color: var(--band-muted); font-size: 15px; line-height: 24px; margin: 18px 0 0; max-width: 32rem; }
.st-key-hero .stDownloadButton button, .st-key-band .stDownloadButton button { background: transparent !important; border: 1px solid var(--band-text) !important;
  border-radius: 2px !important; min-height: 44px; padding: 0 22px; }
.st-key-hero .stDownloadButton button p { color: var(--band-text) !important; font-size: 13px; font-weight: 500; letter-spacing: 0.02em; }
@media (hover: hover) and (pointer: fine) {
  .st-key-hero .stDownloadButton button:hover { background: var(--band-text) !important; }
  .st-key-hero .stDownloadButton button:hover p { color: var(--band) !important; }
}
.st-key-hero .stDownloadButton { margin-top: 10px; }

/* serif sections */
.ehm-section { text-align: center; margin: 24px auto 40px; max-width: 40rem; }
.ehm-section h2 { font-family: 'Playfair Display', Georgia, serif !important; font-weight: 400 !important; font-size: 36px !important; line-height: 1.15 !important;
  letter-spacing: -0.01em; margin: 0 !important; padding: 0 !important; }
.ehm-section p { color: var(--muted); font-size: 15px; line-height: 23px; margin: 12px 0 0; }
.ehm-features { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 56px; margin: 0 0 64px; }
.ehm-features h3 { font-family: 'Playfair Display', Georgia, serif !important; font-weight: 400 !important; font-size: 21px !important; margin: 14px 0 8px !important; padding: 0 !important; }
.ehm-features p { color: var(--muted); font-size: 14px; line-height: 22px; margin: 0; }
.ehm-features .fig { display: block; font-family: 'Playfair Display', Georgia, serif; font-weight: 400; font-size: 44px; line-height: 1; margin-top: 18px; color: var(--text); }
.ehm-icon { width: 56px; height: 56px; fill: none; stroke: var(--text); stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
.ehm-icon .a { fill: var(--accent); stroke: none; }
.ehm-gap { height: 72px; }
[class*="st-key-card-"] h3 { font-family: 'Playfair Display', Georgia, serif !important; font-weight: 400 !important; font-size: 20px !important; }
.ehm-stations td small { display: block; color: var(--muted); font-size: 12px; margin-top: 2px; }
.ehm-stations .n { text-align: right; } .ehm-stations th.n { text-align: right; }
.ehm-stations .sw { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin-right: 8px; }

@media (max-width: 900px) {
  .block-container { padding: 0 1rem 4rem !important; }
  .st-key-hero, .st-key-band { padding: 0 1.25rem; }
  .st-key-band { padding-top: 40px; padding-bottom: 40px; }
  .st-key-hero { margin-top: 40px; padding-bottom: 40px; margin-bottom: 64px; }
  .st-key-hero [data-testid="stColumn"]:first-child [data-testid="stElementContainer"]:has(iframe) { margin: -32px 0 0; }
  .ehm-hero-text h1 { font-size: 34px !important; }
  .ehm-section h2 { font-size: 28px !important; }
  .ehm-features { grid-template-columns: 1fr; gap: 36px; }
  .st-key-nav .stButtonGroup > div { justify-content: flex-start; gap: 18px; overflow-x: auto; }
}

/* ---------- EnginePulse: depth and polished metal ---------- */
.ep-logo { height: 44px !important; width: 173px !important; max-width: none !important; display: block; }
.st-key-nav [data-testid="stMarkdownContainer"]:has(.ep-logo) { overflow: visible; }
.st-key-nav { width: 100vw !important; max-width: 100vw !important; margin-left: calc(50% - 50vw) !important;
  padding: 14px max(2.5rem, calc((100vw - 1240px) / 2 + 2.5rem)) !important; border-bottom: 0 !important;
  background: __NAV__; box-shadow: inset 0 1px 0 __HI__, inset 0 -1px 0 __LO__, 0 10px 24px __DROP__; }
.st-key-nav .stButtonGroup button[aria-checked="true"] { box-shadow: inset 0 -2px 0 __RULE__ !important; }

/* bevelled controls in the bar */
.st-key-nav .react-aria-ComboBox > [role="group"], .st-key-nav [data-testid="stPopover"] button {
  background: __BTN2__ !important; border: 1px solid __BTN2_EDGE__ !important;
  box-shadow: inset 0 1px 0 __BTN2_HI__, 0 2px 6px __BTN2_DROP__ !important; }
.st-key-nav .react-aria-ComboBox input, .st-key-nav [data-testid="stPopover"] button p { color: var(--text) !important; }

/* the primary: polished chrome with a light sweep on hover */
.st-key-hero .stDownloadButton button, .stDownloadButton button[kind="primary"] {
  position: relative; overflow: hidden; border-radius: 12px !important; min-height: 48px; padding: 0 26px;
  border: 1px solid #0b0c0e !important;
  background: linear-gradient(180deg, #ffffff 0%, #e4e7eb 42%, #aeb4bd 56%, #eef0f3 100%) !important;
  box-shadow: inset 0 1px 0 #ffffff, inset 0 -2px 3px rgba(0,0,0,.18), 0 8px 18px rgba(0,0,0,.35) !important; }
.st-key-hero .stDownloadButton button p, .stDownloadButton button[kind="primary"] p {
  color: #15181c !important; font-weight: 600 !important; letter-spacing: .02em; }
.st-key-hero .stDownloadButton button::after, .stDownloadButton button[kind="primary"]::after {
  content: ""; position: absolute; inset: -2px; pointer-events: none;
  background: linear-gradient(110deg, transparent 35%, rgba(255,255,255,.85) 50%, transparent 65%);
  transform: translateX(-120%); transition: transform 750ms var(--ease-out); }
@media (hover: hover) and (pointer: fine) {
  .st-key-hero .stDownloadButton button:hover, .stDownloadButton button[kind="primary"]:hover {
    background: linear-gradient(180deg, #ffffff 0%, #eceef1 42%, #b9bfc7 56%, #f4f5f7 100%) !important; }
  .st-key-hero .stDownloadButton button:hover::after, .stDownloadButton button[kind="primary"]:hover::after { transform: translateX(120%); }
  .st-key-hero .stDownloadButton button:hover p { color: #15181c !important; }
}
.st-key-hero .stDownloadButton button:active { transform: scale(0.97); box-shadow: inset 0 1px 0 #fff, 0 3px 8px rgba(0,0,0,.35) !important; }

/* secondary buttons: a quieter bevel */
.stDownloadButton button:not([kind="primary"]), .stButton button { background: __BTN2__ !important; border: 1px solid __BTN2_EDGE__ !important;
  box-shadow: inset 0 1px 0 __BTN2_HI__, 0 2px 6px __BTN2_DROP__ !important; }
.st-key-hero .stDownloadButton button:not([kind="primary"]) { background: linear-gradient(180deg, #ffffff 0%, #e4e7eb 42%, #aeb4bd 56%, #eef0f3 100%) !important;
  border: 1px solid #0b0c0e !important; box-shadow: inset 0 1px 0 #ffffff, inset 0 -2px 3px rgba(0,0,0,.18), 0 8px 18px rgba(0,0,0,.35) !important; }

/* cards with real elevation and a lit top edge */
[class*="st-key-card-"] { background: __CARD__ !important;
  box-shadow: inset 0 1px 0 __CARD_HI__, 0 1px 2px __CARD_DROP1__, 0 14px 30px __CARD_DROP2__; }

/* the band: a lit top edge, a shadowed bottom */
.st-key-hero, .st-key-band { box-shadow: inset 0 1px 0 rgba(255,255,255,.07), inset 0 -1px 0 rgba(0,0,0,.5); }

/* polished type: chrome on the dark band, steel on the page */
.ehm-hero-text h1, .ehm-hero-text h1 * {
  background: linear-gradient(180deg, #ffffff 0%, #eef0f3 40%, #a9b0b9 60%, #f3f5f7 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent !important; -webkit-text-fill-color: transparent; }
.ehm-features .fig { background: __FIG__; -webkit-background-clip: text; background-clip: text; color: transparent;
  -webkit-text-fill-color: transparent; }
.ehm-pill { box-shadow: inset 0 1px 0 rgba(255,255,255,.35); }
@media (prefers-reduced-motion: reduce) {
  .st-key-hero .stDownloadButton button::after, .stDownloadButton button[kind="primary"]::after { display: none; }
}
@media (max-width: 640px) {
  .block-container { padding: 4.2rem 1rem 3rem; }
  .ehm-kpis { grid-auto-flow: row; grid-template-columns: 1fr 1fr; }
  .ehm-kpis > div { border-left: 0; border-top: 1px solid var(--border); }
  .ehm-kpis > div:nth-child(-n+2) { border-top: 0; }
  .ehm-kpis > div:nth-child(even) { border-left: 1px solid var(--border); }
  .ehm-kpis > div:last-child:nth-child(odd) { grid-column: 1 / -1; }
  .ehm-hero .top { flex-direction: column; gap: 8px; } .ehm-hero .meta { text-align: left; }
  .ehm-hlegend { grid-template-columns: 1fr; gap: 10px; }
  .ehm-sum thead { display: none; } .ehm-sum tr { display: block; border-top: 1px solid var(--rule); padding: 10px 0; }
  .ehm-sum td { display: block; border: 0; padding: 2px 0; width: auto !important; }
}
</style>
"""
    m = METAL[t['dark']] if t['dark'] else METAL['light']
    if t['dark'] and t['ground'] == '#000000':
        m = METAL['black']
    for k, v in m.items():
        s = s.replace(f'__{k}__', v)
    return s.replace('__FACES__', FONT_FACES).replace('__VARS__', _vars(t)).replace('__STACK__', FONT_STACK)


METAL = {
    'light': dict(NAV='linear-gradient(180deg, #ffffff 0%, #f1f3f5 46%, #e3e7eb 54%, #f5f6f8 100%)', HI='#ffffff',
                  LO='rgba(0,0,0,.10)', DROP='rgba(15,27,38,.10)', RULE='#0a0a0a',
                  BTN2='linear-gradient(180deg, #ffffff 0%, #f3f4f6 100%)', BTN2_EDGE='#c9ced5', BTN2_HI='#ffffff',
                  BTN2_DROP='rgba(0,0,0,.08)', CARD='linear-gradient(180deg, #ffffff 0%, #fbfcfd 100%)', CARD_HI='#ffffff',
                  CARD_DROP1='rgba(15,27,38,.06)', CARD_DROP2='rgba(15,27,38,.07)',
                  FIG='linear-gradient(180deg, #59616b 0%, #1d2228 45%, #0b0d10 55%, #4a525c 100%)'),
    True: dict(NAV='linear-gradient(180deg, #3a3f46 0%, #24282d 48%, #1b1e22 52%, #2a2e34 100%)', HI='rgba(255,255,255,.22)',
               LO='rgba(0,0,0,.6)', DROP='rgba(0,0,0,.45)', RULE='#d9dde3',
               BTN2='linear-gradient(180deg, #33373d 0%, #1f2226 100%)', BTN2_EDGE='#0b0c0e', BTN2_HI='rgba(255,255,255,.14)',
               BTN2_DROP='rgba(0,0,0,.45)', CARD='linear-gradient(180deg, #212327 0%, #1a1b1e 100%)', CARD_HI='rgba(255,255,255,.07)',
               CARD_DROP1='rgba(0,0,0,.4)', CARD_DROP2='rgba(0,0,0,.35)',
               FIG='linear-gradient(180deg, #ffffff 0%, #e9ecf0 42%, #9aa1aa 58%, #eef0f3 100%)'),
    'black': dict(NAV='linear-gradient(180deg, #2c3036 0%, #16181b 48%, #0d0e10 52%, #1c1f23 100%)', HI='rgba(255,255,255,.18)',
                  LO='rgba(0,0,0,.8)', DROP='rgba(0,0,0,.6)', RULE='#d9dde3',
                  BTN2='linear-gradient(180deg, #2a2d32 0%, #141618 100%)', BTN2_EDGE='#000000', BTN2_HI='rgba(255,255,255,.12)',
                  BTN2_DROP='rgba(0,0,0,.6)', CARD='linear-gradient(180deg, #151618 0%, #0e0e0f 100%)', CARD_HI='rgba(255,255,255,.06)',
                  CARD_DROP1='rgba(0,0,0,.6)', CARD_DROP2='rgba(0,0,0,.5)',
                  FIG='linear-gradient(180deg, #ffffff 0%, #e9ecf0 42%, #9aa1aa 58%, #eef0f3 100%)'),
}


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


NAV_LOGO = {False: _read('brand/nav_steel.svg', 'r'), True: _read('brand/nav_chrome.svg', 'r')}


def mark_html(t, fleet):
    return f'<div class="ehm-mark">{NAV_LOGO[t["dark"]]}</div>'


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


def page_header(title, sentence, meta):
    m = '<br>'.join(meta)
    return (f'<div class="ehm-hero"><div class="top"><div><h1>{title}</h1><p class="lede">{sentence}</p></div>'
            f'<div class="meta">{m}</div></div></div>')


def health_bar(t, segments, legend=True):
    """segments: (status, count, plain action, threshold words)."""
    total = sum(c for _, c, _, _ in segments) or 1
    bar = ''.join(f'<i style="width:{c / total * 100:.3f}%;background:{t["status"][k]}" title="{c} {k.lower()}"></i>'
                  for k, c, _, _ in segments if c)
    legend_html = ''.join(f'<div style="--dot:{t["status"][k]}"><b>{c}</b><span>{k}: {action}</span><em>{words}</em></div>'
                     for k, c, action, words in segments)
    return ('<div class="ehm-health"><div class="ehm-hbar" role="img" aria-label="'
            + ', '.join(f'{c} {k.lower()}' for k, c, _, _ in segments)
            + f'">{bar}</div>' + (f'<div class="ehm-hlegend">{legend_html}</div>' if legend else '') + '</div>')


def summary_table(rows):
    body = ''.join(f'<tr><td class="q">{q}</td><td class="a">{a}</td><td class="n">{n}</td></tr>' for q, a, n in rows)
    return ('<table class="ehm-sum"><thead><tr><th>Question</th><th>In plain words</th><th>The numbers behind it</th>'
            f'</tr></thead><tbody>{body}</tbody></table>')


ICONS = {
    'gauge': '<path d="M10 38a18 18 0 1 1 36 0" /><path d="M14 38h4M38 38h4M28 20v4M17 26l3 3M39 26l-3 3"/>'
             '<path d="M28 38l9-10"/><circle cx="28" cy="38" r="3.2" class="a"/>',
    'turbine': '<circle cx="28" cy="28" r="18"/>' + ''.join(
        f'<path d="M28 28c2-5 3-10 1-15" transform="rotate({i * 45} 28 28)"/>' for i in range(8))
               + '<circle cx="28" cy="28" r="4.5" class="a"/>',
    'focus': '<path d="M10 44h36"/><path d="M14 44v-3M19 44v-3M24 44v-4M29 44v-5M34 44v-8"/>'
             '<rect x="38" y="16" width="5" height="28" rx="1" class="a"/>',
    'stop': '<path d="M21 10h14l10 10v14L35 44H21L11 34V20z"/><path d="M28 19v12"/><circle cx="28" cy="37" r="2" class="a"/>',
    'calendar': '<rect x="11" y="14" width="34" height="30" rx="3"/><path d="M11 22h34M20 10v7M36 10v7"/>'
                '<rect x="30" y="31" width="8" height="7" rx="1" class="a"/>',
    'plane': '<path d="M28 9c2 0 3 2 3 5v9l14 8v4l-14-4v8l5 4v3l-8-2-8 2v-3l5-4v-8l-14 4v-4l14-8v-9c0-3 1-5 3-5z" class="a"/>',
}


def icon(name, accent):
    return (f'<svg class="ehm-icon" viewBox="0 0 56 56" aria-hidden="true" style="--accent:{accent}">'
            f'{ICONS[name]}</svg>')


def hero_text(t, status_label, kicker, headline, body):
    return (f'<div class="ehm-hero-text"><div class="kicker">{pill(t, status_label)}<span>{kicker}</span></div>'
            f'<h1>{headline}</h1><p>{body}</p></div>')


def band_text(headline, body):
    return f'<div class="ehm-hero-text"><h1>{headline}</h1><p>{body}</p></div>'


def section_head(title, sub=''):
    return f'<div class="ehm-section"><h2>{title}</h2>' + (f'<p>{sub}</p>' if sub else '') + '</div>'


def features(items):
    """items: (icon name, accent colour, title, text, figure or '')."""
    cells = ''.join(f'<div>{icon(i, a)}' + (f'<b class="fig">{f}</b>' if f else '') + f'<h3>{h}</h3><p>{x}</p></div>'
                    for i, a, h, x, f in items)
    return f'<div class="ehm-features">{cells}</div>'


def station_table(t, stations, names):
    def tint(z):
        k = min(max((abs(z) - 1.5) / 2.5, 0), 1) * 0.85
        a, b = t['metal'].lstrip('#'), t['negative'].lstrip('#')
        mix = [round(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k) for i in (0, 2, 4)]
        return '#' + ''.join(f'{v:02x}' for v in mix)
    rows = ''.join(
        f'<tr><td><span class="sw" style="background:{tint(st["drift"])}"></span>{names[s]}'
        f'<small>{", ".join(x["code"] for x in st["sensors"])}</small></td>'
        f'<td class="n">{"+" if st["drift"] >= 0 else "−"}{abs(st["drift"]):.1f}σ'
        f'<small>{st["sensors"][0]["label"]}, {st["sensors"][0]["value"]} {st["sensors"][0]["unit"]}</small></td></tr>'
        for s, st in sorted(stations.items(), key=lambda kv: -abs(kv[1]['drift'])))
    return (f'<table class="ehm-sum ehm-stations"><thead><tr><th>Station, sensors</th><th class="n">Drift from a healthy engine</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>')


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

ENGINE_MARKUP = """
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
</div>"""

PLATE_MARKUP = """
<div class="wrap plate">
  <div class="stage" id="stage" tabindex="0" role="img" aria-label="" style="position:relative"><canvas id="c"></canvas>
    <div class="tools"><button id="explode" aria-pressed="false">Exploded view</button><button id="reset">Reset view</button></div></div>
  <div id="tip" role="tooltip"></div>
  <table id="tbl" hidden><tbody></tbody></table><span id="ramp" hidden></span>
</div>"""

ENGINE_SCRIPT = """<script>__THREE__</script>
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
  if (s && at) { const r = (tip.offsetParent || stage).getBoundingClientRect();
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
  camera.aspect = r.width / r.height; camera.position.z = D.plate ? 15.2 : (r.width < 520 ? 15.5 : 12.5); camera.updateProjectionMatrix(); render(); }
function render() { pivot.rotation.set(pitch, yaw, 0, 'XYZ'); renderer.render(scene, camera); }
new ResizeObserver(size).observe(stage); applyExplode(); size();
</script>"""


PLATE_CSS = """
:root{color-scheme:normal !important}
html,body{background:transparent !important}
.wrap.plate{position:relative;height:100vh;display:flex;align-items:center;justify-content:center}
.plate .stage{width:min(100vw - 96px, 100vh - 96px);height:auto;aspect-ratio:1;border-radius:50%;
  background:radial-gradient(circle at 34% 28%, #2b3037 0%, var(--plate) 60%, #030405 100%);
  box-shadow:0 0 0 9px #2a2e34, 0 0 0 10px #59606a, 0 0 0 11px #15181b, 0 26px 44px rgba(0,0,0,.45), inset 0 2px 1px rgba(255,255,255,.08)}
.plate canvas{border-radius:50%}
.plate .tools{left:50%;bottom:12%;transform:translateX(-50%);z-index:2}
.plate .tools button{white-space:nowrap}
.plate .tools button{background:linear-gradient(180deg,#ffffff 0%,#e4e7eb 45%,#b4bac2 56%,#eef0f3 100%);color:#15181c;border-color:#0b0c0e;
  box-shadow:inset 0 1px 0 #fff, 0 4px 10px rgba(0,0,0,.45)}
.plate .tools button[aria-pressed="true"]{background:#0a0a0a;color:#fff}
"""


def engine_html(t, engine_id, stations, plate=False):
    data = json.dumps({'engine': int(engine_id), 'stations': stations, 'plate': plate,
                       'theme': {'dark': t['dark'], 'metal': t['metal'], 'bad': t['negative'], 'hue': t['hue'],
                                 'shell': t['shell'], 'neutral': t['neutral'], 'env': t['env'], 'shadow': t['shadow']}})
    body = (PLATE_MARKUP if plate else ENGINE_MARKUP) + ENGINE_SCRIPT
    body = body.replace('__THREE__', THREE_JS).replace('__BEZIER__', BEZIER).replace('__DATA__', data)
    return _frame(t, ENGINE_CSS + (PLATE_CSS if plate else ''), body)


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

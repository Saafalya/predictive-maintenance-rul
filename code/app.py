"""Engine Health Monitor: local web app for the C-MAPSS RUL project.

Run with:  streamlit run code/app.py      (or double-click run_website.bat)

Uses the saved seed-0 CNN-LSTM + Attention models in models/. If one is missing it is
trained once on first launch (1-3 minutes on CPU) and saved.
"""
import datetime as dt
import json
import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import torch

import pdm
import ui

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MODEL_DIR = os.path.join(ROOT, 'models')
RESULTS = os.path.join(ROOT, 'results', 'results.json')
WINDOW, CAP, Y_SCALE = 30, 125, 125.0
BASE_CYCLES, RECENT_CYCLES = 30, 10

# Sensor names and units follow Saxena et al. (2008), Table 2. Station = where in the engine it measures.
SENSOR = {
    's2': ('T24', 'LPC outlet temperature', '°R', 'LPC'),
    's3': ('T30', 'HPC outlet temperature', '°R', 'HPC'),
    's4': ('T50', 'LPT outlet temperature', '°R', 'LPT'),
    's7': ('P30', 'HPC outlet pressure', 'psia', 'HPC'),
    's8': ('Nf', 'Fan speed', 'rpm', 'Fan'),
    's9': ('Nc', 'Core speed', 'rpm', 'HPT'),
    's11': ('Ps30', 'HPC outlet static pressure', 'psia', 'HPC'),
    's12': ('phi', 'Fuel flow to Ps30 ratio', 'pps/psi', 'HPC'),
    's13': ('NRf', 'Corrected fan speed', 'rpm', 'Fan'),
    's14': ('NRc', 'Corrected core speed', 'rpm', 'HPT'),
    's15': ('BPR', 'Bypass ratio', '', 'Fan'),
    's17': ('htBleed', 'Bleed enthalpy', '', 'Combustor'),
    's20': ('W31', 'HPT coolant bleed', 'lbm/s', 'HPT'),
    's21': ('W32', 'LPT coolant bleed', 'lbm/s', 'LPT'),
}
STATIONS = ['Fan', 'LPC', 'HPC', 'Combustor', 'HPT', 'LPT']
STATION_NAME = {'Fan': 'fan', 'LPC': 'low-pressure compressor', 'HPC': 'high-pressure compressor',
                'Combustor': 'combustor', 'HPT': 'high-pressure turbine', 'LPT': 'low-pressure turbine'}

st.set_page_config(page_title='Engine Health Monitor', page_icon=os.path.join(ROOT, 'code', 'static', 'mark.png'),
                   layout='wide')
look = st.query_params.get('look', 'Light')
look = look if look in ui.LOOKS else 'Light'


# ---------------------------------------------------------------- data + model
def scaler(subset):
    """Same min-max scaling as pdm.load (fitted on the seed-0 training engines only)."""
    train = pdm.read(f'train_{subset}.txt')
    units = train['unit'].unique()
    val_units = np.random.default_rng(0).choice(units, int(len(units) * 0.2), replace=False)
    fit = train[~train['unit'].isin(val_units)]
    lo, hi = fit[pdm.SENSORS].min(), fit[pdm.SENSORS].max()
    return lambda df: ((df[pdm.SENSORS] - lo) / (hi - lo + 1e-8)).values.astype(np.float32)


@st.cache_resource(show_spinner=False)
def get_model(subset):
    path = os.path.join(MODEL_DIR, f'cnn_lstm_att_{subset}.pt')
    model = pdm.CNNLSTMAttention(len(pdm.SENSORS))
    if os.path.exists(path):
        model.load_state_dict(torch.load(path, map_location='cpu'))
    else:
        torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
        r = pdm.train_dl('CNN-LSTM + Attention', pdm.load(subset), seed=0)
        model = r['model']
        os.makedirs(MODEL_DIR, exist_ok=True)
        torch.save(model.state_dict(), path)
    model.eval()
    return model


@st.cache_data(show_spinner=False)
def load_test(subset):
    test = pdm.read(f'test_{subset}.txt')
    true = np.loadtxt(os.path.join(pdm.DATA_DIR, f'RUL_{subset}.txt'))
    return test, true


@st.cache_data(show_spinner=False)
def healthy_baseline(subset):
    """Mean and spread of every sensor over the first 30 cycles of each training engine."""
    train = pdm.read(f'train_{subset}.txt')
    early = train[train['cycle'] <= BASE_CYCLES]
    return early[pdm.SENSORS].mean(), early[pdm.SENSORS].std()


def engine_windows(scaled):
    """One 30-cycle window ending at every cycle of an engine (early cycles padded)."""
    pad = len(scaled) < WINDOW
    if pad:
        scaled = np.vstack([np.repeat(scaled[:1], WINDOW - len(scaled), 0), scaled])
    X = np.stack([scaled[e - WINDOW:e] for e in range(WINDOW, len(scaled) + 1)])
    return X, pad


def predict(model, X):
    with torch.no_grad():
        p = model(torch.from_numpy(X)).numpy() * Y_SCALE
        att = model.last_attention.numpy()
    return np.clip(p, 0, None), att


@st.cache_data(show_spinner=False)
def fleet_predictions(subset):
    model, (test, _), scale = get_model(subset), load_test(subset), scaler(subset)
    last = [engine_windows(scale(g))[0][-1] for _, g in test.groupby('unit')]
    return predict(model, np.stack(last))[0]


def fmt_value(v):
    return f'{v:,.2f}' if abs(v) < 100 else f'{v:,.1f}'


def station_drift(g, mu, sd):
    recent = g[pdm.SENSORS].tail(RECENT_CYCLES).mean()
    z = (recent - mu) / sd
    out = {}
    for s in STATIONS:
        rows = [{'code': SENSOR[k][0], 'label': SENSOR[k][1], 'unit': SENSOR[k][2],
                 'value': fmt_value(recent[k]), 'z': round(float(z[k]), 2)}
                for k in pdm.SENSORS if SENSOR[k][3] == s]
        rows.sort(key=lambda r: -abs(r['z']))
        out[s] = {'drift': rows[0]['z'], 'sensors': rows}
    return out, z


# The fault NASA simulated in each fleet (Saxena et al., 2008)
FAULT = {'FD001': (['HPC'], 'the high-pressure compressor'),
         'FD003': (['HPC', 'Fan'], 'the high-pressure compressor and the fan')}


@st.cache_data(show_spinner=False)
def fleet_drift(subset):
    test, _ = load_test(subset)
    mu, sd = healthy_baseline(subset)
    return pd.DataFrame.from_dict(
        {int(u): {s: station_drift(g, mu, sd)[0][s]['drift'] for s in STATIONS} for u, g in test.groupby('unit')},
        orient='index')


def name_list(ids, show=3):
    ids = [str(i) for i in ids]
    if len(ids) <= show + 1:
        return ids[0] if len(ids) == 1 else ', '.join(ids[:-1]) + ' and ' + ids[-1]
    return ', '.join(ids[:show]) + f' and {len(ids) - show} others'


def plural(n, one, many):
    return f'{n} {one if n == 1 else many}'


def status(rul, red, amber):
    if rul <= red:
        return 'Critical', 'Ground the engine and schedule a shop visit now.'
    if rul <= amber:
        return 'Plan maintenance', 'Book a shop visit within the next few weeks.'
    return 'Healthy', 'No action needed. Keep monitoring.'


def lead_lower(text):
    """Lower-case the first word unless it is an acronym such as HPC."""
    first = text.split()[0]
    return text if first.isupper() and len(first) > 1 else text[0].lower() + text[1:]


def signed(v, digits=0):
    s = f'{abs(v):.{digits}f}'
    return ('+' if v > 0 else '−' if v < 0 else '') + s


# ---------------------------------------------------------------- sidebar
mark_slot = st.sidebar.empty()
picked = st.sidebar.segmented_control('Appearance', ui.LOOKS, default=look, key='look_pick')
if picked and picked != look:
    look = picked
    st.query_params['look'] = look
t = ui.THEMES[look]
st.markdown(ui.css(t), unsafe_allow_html=True)
components.html(ui.theme_sync_html(t['dark']), height=0)
subset = st.sidebar.radio('Fleet', ['FD001', 'FD003'],
                          format_func=lambda s: {'FD001': 'FD001, one fault mode', 'FD003': 'FD003, two fault modes'}[s])
mark_slot.markdown(ui.mark_html(t, subset), unsafe_allow_html=True)
st.sidebar.markdown('**Maintenance thresholds**')
red = st.sidebar.slider('Critical at or below (cycles)', 5, 60, 25)
amber = st.sidebar.slider('Plan maintenance at or below (cycles)', red + 5, 125, max(red + 5, 60))
st.sidebar.markdown(
    '<p class="ehm-side-note">Model: CNN-LSTM with additive attention, seed 0, trained on NASA C-MAPSS. '
    'Remaining life is capped at 125 cycles, as in training. Drift compares each sensor’s last 10 cycles '
    'with its first 30 across all training engines.</p>', unsafe_allow_html=True)

if not os.path.exists(os.path.join(MODEL_DIR, f'cnn_lstm_att_{subset}.pt')):
    with st.spinner(f'First run for {subset}: training the model once (1-3 minutes). It is saved afterwards.'):
        get_model(subset)

model = get_model(subset)
test, true_rul = load_test(subset)
scale = scaler(subset)
mu, sd = healthy_baseline(subset)
fleet_pred = fleet_predictions(subset)
true_capped = np.minimum(true_rul, CAP)
fleet = pd.DataFrame({'Engine': np.arange(1, len(fleet_pred) + 1), 'Predicted': np.round(fleet_pred).astype(int),
                      'Actual': true_rul.astype(int)})
fleet['Status'] = [status(p, red, amber)[0] for p in fleet_pred]
n_crit = int((fleet['Status'] == 'Critical').sum())
n_plan = int((fleet['Status'] == 'Plan maintenance').sum())
n_ok = int((fleet['Status'] == 'Healthy').sum())
assert n_crit + n_plan + n_ok == len(fleet)
lowest = fleet.sort_values('Predicted').iloc[0]

# ---------------------------------------------------------------- title card
urgent = fleet.sort_values(['Predicted', 'Engine'])
crit_ids = urgent[urgent['Status'] == 'Critical']['Engine'].tolist()
plan_ids = urgent[urgent['Status'] == 'Plan maintenance']['Engine'].tolist()
err = fleet_pred - true_capped
rmse, mae = pdm.rmse(fleet_pred, true_capped), float(np.mean(np.abs(err)))
near = true_capped < 50
rmse_near = pdm.rmse(fleet_pred[near], true_capped[near]) if near.any() else float('nan')
n_late = int((np.round(fleet_pred) > np.round(true_capped)).sum())
n_early = int((np.round(fleet_pred) < np.round(true_capped)).sum())

sentence = (f'{len(fleet)} engines checked: {n_crit} should stop flying now, {n_plan} need a shop visit soon '
            f'and {n_ok} are fine. Engine {int(lowest.Engine)} is the most urgent, with about '
            f'{plural(int(lowest.Predicted), "flight", "flights")} left.')
segments = [('Critical', n_crit, 'stop flying now', f'{red} flights or fewer left'),
            ('Plan maintenance', n_plan, 'book a shop visit', f'{red + 1} to {amber} flights left'),
            ('Healthy', n_ok, 'keep flying', f'more than {amber} flights left')]

# Plain-words summary, every line computed from the numbers on this page
share_ok = n_ok / len(fleet)
overall = ('Most engines are in good shape.' if share_ok >= 0.75 else
           'More than half the engines can keep flying normally.' if share_ok >= 0.5 else
           'Fewer than half the engines can keep flying normally; the fleet needs attention.')
fd = fleet_drift(subset)
crit_drift = fd.loc[crit_ids] if crit_ids else fd.loc[urgent['Engine'].head(10)]
by_station = crit_drift.abs().mean().sort_values(ascending=False)
top = by_station.index[0]
expected, expected_words = FAULT[subset]
matches = top in expected
wear = (f'In the engines closest to failure, the {STATION_NAME[top]} has changed the most. '
        + ('That matches the fault NASA built into this fleet, so the model is picking up the right signal.'
           if matches else f'NASA built its fault into {expected_words}, which also shows clear change.'))
late_words = ('It guesses a little late more often than early, so keep a safety margin.' if n_late > n_early else
              'It guesses early at least as often as late, which errs on the side of caution.')
summary = [
    ('How is the fleet doing?', overall,
     f'{n_ok} healthy, {n_plan} plan maintenance, {n_crit} critical, of {len(fleet)}'),
    ('Which engines should stop flying now?',
     (f'Engines {name_list(crit_ids)} are close to the end of their safe life.' if len(crit_ids) > 1 else
      f'Engine {crit_ids[0]} is close to the end of its safe life.' if crit_ids else
      'None right now. No engine is inside the critical limit.'),
     f'{red} cycles or fewer predicted' + (f'; lowest is engine {crit_ids[0]} at {int(lowest.Predicted)}' if crit_ids else '')),
    ('Which ones need a visit soon?',
     (f'{plural(n_plan, "engine", "engines")} should be booked in for a check in the coming weeks: {name_list(plan_ids)}.'
      if plan_ids else 'None. Every engine is either critical or comfortably healthy.'),
     f'{red + 1} to {amber} cycles predicted'),
    ('Where is the wear showing?', wear,
     'Average drift in ' + ('critical' if crit_ids else 'the 10 most urgent') + ' engines: '
     + ', '.join(f'{k} {by_station[k]:.1f}σ' for k in by_station.index[:3])),
    ('How far off are the predictions?',
     f'Usually within about {round(mae)} flights. They get sharper as an engine nears failure.',
     f'Average error {mae:.1f}, RMSE {rmse:.1f} cycles; RMSE {rmse_near:.1f} when under 50 remain'),
    ('Does it guess early or late?', late_words,
     f'Late on {n_late}, early on {n_early}, exact on {len(fleet) - n_late - n_early} engines'),
    ('What should we do next?',
     ' '.join(x for x in [
         f'Ground {plural(n_crit, "engine", "engines")} and inspect the {STATION_NAME[top]}'
         + (f' and {STATION_NAME[by_station.index[1]]}' if len(by_station) > 1 else '') + ' first.' if n_crit else '',
         f'Book shop visits for {plural(n_plan, "other", "others")}.' if n_plan else '',
         'Keep monitoring the rest.'] if x),
     'Download a work order for any engine from Check an engine'),
]
assert n_crit + n_plan + n_ok == len(fleet) and n_late + n_early <= len(fleet)

with st.container(border=True, key='card-title'):
    st.markdown(ui.title_card(t, f'Fleet {subset}', sentence, segments,
                              [f'NASA C-MAPSS {subset}', 'CNN-LSTM + attention model']), unsafe_allow_html=True)
    with st.expander('Summary in plain words', expanded=True):
        st.markdown(ui.summary_table(summary), unsafe_allow_html=True)
        st.caption('Written automatically from the model’s predictions and the sensor data on this page. '
                   'It updates when you change the fleet or the thresholds. A cycle is one flight.')

tab_engine, tab_fleet, tab_upload, tab_models = st.tabs(
    ['Check an engine', 'Fleet board', 'Score your own data', 'Model comparison'])

# ---------------------------------------------------------------- engine view
with tab_engine:
    units = sorted(test['unit'].unique())
    longest = int(test.groupby('unit').size().idxmax())
    head, pick = st.columns([3, 1.1], vertical_alignment='bottom')
    with pick:
        unit = st.selectbox('Engine', units, index=units.index(longest), format_func=lambda u: f'Engine {u}')

    g = test[test['unit'] == unit]
    X, padded = engine_windows(scale(g))
    preds, att = predict(model, X)
    p_now, t_now = float(preds[-1]), float(true_rul[unit - 1])
    label, advice = status(p_now, red, amber)
    stations, z = station_drift(g, mu, sd)
    worst = max(STATIONS, key=lambda s: abs(stations[s]['drift']))
    ws = stations[worst]['sensors'][0]
    err = round(p_now) - round(min(t_now, CAP))

    with head:
        st.markdown(
            f'<div class="ehm-title"><h2>Engine {unit} &nbsp;{ui.pill(t, label)}</h2>'
            f'<p>Predicted <b>{p_now:.0f} cycles</b> left, against {t_now:.0f} actual. The {STATION_NAME[worst]} '
            f'shows the most wear: {lead_lower(ws["label"])} is {signed(ws["z"], 1)}σ from a healthy engine.</p></div>',
            unsafe_allow_html=True)

    order = (f'WORK ORDER: ENGINE {unit}, FLEET {subset}\n'
             f'Generated {dt.datetime.now():%Y-%m-%d %H:%M}\n\n'
             f'Status: {label}. {advice}\n'
             f'Predicted remaining life: {p_now:.0f} cycles (thresholds: critical {red}, plan {amber})\n'
             f'Cycles flown so far: {len(g)}\n\n'
             f'Inspect first, by sensor drift from a healthy engine:\n'
             + ''.join(f'  {s:<10} {signed(stations[s]["drift"], 1):>6} sigma  '
                       f'({stations[s]["sensors"][0]["label"]}, {stations[s]["sensors"][0]["value"]} '
                       f'{stations[s]["sensors"][0]["unit"]})\n'
                       for s in sorted(STATIONS, key=lambda s: -abs(stations[s]['drift'])))
             + '\nModel: CNN-LSTM + attention, seed 0. Prediction only; confirm with a borescope inspection.\n')
    with pick:
        st.download_button('Download work order', order, f'work_order_engine_{unit}_{subset}.txt',
                           type='primary', width='stretch')

    map_col, life_col = st.columns([2.75, 1], gap='medium')
    with map_col:
        with st.container(border=True, key='card-1'):
            st.markdown('### Where the wear shows')
            components.html(ui.engine_html(t, unit, stations), height=418)
    with life_col:
        with st.container(border=True, key='card-2'):
            st.markdown('### Remaining life')
            components.html(ui.dial_html(t, p_now, t_now, red, amber, CAP), height=212)
            late = err > 0
            err_col = t['negative'] if late else t['text']
            err_txt = ('on target' if err == 0 else
                       f'<span style="color:{err_col}">{signed(err)}</span>'
                       f'<small>{"late" if late else "early"}</small>')
            st.markdown(ui.kv([('Actual cycles left', f'{t_now:.0f}'),
                               ('Prediction error', err_txt),
                               ('Cycles flown so far', f'{len(g)}'),
                               ('Next threshold', f'{red if p_now > red else 0}<small>cycles</small>')]),
                        unsafe_allow_html=True)
            st.caption(advice)

    traj_col, att_col = st.columns([2, 1], gap='medium')
    with traj_col:
        with st.container(border=True, key='card-3'):
            st.markdown('### Predicted life over this engine’s history')
            cycles = g['cycle'].values[-len(preds):] if not padded else g['cycle'].values[-1:]
            traj = pd.DataFrame({'Cycle': cycles, 'Predicted': preds[-len(cycles):]})
            traj['Actual (capped at 125)'] = np.minimum(t_now + (cycles.max() - cycles), CAP)
            long = traj.melt('Cycle', var_name='Series', value_name='RUL')
            dom = ['Predicted', 'Actual (capped at 125)']
            lines = alt.Chart(long).mark_line(point=len(cycles) < 3).encode(
                x=alt.X('Cycle:Q', title='Cycle', scale=alt.Scale(zero=False, nice=False)),
                y=alt.Y('RUL:Q', title='Cycles left', scale=alt.Scale(domain=[0, 140])),
                color=alt.Color('Series:N', scale=alt.Scale(domain=dom, range=[t['hue'], t['comp']]), title=None),
                strokeDash=alt.StrokeDash('Series:N', scale=alt.Scale(domain=dom, range=[[1, 0], [5, 4]]), legend=None),
                strokeWidth=alt.StrokeWidth('Series:N', scale=alt.Scale(domain=dom, range=[2, 1.5]), legend=None),
                tooltip=['Cycle', 'Series', alt.Tooltip('RUL:Q', format='.0f', title='Cycles left')])
            refs = pd.DataFrame({'y': [red, amber], 'label': [f'Critical, {red}', f'Plan maintenance, {amber}'],
                                 'x': [cycles.min()] * 2})
            rule = alt.Chart(refs).mark_rule(strokeDash=[3, 3], color=t['axis'], strokeWidth=1).encode(y='y:Q')
            txt = alt.Chart(refs).mark_text(align='left', dx=4, dy=-6, fontSize=11, color=t['muted']).encode(
                x='x:Q', y='y:Q', text='label:N')
            st.altair_chart(ui.styled(t, (rule + txt + lines).properties(height=250)), width='stretch')
            if padded:
                st.caption('This engine has fewer than 30 recorded cycles, so only one prediction exists.')
    with att_col:
        with st.container(border=True, key='card-4'):
            st.markdown('### Where the model looked')
            a = pd.DataFrame({'Cycles ago': np.arange(WINDOW - 1, -1, -1), 'Weight': att[-1]})
            st.altair_chart(ui.styled(t, alt.Chart(a).mark_bar(color=t['text'], width=4).encode(
                x=alt.X('Cycles ago:Q', title='Cycles ago', scale=alt.Scale(domain=[29.5, -0.5])),
                y=alt.Y('Weight:Q', title='Attention weight'),
                tooltip=['Cycles ago', alt.Tooltip('Weight', format='.3f')]).properties(height=212)),
                width='stretch')
            st.caption(f'{att[-1][-1]:.0%} of the weight sits on the latest cycle and '
                       f'{att[-1][-5:].sum():.0%} on the last five.')

    with st.container(border=True, key='card-5'):
        st.markdown('### Sensor history')
        ranked = sorted(pdm.SENSORS, key=lambda k: -abs(z[k]))
        s_col, note_col = st.columns([1.2, 2.8], vertical_alignment='bottom')
        with s_col:
            sensor = st.selectbox('Sensor', ranked, format_func=lambda k: f'{SENSOR[k][1]} ({SENSOR[k][0]})')
        code, name, unit_s, stn = SENSOR[sensor]
        with note_col:
            st.caption(f'Measured at the {STATION_NAME[stn]}. Last {RECENT_CYCLES} cycles average '
                       f'{fmt_value(g[sensor].tail(RECENT_CYCLES).mean())} {unit_s}, {signed(z[sensor], 1)}σ from the '
                       f'healthy baseline of {fmt_value(mu[sensor])} {unit_s}. Sorted by drift, largest first.')
        line = alt.Chart(g).mark_line(color=t['text'], strokeWidth=1.4).encode(
            x=alt.X('cycle:Q', title='Cycle'),
            y=alt.Y(f'{sensor}:Q', title=f'{code} ({unit_s})' if unit_s else code, scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip('cycle', title='Cycle'), alt.Tooltip(sensor, title=code, format=',.2f')])
        base = pd.DataFrame({'y': [mu[sensor]], 'x': [g['cycle'].max()], 't': ['Healthy baseline']})
        brule = alt.Chart(base).mark_rule(strokeDash=[3, 3], color=t['axis']).encode(y='y:Q')
        btxt = alt.Chart(base).mark_text(align='right', dy=-6, fontSize=11, color=t['muted']).encode(x='x:Q', y='y:Q', text='t:N')
        st.altair_chart(ui.styled(t, (brule + btxt + line).properties(height=220)), width='stretch')

# ---------------------------------------------------------------- fleet board
with tab_fleet:
    with st.container(border=True, key='card-6'):
        st.markdown('### Every engine, most urgent first')
        board = fleet.sort_values(['Predicted', 'Engine'])
        components.html(ui.hangar_html(t, board.to_dict('records')), height=-(-len(board) // 10) * 60 + 4, scrolling=True)

    sc_col, list_col = st.columns([1.6, 1], gap='medium')
    with sc_col:
        with st.container(border=True, key='card-7'):
            st.markdown('### Predicted against actual')
            sc = alt.Chart(fleet.assign(Capped=true_capped)).mark_circle(size=46, opacity=0.85).encode(
                x=alt.X('Capped:Q', title='Actual cycles left (capped at 125)', scale=alt.Scale(domain=[0, 130])),
                y=alt.Y('Predicted:Q', title='Predicted cycles left', scale=alt.Scale(domain=[0, 140])),
                color=alt.Color('Status:N', title=None, scale=alt.Scale(domain=list(t['status']), range=list(t['status'].values()))),
                tooltip=['Engine', 'Predicted', 'Actual', 'Status'])
            diag = alt.Chart(pd.DataFrame({'x': [0, CAP], 'y': [0, CAP]})).mark_line(
                color=t['axis'], strokeDash=[3, 3], strokeWidth=1).encode(x='x:Q', y='y:Q')
            st.altair_chart(ui.styled(t, (diag + sc).properties(height=330)), width='stretch')
            st.caption('On the dashed line the prediction is exact. Above it the model predicted failure too late.')
    with list_col:
        with st.container(border=True, key='card-8'):
            st.markdown('### Shop visit queue')
            q = fleet[fleet['Status'] != 'Healthy'].sort_values('Predicted')
            st.dataframe(q.rename(columns={'Predicted': 'Predicted (cycles)', 'Actual': 'Actual (cycles)'}),
                         hide_index=True, width='stretch', height=372,
                         column_config={'Engine': st.column_config.NumberColumn(format='%d')})

# ---------------------------------------------------------------- upload
with tab_upload:
    with st.container(border=True, key='card-9'):
        st.markdown('### Score a sensor file')
        st.markdown('Upload readings in the C-MAPSS format: a space-separated text file with 26 columns '
                    '(engine id, cycle, 3 operating settings, 21 sensors), like `test_FD001.txt`. '
                    f'The **{subset}** model from the sidebar scores it.')
        up = st.file_uploader('Sensor file (.txt or .csv)', type=['txt', 'csv'])
        if up is not None:
            try:
                u = pd.read_csv(up, sep=r'\s+', header=None, names=pdm.COLS)
                out = []
                for unit_id, gg in u.groupby('unit'):
                    p = float(predict(model, engine_windows(scale(gg))[0][-1:])[0][0])
                    out.append({'Engine': unit_id, 'Cycles flown': len(gg), 'Predicted (cycles)': round(p),
                                'Status': status(p, red, amber)[0]})
                out = pd.DataFrame(out).sort_values('Predicted (cycles)')
                st.success(f'Scored {len(out)} engine{"s" if len(out) != 1 else ""}.')
                st.dataframe(out, hide_index=True, width='stretch')
                st.download_button('Download predictions (CSV)', out.to_csv(index=False), 'predictions.csv')
            except Exception as e:
                st.error(f'Could not read that file. It needs 26 space-separated columns per row. ({e})')

# ---------------------------------------------------------------- models
with tab_models:
    with st.container(border=True, key='card-10'):
        st.markdown('### Test error by model')
        st.caption('From the full experiment in results/results.json: mean ± standard deviation over 5 seeds. '
                   'Lower is better for both. PHM08 penalises late predictions more than early ones.')
        try:
            res = json.load(open(RESULTS))['main'][subset]
            rows = [{'Model': n, 'RMSE (cycles)': f"{r['rmse_mean']:.2f} ± {r['rmse_std']:.2f}" if r['rmse_std'] else f"{r['rmse_mean']:.2f}",
                     'PHM08 score': f"{r['score_mean']:,.0f} ± {r['score_std']:,.0f}" if r['score_std'] else f"{r['score_mean']:,.0f}",
                     'Parameters': f"{r['params']:,}" if r['params'] else '—',
                     'm': r['rmse_mean'], 's': r['rmse_std']} for n, r in res.items()]
            tbl = pd.DataFrame(rows).sort_values('m')
            order_m = tbl['Model'].tolist()
            c1, c2 = st.columns([1, 1.2], gap='large')
            with c1:
                st.dataframe(tbl.drop(columns=['m', 's']), hide_index=True, width='stretch')
            with c2:
                bar = alt.Chart(tbl).mark_bar(height=16).encode(
                    x=alt.X('m:Q', title='RMSE (cycles)', scale=alt.Scale(domain=[0, 18])),
                    y=alt.Y('Model:N', sort=order_m, title=None, axis=alt.Axis(labelLimit=220)),
                    color=alt.condition(alt.datum.Model == 'CNN-LSTM + Attention', alt.value(t['hue']), alt.value(t['comp'])),
                    tooltip=['Model', 'RMSE (cycles)', 'PHM08 score'])
                eb = alt.Chart(tbl).mark_rule(color=t['text']).encode(
                    x='lo:Q', x2='hi:Q', y=alt.Y('Model:N', sort=order_m)).transform_calculate(
                    lo='datum.m - datum.s', hi='datum.m + datum.s')
                st.altair_chart(ui.styled(t, (bar + eb).properties(height=200)), width='stretch')
        except Exception:
            st.info('No results yet. Run the full experiment from start.bat, option 1, then refresh this page.')

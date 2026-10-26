"""Local web app for the C-MAPSS RUL project.

Run with:  streamlit run code/app.py      (or double-click run_website.bat)

The first time a dataset is opened, the CNN-LSTM + Attention model is trained
once (about 1-3 minutes on CPU) and saved to models/. After that it loads instantly.
"""
import json
import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import torch

import pdm

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MODEL_DIR = os.path.join(ROOT, 'models')
RESULTS = os.path.join(ROOT, 'results', 'results.json')
WINDOW, CAP, Y_SCALE = 30, 125, 125.0

SENSOR_NAMES = {
    's2': 'LPC outlet temperature', 's3': 'HPC outlet temperature', 's4': 'LPT outlet temperature',
    's7': 'HPC outlet pressure', 's8': 'Physical fan speed', 's9': 'Physical core speed',
    's11': 'HPC outlet static pressure', 's12': 'Fuel flow to Ps30 ratio', 's13': 'Corrected fan speed',
    's14': 'Corrected core speed', 's15': 'Bypass ratio', 's17': 'Bleed enthalpy',
    's20': 'HPT coolant bleed', 's21': 'LPT coolant bleed',
}

st.set_page_config(page_title='Engine Health Monitor', page_icon='✈️', layout='wide')


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


def engine_windows(scaled):
    """One 30-cycle window ending at every cycle of an engine (early cycles padded)."""
    if len(scaled) < WINDOW:
        scaled = np.vstack([np.repeat(scaled[:1], WINDOW - len(scaled), 0), scaled])
        pad = True
    else:
        pad = False
    X = np.stack([scaled[e - WINDOW:e] for e in range(WINDOW, len(scaled) + 1)])
    return X, pad


def predict(model, X):
    with torch.no_grad():
        p = model(torch.from_numpy(X)).numpy() * Y_SCALE
        att = model.last_attention.numpy()
    return np.clip(p, 0, None), att


@st.cache_data(show_spinner=False)
def fleet_predictions(subset):
    model = get_model(subset)
    test, true = load_test(subset)
    scale = scaler(subset)
    last = []
    for _, g in test.groupby('unit'):
        X, _ = engine_windows(scale(g))
        last.append(X[-1])
    pred, _ = predict(model, np.stack(last))
    return pred


def status(rul, red, amber):
    if rul <= red:
        return 'Critical', '#c0392b', 'Ground the engine and service it now.'
    if rul <= amber:
        return 'Plan maintenance', '#d68910', 'Book maintenance in the next few weeks.'
    return 'Healthy', '#1e8449', 'No action needed. Keep monitoring.'


# ---------------------------------------------------------------- sidebar
st.sidebar.title('✈️ Engine Health Monitor')
st.sidebar.caption('Predicts remaining useful life (RUL) of turbofan engines from NASA C-MAPSS sensor data.')
subset = st.sidebar.radio('Engine fleet', ['FD001', 'FD003'],
                          format_func=lambda s: {'FD001': 'FD001 · one fault type',
                                                 'FD003': 'FD003 · two fault types'}[s])
st.sidebar.markdown('**Maintenance thresholds** (cycles left)')
red = st.sidebar.slider('Critical at or below', 5, 60, 25)
amber = st.sidebar.slider('Plan maintenance at or below', red + 5, 125, max(red + 5, 60))
st.sidebar.divider()
st.sidebar.caption('Model: CNN-LSTM with additive attention (seed 0). '
                   'Predictions are capped at 125 cycles, same as in training.')

if not os.path.exists(os.path.join(MODEL_DIR, f'cnn_lstm_att_{subset}.pt')):
    with st.spinner(f'First run for {subset}: training the model once (1-3 minutes). It is saved afterwards.'):
        get_model(subset)

model = get_model(subset)
test, true_rul = load_test(subset)
scale = scaler(subset)
fleet_pred = fleet_predictions(subset)
true_capped = np.minimum(true_rul, CAP)

tab_engine, tab_fleet, tab_upload, tab_models = st.tabs(
    ['🔧 Check an engine', '📋 Fleet overview', '📤 Try your own data', '📊 Model comparison'])

# ---------------------------------------------------------------- engine tab
with tab_engine:
    units = sorted(test['unit'].unique())
    c1, c2 = st.columns([1, 3])
    with c1:
        longest = int(test.groupby('unit').size().idxmax())
        unit = st.selectbox('Test engine', units, index=units.index(longest),
                            format_func=lambda u: f'Engine {u}')
    g = test[test['unit'] == unit]
    X, padded = engine_windows(scale(g))
    preds, att = predict(model, X)
    p_now = float(preds[-1])
    t_now = float(true_rul[unit - 1])
    label, color, advice = status(p_now, red, amber)

    with c2:
        st.markdown(
            f"<div style='padding:14px 18px;border-radius:10px;background:{color}1a;border-left:6px solid {color}'>"
            f"<span style='font-size:1.3rem;font-weight:600;color:{color}'>{label}</span><br>"
            f"<span>{advice}</span></div>", unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Predicted cycles left', f'{p_now:.0f}')
    m2.metric('Actual cycles left', f'{t_now:.0f}',
              help='From NASA’s answer file. Values above 125 are shown in full here but the model caps at 125.')
    err = p_now - min(t_now, CAP)
    m3.metric('Error vs. capped actual', f'{err:+.0f}',
              help='Positive = predicted too late (riskier). Negative = predicted too early.')
    m4.metric('Cycles observed so far', len(g))

    st.subheader('How the prediction changed over this engine’s life')
    cycles = g['cycle'].values[-len(preds):] if not padded else g['cycle'].values[-1:]
    traj = pd.DataFrame({'Cycle': cycles, 'Predicted RUL': preds[-len(cycles):]})
    traj['Actual RUL (capped)'] = np.minimum(t_now + (cycles.max() - cycles), CAP)
    long = traj.melt('Cycle', var_name='Series', value_name='RUL')
    x0, x1 = float(cycles.min()), float(cycles.max())
    if x0 == x1:
        x0 -= 1
    bands = pd.DataFrame({'x0': [x0] * 3, 'x1': [x1] * 3,
                          'y0': [0, red, amber], 'y1': [red, amber, CAP + 10],
                          'zone': ['#c0392b', '#d68910', '#1e8449']})
    zone = alt.Chart(bands).mark_rect(opacity=0.09).encode(
        x=alt.X('x0:Q', title='Cycle'), x2='x1:Q', y=alt.Y('y0:Q', title='Cycles left'), y2='y1:Q', color=alt.Color('zone:N', scale=None))
    lines = alt.Chart(long).mark_line(point=len(cycles) < 40, strokeWidth=2.5).encode(
        x=alt.X('Cycle:Q', title='Cycle', scale=alt.Scale(zero=False)),
        y=alt.Y('RUL:Q', title='Cycles left', scale=alt.Scale(domain=[0, CAP + 10])),
        color=alt.Color('Series:N', scale=alt.Scale(domain=['Predicted RUL', 'Actual RUL (capped)'],
                                                    range=['#7b241c', '#566573']),
                        legend=alt.Legend(orient='top', title=None)),
        strokeDash=alt.StrokeDash('Series:N', scale=alt.Scale(domain=['Predicted RUL', 'Actual RUL (capped)'],
                                                              range=[[1, 0], [6, 4]]), legend=None),
        tooltip=['Cycle', 'Series', alt.Tooltip('RUL:Q', format='.0f')])
    st.altair_chart((zone + lines).resolve_scale(color='independent').properties(height=320), width='stretch')
    st.caption('Shaded bands show the critical (red), plan-maintenance (amber) and healthy (green) zones.')
    if padded:
        st.info('This engine has fewer than 30 recorded cycles, so only one prediction could be made.')

    left, right = st.columns(2)
    with left:
        st.subheader('Sensor readings')
        default = ['s4', 's11']
        chosen = st.multiselect('Sensors', pdm.SENSORS, default=default,
                                format_func=lambda s: f'{s} · {SENSOR_NAMES.get(s, s)}')
        for s in chosen:
            st.altair_chart(alt.Chart(g).mark_line(color='#34495e').encode(
                x=alt.X('cycle:Q', title='Cycle'),
                y=alt.Y(f'{s}:Q', title=None, scale=alt.Scale(zero=False)),
                tooltip=['cycle', s]).properties(height=140, title=f'{s} · {SENSOR_NAMES.get(s, s)}'),
                width='stretch')
    with right:
        st.subheader('Where the model looked')
        a = pd.DataFrame({'Cycles ago': np.arange(WINDOW - 1, -1, -1), 'Attention': att[-1]})
        st.altair_chart(alt.Chart(a).mark_bar(color='#7b241c').encode(
            x=alt.X('Cycles ago:O', sort='descending', title='Cycles ago (0 = latest)'),
            y=alt.Y('Attention:Q', title='Attention weight'),
            tooltip=['Cycles ago', alt.Tooltip('Attention', format='.3f')]).properties(height=260),
            width='stretch')
        st.caption(f'The model put {att[-1][-1]:.0%} of its attention on the latest cycle '
                   f'and {att[-1][-5:].sum():.0%} on the last five.')

# ---------------------------------------------------------------- fleet tab
with tab_fleet:
    df = pd.DataFrame({'Engine': np.arange(1, len(fleet_pred) + 1),
                       'Predicted RUL': fleet_pred.round(0),
                       'Actual RUL': true_rul.astype(int),
                       'Error (vs capped)': (fleet_pred - true_capped).round(0)})
    df['Status'] = [status(p, red, amber)[0] for p in fleet_pred]
    rmse = pdm.rmse(fleet_pred, true_capped)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Engines', len(df))
    k2.metric('Critical', int((df['Status'] == 'Critical').sum()))
    k3.metric('Plan maintenance', int((df['Status'] == 'Plan maintenance').sum()))
    k4.metric('Test RMSE', f'{rmse:.2f}', help='Average size of the error in cycles, on the 100 test engines.')

    sc = alt.Chart(df.assign(Capped=true_capped)).mark_circle(size=60, opacity=0.75).encode(
        x=alt.X('Capped:Q', title='Actual RUL (capped at 125)'),
        y=alt.Y('Predicted RUL:Q', title='Predicted RUL'),
        color=alt.Color('Status:N', scale=alt.Scale(domain=['Critical', 'Plan maintenance', 'Healthy'],
                                                    range=['#c0392b', '#d68910', '#1e8449'])),
        tooltip=['Engine', 'Predicted RUL', 'Actual RUL', 'Status'])
    diag = alt.Chart(pd.DataFrame({'x': [0, CAP], 'y': [0, CAP]})).mark_line(
        color='#999', strokeDash=[4, 4]).encode(x=alt.X('x:Q', title='Actual RUL (capped at 125)'), y=alt.Y('y:Q', title='Predicted RUL'))
    st.subheader('Predicted vs. actual')
    st.caption('Points on the dashed line are perfect predictions. Above the line = predicted too late.')
    st.altair_chart((diag + sc).properties(height=380), width='stretch')

    st.subheader('All engines')
    only = st.multiselect('Show', ['Critical', 'Plan maintenance', 'Healthy'],
                          default=['Critical', 'Plan maintenance', 'Healthy'])
    st.dataframe(df[df['Status'].isin(only)].sort_values('Predicted RUL'),
                 hide_index=True, width='stretch')

# ---------------------------------------------------------------- upload tab
with tab_upload:
    st.markdown('Upload sensor readings in the C-MAPSS format: a space-separated text file with '
                '26 columns (engine id, cycle, 3 operating settings, 21 sensors), like `test_FD001.txt`. '
                f'Predictions use the **{subset}** model selected in the sidebar.')
    up = st.file_uploader('Sensor file', type=['txt', 'csv'])
    if up is not None:
        try:
            u = pd.read_csv(up, sep=r'\s+', header=None, names=pdm.COLS)
            rows = []
            for unit_id, gg in u.groupby('unit'):
                Xu, _ = engine_windows(scale(gg))
                p, _ = predict(model, Xu[-1:])
                lab = status(float(p[0]), red, amber)[0]
                rows.append({'Engine': unit_id, 'Cycles observed': len(gg),
                             'Predicted RUL': round(float(p[0])), 'Status': lab})
            out = pd.DataFrame(rows)
            st.success(f'Scored {len(out)} engine(s).')
            st.dataframe(out, hide_index=True, width='stretch')
            st.download_button('Download predictions (CSV)', out.to_csv(index=False), 'predictions.csv')
        except Exception as e:
            st.error(f'Could not read that file. Check it has 26 space-separated columns. ({e})')

# ---------------------------------------------------------------- models tab
with tab_models:
    st.markdown('Results from the full experiment (`results/results.json`), mean ± std over 5 random seeds. '
                '**Lower is better** for both metrics. PHM08 punishes late predictions more than early ones.')
    try:
        res = json.load(open(RESULTS))['main'][subset]
        rows = []
        for name, r in res.items():
            rows.append({'Model': name,
                         'RMSE': f"{r['rmse_mean']:.2f} ± {r['rmse_std']:.2f}" if r['rmse_std'] else f"{r['rmse_mean']:.2f}",
                         'PHM08 score': f"{r['score_mean']:.0f} ± {r['score_std']:.0f}" if r['score_std'] else f"{r['score_mean']:.0f}",
                         'Parameters': f"{r['params']:,}" if r['params'] else '—',
                         'rmse_mean': r['rmse_mean'], 'rmse_std': r['rmse_std']})
        t = pd.DataFrame(rows).sort_values('rmse_mean')
        st.dataframe(t.drop(columns=['rmse_mean', 'rmse_std']), hide_index=True, width='stretch')
        order = t['Model'].tolist()
        bar = alt.Chart(t).mark_bar().encode(
            x=alt.X('rmse_mean:Q', title='Test RMSE (cycles)'),
            y=alt.Y('Model:N', sort=order, title=None, axis=alt.Axis(labelLimit=200)),
            color=alt.condition(alt.datum.Model == 'CNN-LSTM + Attention', alt.value('#7b241c'), alt.value('#aab7b8')),
            tooltip=['Model', 'RMSE', 'PHM08 score'])
        err = alt.Chart(t).mark_errorbar().encode(
            x=alt.X('lo:Q', title='Test RMSE (cycles)'), x2='hi:Q', y=alt.Y('Model:N', sort=order, title=None)).transform_calculate(
            lo='datum.rmse_mean - datum.rmse_std', hi='datum.rmse_mean + datum.rmse_std')
        st.altair_chart((bar + err).properties(height=240), width='stretch')
    except Exception:
        st.warning('results/results.json not found or incomplete. Run the full experiment from start.bat first.')

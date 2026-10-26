"""EnginePulse v2: can the CNN-LSTM + attention model be made more accurate?

Every choice here is made on the VALIDATION engines only (20% of the training engines,
held out by unit). The 100 test engines are scored once per configuration and never used
to pick anything, so the final test numbers stay an honest estimate.

Usage:
    python code/improve.py ablate FD001          # one change at a time, 2 seeds each
    python code/improve.py final FD001 FD003     # chosen recipe, 5 seeds, ensemble
Results go to results/improve.json; final models to models/v2/.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import pdm

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'results', 'improve.json')
torch.set_num_threads(max(1, os.cpu_count() or 1))


# ---------------------------------------------------------------- data
def load_v2(subset, window=30, cap=125, alpha=None, add_cycle=False, val_frac=0.2, seed=0):
    """pdm.load plus two optional inputs: exponentially smoothed sensors and the engine's age."""
    train, test = pdm.read(f'train_{subset}.txt'), pdm.read(f'test_{subset}.txt')
    rul_test = np.loadtxt(f'{pdm.DATA_DIR}/RUL_{subset}.txt')
    train['rul'] = (train.groupby('unit')['cycle'].transform('max') - train['cycle']).clip(upper=cap)

    feats = list(pdm.SENSORS)
    for df in (train, test):
        if alpha:   # causal smoothing: each value uses only the past, so nothing leaks from the future
            df[pdm.SENSORS] = df.groupby('unit')[pdm.SENSORS].transform(lambda s: s.ewm(alpha=alpha, adjust=False).mean())
        if add_cycle:
            df['age'] = df['cycle'] / 400.0
    if add_cycle:
        feats.append('age')

    units = train['unit'].unique()
    val_units = np.random.default_rng(seed).choice(units, int(len(units) * val_frac), replace=False)
    fit = train[~train['unit'].isin(val_units)]
    lo, hi = fit[feats].min(), fit[feats].max()
    scale = lambda df: ((df[feats] - lo) / (hi - lo + 1e-8)).values.astype(np.float32)

    def windows(df):
        X, y = [], []
        for _, g in df.groupby('unit'):
            v, r = scale(g), g['rul'].values
            if len(v) < window:
                v = np.vstack([np.repeat(v[:1], window - len(v), 0), v]); r = np.concatenate([np.repeat(r[:1], window - len(r)), r])
            for end in range(window, len(v) + 1):
                X.append(v[end - window:end]); y.append(r[end - 1])
        return np.stack(X), np.array(y, np.float32)

    def last_windows(df):
        X = []
        for _, g in df.groupby('unit'):
            v = scale(g)
            if len(v) < window:
                v = np.vstack([np.repeat(v[:1], window - len(v), 0), v])
            X.append(v[-window:])
        return np.stack(X)

    Xtr, ytr = windows(fit)
    Xva, yva = windows(train[train['unit'].isin(val_units)])
    return Xtr, ytr, Xva, yva, last_windows(test), np.minimum(rul_test, cap).astype(np.float32), feats


# ---------------------------------------------------------------- training
def train_v2(data, seed, epochs=150, patience=25, batch=256, lr=1e-3, loss='mse', sched=False, y_scale=125.0):
    torch.manual_seed(seed); np.random.seed(seed)
    Xtr, ytr, Xva, yva, Xte, yte, feats = data
    model = pdm.CNNLSTMAttention(Xtr.shape[2])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    lr_sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=6) if sched else None
    lossf = nn.HuberLoss(delta=0.1) if loss == 'huber' else nn.MSELoss()   # delta 0.1 of 125 = 12.5 cycles
    Xtr_t, ytr_t, Xva_t = torch.from_numpy(Xtr), torch.from_numpy(ytr / y_scale), torch.from_numpy(Xva)

    def predict(X):
        model.eval()
        with torch.no_grad():
            return torch.cat([model(X[i:i + 4096]) for i in range(0, len(X), 4096)]).numpy() * y_scale

    best, best_state, wait, t0 = np.inf, None, 0, time.time()
    for ep in range(epochs):
        model.train()
        perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), batch):
            idx = perm[i:i + batch]
            opt.zero_grad(); lossf(model(Xtr_t[idx]), ytr_t[idx]).backward(); opt.step()
        val = float(np.sqrt(np.mean((predict(Xva_t) - yva) ** 2)))
        if lr_sched:
            lr_sched.step(val)
        if val < best - 1e-4:
            best, wait, best_state = val, 0, {k: v.clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    pred = np.clip(predict(torch.from_numpy(Xte)), 0, None)
    return {'val_rmse': best, 'pred': pred, 'epochs': ep + 1, 'time_s': time.time() - t0, 'model': model}


def scores(pred, true):
    return {'rmse': pdm.rmse(pred, true), 'score': pdm.phm_score(pred, true)}


def save(key, value):
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    res[key] = value
    json.dump(res, open(OUT, 'w'), indent=1)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- runs
ABLATIONS = {   # one change at a time against the report's recipe
    'baseline':          dict(),
    'lr schedule':       dict(train=dict(sched=True)),
    'huber loss':        dict(train=dict(loss='huber')),
    'smoothing 0.3':     dict(data=dict(alpha=0.3)),
    'engine age input':  dict(data=dict(add_cycle=True)),
    'window 40':         dict(data=dict(window=40)),
}


def run_config(subset, cfg, seeds):
    data = load_v2(subset, **cfg.get('data', {}))
    runs = [train_v2(data, s, **cfg.get('train', {})) for s in seeds]
    yte = data[5]
    ens = np.mean([r['pred'] for r in runs], axis=0)
    return {'val_rmse': float(np.mean([r['val_rmse'] for r in runs])),
            'test_rmse_each': [round(scores(r['pred'], yte)['rmse'], 3) for r in runs],
            'test_rmse_mean': float(np.mean([scores(r['pred'], yte)['rmse'] for r in runs])),
            'ensemble': scores(ens, yte), 'epochs': [r['epochs'] for r in runs],
            'time_s': float(np.mean([r['time_s'] for r in runs]))}, runs, data


if __name__ == '__main__':
    mode, subsets = sys.argv[1], sys.argv[2:]
    if mode == 'ablate':
        for subset in subsets:
            for name, cfg in ABLATIONS.items():
                r, _, _ = run_config(subset, cfg, seeds=[0, 1])
                save(f'ablate/{subset}/{name}', r)
                log(subset, f'{name:<18}', f"val {r['val_rmse']:.2f}", f"test {r['test_rmse_mean']:.2f}", f"epochs {r['epochs']}")
    elif mode == 'final':
        cfg = json.loads(os.environ.get('EP_RECIPE', '{}'))
        for subset in subsets:
            r, runs, data = run_config(subset, cfg, seeds=[0, 1, 2, 3, 4])
            r['recipe'] = cfg
            save(f'final/{subset}', r)
            d = os.path.join(ROOT, 'models', 'v2'); os.makedirs(d, exist_ok=True)
            for i, run in enumerate(runs):
                torch.save(run['model'].state_dict(), os.path.join(d, f'{subset}_seed{i}.pt'))
            json.dump({'recipe': cfg, 'features': data[6]}, open(os.path.join(d, f'{subset}_recipe.json'), 'w'), indent=1)
            log(subset, 'final', f"val {r['val_rmse']:.2f}", f"test mean {r['test_rmse_mean']:.2f}",
                f"ensemble {r['ensemble']['rmse']:.2f} / PHM08 {r['ensemble']['score']:.0f}")

"""Figures for the report from the FD001 seed-0 CNN-LSTM + Attention model.

Run on its own to rebuild the figures without rerunning every experiment:
    python make_figures.py    (retrains the seed-0 model, ~1 min)
"""
import json
import os
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import pdm

plt.rcParams.update({'font.family': 'serif', 'font.size': 11})
Y_SCALE = 125.0  # models output RUL / 125, see pdm.train_dl


def make(model, data, pred, true, hist, fig_dir):
    o = np.argsort(true)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.plot(true[o], 'o-', ms=3, label='Actual RUL', color='#333')
    ax.plot(pred[o], 's', ms=3, label='Predicted RUL (CNN-LSTM-Att)', color='#8B0000', alpha=.7)
    ax.set_xlabel('Test engine (sorted by actual RUL)'); ax.set_ylabel('RUL (cycles)'); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f'{fig_dir}/fig_pred_vs_actual.png', dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    e = np.arange(1, len(hist['train']) + 1)
    ax.plot(e, hist['train'], label='Training', color='#333'); ax.plot(e, hist['val'], label='Validation', color='#8B0000')
    ax.set_xlabel('Epoch'); ax.set_ylabel('MSE loss (cycles²)'); ax.set_yscale('log'); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f'{fig_dir}/fig_loss_curves.png', dpi=160); plt.close(fig)

    # Full-life trajectory of one held-out validation engine (validation engines run to failure).
    train = pdm.read('train_FD001.txt')
    units = train['unit'].unique()
    val_units = np.sort(np.random.default_rng(0).choice(units, int(len(units) * 0.2), replace=False))
    _, _, Xva, yva, _, _ = data
    lengths = {u: len(train[train['unit'] == u]) - 30 + 1 for u in val_units}
    eng = val_units[0]
    start, n = 0, lengths[eng]
    model.eval()
    with torch.no_grad():
        vp = model(torch.from_numpy(Xva[start:start + n])).numpy() * Y_SCALE
        model(torch.from_numpy(Xva))  # fills last_attention for every validation window
        att = model.last_attention.numpy()
    cyc = train[train['unit'] == eng]['cycle'].values[29:]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.plot(cyc, yva[start:start + n], label='Actual RUL (capped at 125)', color='#333', lw=2)
    ax.plot(cyc, vp, label='Predicted RUL', color='#8B0000', alpha=.85)
    ax.set_xlabel('Operating cycle'); ax.set_ylabel('RUL (cycles)'); ax.set_title(f'Validation engine {eng}', fontsize=10)
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f'{fig_dir}/fig_engine_trajectory.png', dpi=160); plt.close(fig)

    mean_att = att.mean(0)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.bar(np.arange(-len(mean_att) + 1, 1), mean_att, color='#8B0000')
    ax.set_xlabel('Time step within window (0 = current cycle)'); ax.set_ylabel('Mean attention weight'); ax.grid(alpha=.3, axis='y')
    fig.tight_layout(); fig.savefig(f'{fig_dir}/fig_attention.png', dpi=160); plt.close(fig)

    d = pred - true
    return {'val_engine': int(eng), 'val_engine_rmse': float(np.sqrt(np.mean((vp - yva[start:start + n]) ** 2))),
            'attention_last_share': float(mean_att[-1]), 'attention_last5_share': float(mean_att[-5:].sum()),
            'attention_mean': mean_att.tolist(),
            'test_mae': float(np.mean(np.abs(d))), 'test_late_share': float(np.mean(d > 0)),
            'test_rmse_true_ge_100': float(np.sqrt(np.mean(d[true >= 100] ** 2))),
            'test_rmse_true_lt_50': float(np.sqrt(np.mean(d[true < 50] ** 2))),
            'test_abs_err_gt_20': int(np.sum(np.abs(d) > 20))}


if __name__ == '__main__':
    torch.set_num_threads(4)
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    data = pdm.load('FD001')
    r = pdm.train_dl('CNN-LSTM + Attention', data, 0)
    print('seed-0 test RMSE', round(r['rmse'], 2))
    figs = make(r['model'], data, np.array(r['pred']), data[5], r['history'], f'{root}/report')
    path = f'{root}/results/results.json'
    res = json.load(open(path)); res['figures'] = figs; json.dump(res, open(path, 'w'), indent=1)
    print({k: v for k, v in figs.items() if k != 'attention_mean'})

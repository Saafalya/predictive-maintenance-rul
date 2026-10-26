# AI-Based Predictive Maintenance Using Multivariate Sensor Data

Deep Learning ESE project (CA3), Symbiosis Institute of Technology, Pune, AY 2026-27.

**Team:** Saafalya Sengupta (24070126158) and Ribhav Dhankani (24070126150), AIML C1
**Faculty Coordinator:** Dr. Shrikrishna Kolhar

We predict the **Remaining Useful Life (RUL)** of turbofan engines from 14 sensor channels in the NASA C-MAPSS dataset, and compare classical ML baselines with deep sequence models under one shared pipeline.

| Model | Type |
|---|---|
| Linear Regression | baseline |
| Random Forest (200 trees) | baseline |
| 1D-CNN | deep |
| Stacked LSTM | deep |
| CNN-LSTM + additive attention | deep (proposed) |

## Results (test set, mean ± std over 5 seeds)

| Model | RMSE FD001 | PHM08 FD001 | RMSE FD003 | PHM08 FD003 |
|---|---|---|---|---|
| Linear Regression | 14.99 | 374 | 16.26 | 471 |
| Random Forest | 15.91 ± 0.16 | 570 ± 14 | 17.43 ± 0.16 | 1,096 ± 48 |
| 1D-CNN | 13.82 ± 0.19 | 344 ± 21 | 13.78 ± 0.48 | 477 ± 69 |
| LSTM | 13.64 ± 0.52 | **305 ± 46** | 12.36 ± 0.67 | **261 ± 23** |
| CNN-LSTM + Attention | **13.37 ± 0.35** | 337 ± 23 | **11.88 ± 0.70** | 303 ± 79 |

Lower is better. Full output in `results/results.json`, run log in `results/run_log.txt`.

## Pipeline

Raw sensors → drop 7 constant sensors → min-max scale (fit on train only) → RUL capped at 125 → 30-cycle sliding windows → model → RUL → maintenance decision.

Metrics: RMSE and the asymmetric PHM08 score (late predictions are penalised more).

## Layout

```
code/pdm.py               data pipeline, models, training loop
code/run_experiments.py   all experiments + figures -> results/results.json
code/make_figures.py      rebuild figures only (retrains the seed-0 model, ~1 min)
code/app.py               local website (Streamlit) for exploring predictions
models/                   saved seed-0 CNN-LSTM + Attention weights for FD001 and FD003
data/CMAPSS/              FD001 and FD003 (NASA C-MAPSS)
report/                   Word report, its build script and figures
results/                  experiment outputs
```

## Run

On Windows, double-click `start.bat` for a menu. Or:

```bash
pip install -r requirements.txt
python code/run_experiments.py      # ~75 min on a 4-core CPU, no GPU needed
cd report && npm install docx && node build_report.js
```

## Website

Double-click `run_website.bat` on Windows, or run:

```bash
pip install -r requirements.txt
streamlit run code/app.py
```

It opens at http://localhost:8501 and has four tabs:

- **Check an engine**: the predicted cycles left on a dial, a maintenance call, and a **3D cutaway of the turbofan** you can turn with the mouse or arrow keys. Each station (fan, compressors, combustor, turbines) is tinted by how far its own sensors have drifted from a healthy engine; hover a station for its readings, or use *Exploded view* to pull the stations apart. Below it: the prediction over the engine's history, where the attention layer looked, and each sensor's history against its healthy baseline. *Download work order* saves a text work card for the engine.
- **Fleet board**: every test engine sorted by urgency, predicted against actual, and the shop visit queue.
- **Score your own data**: upload a C-MAPSS-format sensor file and download predictions.
- **Model comparison**: the five-model results from `results/results.json`.

Drift is the mean of a sensor's last 10 cycles compared with the mean and spread of the first 30 cycles of every training engine. Sensor names, units and stations follow Saxena et al. (2008).

Bundled in `code/static`: the Geist typeface (SIL Open Font License) and three.js r149 (MIT), so the site works offline.

## Dataset

A. Saxena, K. Goebel, D. Simon, N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," PHM 2008. NASA Prognostics Center of Excellence Data Repository.

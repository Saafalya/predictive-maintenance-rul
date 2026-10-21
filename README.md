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

## Pipeline

Raw sensors → drop 7 constant sensors → min-max scale (fit on train only) → RUL capped at 125 → 30-cycle sliding windows → model → RUL → maintenance decision.

Metrics: RMSE and the asymmetric PHM08 score (late predictions are penalised more).

## Layout

```
code/pdm.py               data pipeline, models, training loop
code/run_experiments.py   all experiments + figures -> results/results.json
data/CMAPSS/              FD001 and FD003 (NASA C-MAPSS)
report/                   Word report, its build script and figures
results/                  experiment outputs
```

## Run

```bash
pip install -r requirements.txt
python code/run_experiments.py      # ~40 min on a 4-core CPU, no GPU needed
cd report && npm install docx && node build_report.js
```

## Dataset

A. Saxena, K. Goebel, D. Simon, N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," PHM 2008. NASA Prognostics Center of Excellence Data Repository.

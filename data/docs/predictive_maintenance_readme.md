# Predictive Maintenance with Early Warning and Drift Detection

![Project Banner](docs/graphics/project_banner.png)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Sequence%20Models-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Tree%20Explainability-F4A261?style=for-the-badge)
![NASA C-MAPSS](https://img.shields.io/badge/NASA-C--MAPSS%20FD001-264653?style=for-the-badge)
![R&D](https://img.shields.io/badge/Focus-Early%20Warning%20%2B%20Drift-2A9D8F?style=for-the-badge)

This project studies whether early-warning failure prediction improves when supervised models, anomaly detection, uncertainty estimates, and drift-aware monitoring are combined in one operator-facing pipeline. It uses NASA C-MAPSS FD001, temporal window feature engineering, sequence models, anomaly scoring, uncertainty from ensemble disagreement, SHAP-based sensor importance, and drift monitoring over sensor distributions.

## Research question

**Can early-warning failure prediction be improved by combining supervised models, anomaly detection, and drift-aware monitoring?**

## What the project includes

- Temporal window feature engineering on multivariate sensor streams
- Early-warning labels for failure within a configurable horizon
- Remaining useful life proxy for lead-time analysis
- Supervised baselines: Logistic Regression, Random Forest, XGBoost
- Deep models: 1D CNN, GRU, Temporal CNN, Transformer
- Anomaly detection: Isolation Forest, One-Class SVM, PCA reconstruction error
- Uncertainty estimate from supervised ensemble disagreement
- Drift detection monitors over sensor distributions
- SHAP sensor importance for the tree model
- Operator-style Markdown/HTML reports

## Dataset

The demo run uses **NASA C-MAPSS FD001** with a `30-cycle` early-warning horizon and `20-step` temporal windows.

## Demo snapshot

![F1 Snapshot](docs/graphics/f1_snapshot.png)

![Tradeoff Snapshot](docs/graphics/tradeoff_snapshot.png)

![Model F1 Comparison](outputs/demo/model_f1_comparison.png)

![Lead Time vs False Alarm](outputs/demo/leadtime_falsealarm.png)

### Headline findings from the generated demo run

- The best single supervised model was `XGBoost` with `F1 = 0.787`, `AUROC = 0.996`, `lead time = 6.83 cycles`, and `false alarm rate = 0.004`.
- The best deep model was the `GRU` with `F1 = 0.720` and `AUROC = 0.994`.
- The hybrid operator score, which fuses supervised probabilities, anomaly signal, and drift score, reached the best overall `F1 = 0.792` with `AUROC = 0.994`.
- `Isolation Forest` gave much earlier warnings (`41.23 cycles`) but with a noticeably higher false alarm rate (`0.049`), which is exactly the practical trade-off operators care about.
- The ensemble disagreement signal had a positive uncertainty-error correlation of `0.181`, so higher disagreement did align with more prediction failures.
- The drift monitors were moderately sensitive on injected shift scenarios, each reaching `0.462` sensitivity and `0.577` precision in the demo setup.

## Why this project is strong

- It goes beyond standard classification by combining early warning, anomaly detection, uncertainty, and drift.
- It frames results in operator-facing terms like lead time and false alarm rate instead of only accuracy.
- It includes interpretability through SHAP and sensor-level ranking.
- It looks like a real monitoring system, not just an offline model benchmark.

## Model comparison

| Category | Model | F1 | AUROC | Lead time | False alarm rate |
| --- | --- | ---: | ---: | ---: | ---: |
| Supervised baseline | Logistic Regression | 0.772 | 0.996 | 6.95 | 0.005 |
| Supervised baseline | Random Forest | 0.748 | 0.996 | 5.61 | 0.003 |
| Supervised baseline | XGBoost | 0.787 | 0.996 | 6.83 | 0.004 |
| Deep sequence model | 1D CNN | 0.625 | 0.973 | 9.81 | 0.022 |
| Deep sequence model | GRU | 0.720 | 0.994 | 12.67 | 0.019 |
| Deep sequence model | Temporal CNN | 0.613 | 0.976 | 10.39 | 0.024 |
| Deep sequence model | Transformer | 0.688 | 0.993 | 12.70 | 0.022 |
| Anomaly detection | Isolation Forest | 0.446 | 0.953 | 41.23 | 0.049 |
| Anomaly detection | One-Class SVM | 0.366 | 0.921 | 111.38 | 0.072 |
| Anomaly detection | PCA Reconstruction | 0.097 | 0.584 | 112.70 | 0.099 |
| Hybrid operator score | Supervised + Anomaly + Drift Fusion | 0.792 | 0.994 | 6.97 | 0.007 |

## Uncertainty, drift, and interpretability

### Uncertainty quality

![Uncertainty Quality](outputs/demo/uncertainty_quality.png)

### Drift timeline

![Drift Timeline](outputs/demo/drift_timeline.png)

### Drift monitor sensitivity

![Drift Monitor Sensitivity](outputs/demo/drift_monitor_sensitivity.png)

### SHAP sensor importance

![Sensor Importance](outputs/demo/sensor_importance.png)

These plots make the project feel operational:

- uncertainty is tied to ensemble disagreement rather than only softmax confidence
- drift is tracked over the test stream instead of assumed away
- SHAP groups the tree model's most influential features back to sensors engineers recognize

## Operator-style visuals

### XGBoost confusion matrix

![XGBoost Confusion](outputs/demo/xgboost_confusion.png)

### Hybrid fusion confusion matrix

![Hybrid Confusion](outputs/demo/hybrid_confusion.png)

### Failure window visualization

![Failure Window Visualization](outputs/demo/failure_window_visualization.png)

## Project structure

| Path | Purpose |
| --- | --- |
| `src/pm_early_warning/data.py` | NASA C-MAPSS loading and RUL construction |
| `src/pm_early_warning/features.py` | temporal windowing and engineered sensor features |
| `src/pm_early_warning/models.py` | supervised models, anomaly detectors, and sequence networks |
| `src/pm_early_warning/monitoring.py` | drift scoring and uncertainty helpers |
| `src/pm_early_warning/pipeline.py` | end-to-end experiment orchestration |
| `src/pm_early_warning/reporting.py` | plots and operator report generation |
| `notebooks/predictive_maintenance_early_warning.ipynb` | showcase notebook |
| `outputs/demo/` | generated tables, plots, and summary reports |

## CLI usage

```bash
pm-early-warning run-demo configs/demo.yaml
```

## Local setup

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\pm-early-warning.exe run-demo configs\demo.yaml
```

## Testing

```powershell
.venv\Scripts\python.exe -m pytest
```

## Docker

```powershell
docker build -t pm-early-warning .
docker run --rm pm-early-warning
```

## Demo outputs in this repo

- Model comparison CSV: [outputs/demo/model_comparison.csv](outputs/demo/model_comparison.csv)
- Drift monitor CSV: [outputs/demo/drift_monitor_comparison.csv](outputs/demo/drift_monitor_comparison.csv)
- Operator summary Markdown: [outputs/demo/operator_summary.md](outputs/demo/operator_summary.md)
- Operator summary HTML: [outputs/demo/operator_summary.html](outputs/demo/operator_summary.html)
- Notebook: [notebooks/predictive_maintenance_early_warning.ipynb](notebooks/predictive_maintenance_early_warning.ipynb)

## Notes on the demo configuration

- The checked-in demo uses `stride = 2` and a compact deep-model training budget so the full pipeline can be rerun on CPU in a reasonable time.
- The anomaly and drift sections are intentionally included even when they do not maximize F1, because the project is about operator usefulness and monitoring, not just headline classification performance.

## Resume-ready framing

**Predictive Maintenance with Early Warning and Drift Detection**  
Built a drift-aware predictive maintenance pipeline on NASA C-MAPSS that combines temporal feature engineering, supervised failure prediction, anomaly detection, uncertainty estimation, SHAP interpretability, and operator-style reporting to study the trade-off between lead time, false alarms, and predictive quality.

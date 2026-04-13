# Predictive Maintenance with Early Warning and Drift Detection

Generated at: `2026-04-10T23:58:03.514251+00:00`

## Model Comparison

| category              | model_name                          |   accuracy |   precision |   recall |       f1 |    auroc |   lead_time_cycles |   false_alarm_rate |   brier_score |   uncertainty_corr | notes                                                                         |
|:----------------------|:------------------------------------|-----------:|------------:|---------:|---------:|---------:|-------------------:|-------------------:|--------------:|-------------------:|:------------------------------------------------------------------------------|
| anomaly_detection     | Isolation Forest                    |   0.945244 |   0.318766  | 0.742515 | 0.446043 | 0.953099 |              41.23 |         0.0485526  |    0.0470993  |          nan       | Thresholded anomaly score treated as alert probability proxy.                 |
| anomaly_detection     | One-Class SVM                       |   0.922489 |   0.241843  | 0.754491 | 0.366279 | 0.92057  |             111.38 |         0.0723708  |    0.0641394  |          nan       | Thresholded anomaly score treated as alert probability proxy.                 |
| anomaly_detection     | PCA Reconstruction                  |   0.881067 |   0.0627178 | 0.215569 | 0.097166 | 0.583639 |             112.7  |         0.0985709  |    0.0975961  |          nan       | Thresholded anomaly score treated as alert probability proxy.                 |
| deep_sequence_model   | GRU                                 |   0.979022 |   0.596078  | 0.91018  | 0.720379 | 0.99374  |              12.67 |         0.0188714  |    0.01536    |          nan       |                                                                               |
| deep_sequence_model   | Transformer                         |   0.975644 |   0.555147  | 0.904192 | 0.687927 | 0.993146 |              12.7  |         0.0221693  |    0.0171744  |          nan       |                                                                               |
| deep_sequence_model   | Temporal CNN                        |   0.970311 |   0.5       | 0.790419 | 0.612529 | 0.97623  |              10.39 |         0.0241847  |    0.0213506  |          nan       |                                                                               |
| deep_sequence_model   | 1D CNN                              |   0.972089 |   0.519841  | 0.784431 | 0.625298 | 0.972932 |               9.81 |         0.0221693  |    0.0213229  |          nan       |                                                                               |
| hybrid_operator_score | Supervised + Anomaly + Drift Fusion |   0.987556 |   0.786982  | 0.796407 | 0.791667 | 0.993835 |               6.97 |         0.00659582 |    0.0178921  |            0.18125 | Weighted ensemble of supervised probability, anomaly signal, and drift score. |
| supervised_baseline   | Logistic Regression                 |   0.9872   |   0.818792  | 0.730539 | 0.772152 | 0.996115 |               6.95 |         0.00494687 |    0.0091099  |          nan       |                                                                               |
| supervised_baseline   | Random Forest                       |   0.986844 |   0.866142  | 0.658683 | 0.748299 | 0.996008 |               5.61 |         0.00311469 |    0.00898524 |          nan       |                                                                               |
| supervised_baseline   | XGBoost                             |   0.988267 |   0.853147  | 0.730539 | 0.787097 | 0.996003 |               6.83 |         0.00384756 |    0.008913   |          nan       |                                                                               |

## Drift Monitor Comparison

| monitor_name       |   sensitivity |   precision |   mean_score_clean |   mean_score_shifted |
|:-------------------|--------------:|------------:|-------------------:|---------------------:|
| PSI Drift Monitor  |      0.461667 |    0.577083 |           0.245751 |              0.29195 |
| Mean Shift Monitor |      0.461667 |    0.577083 |           0.245751 |              0.29195 |
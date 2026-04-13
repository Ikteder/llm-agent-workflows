# Model Export, Validation, and Inference Benchmarking Toolkit Demo

## Verification Summary

| model_key           | format_name   |   max_abs_error |   mean_abs_error |   max_rel_error | passed   |
|:--------------------|:--------------|----------------:|-----------------:|----------------:|:---------|
| distilgpt2          | npz           |     0           |      0           |     0           | True     |
| efficientnet-b0     | npz           |     0           |      0           |     0           | True     |
| efficientnet-b0     | onnx          |     3.30343e-20 |      7.3638e-21  |     3.30343e-16 | True     |
| efficientnet-b0     | torchscript   |     0           |      0           |     0           | True     |
| logistic-regression | npz           |     1.19209e-06 |      1.76906e-07 |     8.52532e-06 | True     |
| logistic-regression | onnx          |     1.60933e-06 |      2.79897e-07 |     0.000662335 | True     |
| mobilenetv3         | npz           |     0           |      0           |     0           | True     |
| mobilenetv3         | onnx          |     3.67761e-16 |      8.59279e-17 |     3.67761e-12 | True     |
| mobilenetv3         | torchscript   |     0           |      0           |     0           | True     |
| resnet18            | npz           |     0           |      0           |     0           | True     |
| resnet18            | onnx          |     2.6226e-06  |      5.79042e-07 |     0.000604989 | True     |
| resnet18            | torchscript   |     0           |      0           |     0           | True     |
| xgboost             | npz           |     0           |      0           |     0           | True     |
| xgboost             | onnx          |     8.56817e-08 |      4.05125e-08 |     2.38925e-06 | True     |

## Benchmark Summary

| model_key           | format_name   | device   |   batch_size |   latency_ms |   throughput_items_per_sec |   peak_rss_mb |   model_size_mb |
|:--------------------|:--------------|:---------|-------------:|-------------:|---------------------------:|--------------:|----------------:|
| distilgpt2          | baseline      | cpu      |            1 |     31.7161  |                    31.5297 |      1054.02  |   309.686       |
| distilgpt2          | npz           | cpu      |            1 |     38.0399  |                    26.2882 |      1057.56  |   422.885       |
| efficientnet-b0     | baseline      | cpu      |            1 |     50.2415  |                    19.9039 |       839.797 |    20.4535      |
| efficientnet-b0     | npz           | cpu      |            1 |     67.4583  |                    14.824  |       908.984 |    18.5053      |
| efficientnet-b0     | onnx          | cpu      |            1 |     31.4262  |                    31.8206 |       908.863 |    20.0704      |
| efficientnet-b0     | torchscript   | cpu      |            1 |     45.5073  |                    21.9745 |       849.523 |    20.9616      |
| logistic-regression | baseline      | cpu      |            8 |      0.11091 |                 72130.6    |       471.707 |     0.000902176 |
| logistic-regression | npz           | cpu      |            8 |      0.01644 |                486618      |       471.855 |     0.000685692 |
| logistic-regression | onnx          | cpu      |            8 |      0.02501 |                319872      |       471.855 |     0.000650406 |
| mobilenetv3         | baseline      | cpu      |            1 |     40.727   |                    24.5537 |       705.07  |    21.1074      |
| mobilenetv3         | npz           | cpu      |            1 |     28.5588  |                    35.0155 |       757.82  |    19.352       |
| mobilenetv3         | onnx          | cpu      |            1 |     15.9411  |                    62.7311 |       757.211 |    20.8562      |
| mobilenetv3         | torchscript   | cpu      |            1 |     24.6031  |                    40.6453 |       708.914 |    21.4887      |
| resnet18            | baseline      | cpu      |            1 |     49.7229  |                    20.1115 |       646.809 |    44.6654      |
| resnet18            | npz           | cpu      |            1 |     47.0423  |                    21.2575 |       701.406 |    41.3002      |
| resnet18            | onnx          | cpu      |            1 |     25.8069  |                    38.7494 |       701.359 |    44.5687      |
| resnet18            | torchscript   | cpu      |            1 |     47.3301  |                    21.1282 |       651.648 |    44.7728      |
| xgboost             | baseline      | cpu      |            8 |      0.35093 |                 22796.6    |       474.316 |     0.045929    |
| xgboost             | npz           | cpu      |            8 |      0.70561 |                 11337.7    |       474.473 |     0.0100517   |
| xgboost             | onnx          | cpu      |            8 |      0.03139 |                254858      |       474.465 |     0.016078    |

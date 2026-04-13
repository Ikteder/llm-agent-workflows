# Efficient and Robust Computer Vision Benchmark

## Leaderboard

```text
dataset_name      model_name      variant  accuracy  precision  recall     f1  auroc  latency_ms  throughput_items_per_sec  peak_rss_mb  model_size_mb  params_m  flops_g  robustness_drop
 BreastMNIST EfficientNet-B0     baseline    0.8846     0.8871  0.9649 0.9244 0.8916    687.9108                   46.5177    1438.3906         16.030     4.008    0.385           0.1143
 BreastMNIST     MobileNetV3     baseline    0.8526     0.8824  0.9211 0.9013 0.8555    395.1030                   80.9915    1430.2461         16.808     4.202    0.215           0.1934
 BreastMNIST     MobileNetV3 robust_train    0.8397     0.8618  0.9298 0.8945 0.8440    395.1030                   80.9915    1430.2461         16.808     4.202    0.215           0.0609
 BreastMNIST   ConvNeXt-Tiny     baseline    0.8397     0.8870  0.8947 0.8908 0.8505   2355.1397                   13.5873    1432.9727        111.281    27.820    4.455           0.1645
 BreastMNIST        ResNet18     baseline    0.8013     0.8374  0.9035 0.8692 0.8475    881.9079                   36.2850    1408.1211         44.706    11.177    1.824           0.0962
    CIFAR-10   ConvNeXt-Tiny     baseline    0.9267     0.9287  0.9267 0.9267 0.9961   2763.5438                   11.5793    1400.3047        111.281    27.820    4.455           0.2539
    CIFAR-10        ResNet18     baseline    0.8267     0.8294  0.8267 0.8267 0.9742    858.4901                   37.2747    1032.7266         44.706    11.177    1.824           0.3483
    CIFAR-10 EfficientNet-B0     baseline    0.8233     0.8258  0.8233 0.8232 0.9855    679.7808                   47.0740    1378.4141         16.030     4.008    0.385           0.2539
    CIFAR-10     MobileNetV3     baseline    0.8167     0.8215  0.8167 0.8152 0.9835    379.7421                   84.2677    1108.8047         16.808     4.202    0.215           0.2650
    CIFAR-10     MobileNetV3 robust_train    0.7833     0.7889  0.7833 0.7799 0.9769    379.7421                   84.2677    1108.8047         16.808     4.202    0.215           0.1544
```

## Robustness Drop

```text
dataset_name      model_name      variant  accuracy_drop
 BreastMNIST   ConvNeXt-Tiny     baseline         0.1645
 BreastMNIST EfficientNet-B0     baseline         0.1143
 BreastMNIST     MobileNetV3     baseline         0.1934
 BreastMNIST     MobileNetV3 robust_train         0.0609
 BreastMNIST        ResNet18     baseline         0.0962
    CIFAR-10   ConvNeXt-Tiny     baseline         0.2539
    CIFAR-10 EfficientNet-B0     baseline         0.2539
    CIFAR-10     MobileNetV3     baseline         0.2650
    CIFAR-10     MobileNetV3 robust_train         0.1544
    CIFAR-10        ResNet18     baseline         0.3483
```

## Ablation

```text
dataset_name  model_name  baseline_accuracy  robust_accuracy  baseline_robustness_drop  robust_robustness_drop
    CIFAR-10 MobileNetV3             0.8167           0.7833                    0.2650                  0.1544
 BreastMNIST MobileNetV3             0.8526           0.8397                    0.1934                  0.0609
```
# Efficient and Robust Computer Vision Benchmark

![Project Banner](docs/graphics/project_banner.png)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Backbone%20Benchmark-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![timm](https://img.shields.io/badge/timm-Pretrained%20Vision-0F4C81?style=for-the-badge)
![Focus](https://img.shields.io/badge/Focus-Accuracy%20%2B%20Robustness%20%2B%20Efficiency-2A9D8F?style=for-the-badge)

This project compares modern computer vision backbones under three pressures that matter in practice: predictive quality, inference efficiency, and robustness to realistic corruptions. Instead of stopping at a single clean-test accuracy number, it benchmarks how models behave under Gaussian noise, blur, brightness and contrast shifts, cutout, and JPEG compression, then adds a corruption-robust training ablation to study the trade-off more honestly.

## Research question

**Which vision backbones provide the best trade-off between predictive performance, inference efficiency, and robustness under realistic input perturbations?**

## Datasets

- `CIFAR-10` for a classic multiclass benchmark
- `BreastMNIST` for applied medical relevance and cleaner binary AUROC / confusion-matrix analysis

I chose `BreastMNIST` instead of `ChestMNIST` for the secondary dataset so the benchmark could stay directly comparable, lightweight on CPU, and still support clear confusion matrices and AUROC reporting.

## Models compared

- `ResNet18`
- `MobileNetV3`
- `EfficientNet-B0`
- `ConvNeXt-Tiny`

## Stronger research angle

This repo uses **corruption-robust training** as the deeper research angle. A `MobileNetV3` ablation is retrained with corruption-augmented examples at the probe-training stage and then compared against the baseline on both datasets.

## Experimental setup

- pretrained backbones from `timm`
- frozen feature extraction
- logistic-regression linear probes on extracted features
- clean evaluation plus six corruption families
- efficiency benchmarking with latency, throughput, peak RSS, parameter count, FLOPs, and model size

This is intentionally honest and laptop-runnable: the benchmark focuses on comparative inference and robustness behavior rather than pretending to fully fine-tune four large backbones on CPU.

## Demo snapshot

![Snapshot Cards](docs/graphics/snapshot_cards.png)

![Latency vs Accuracy](outputs/demo/latency_vs_accuracy.png)

![Model Size vs Performance](outputs/demo/model_size_vs_performance.png)

![Robustness Drop](outputs/demo/robustness_drop_comparison.png)

## Headline findings from the generated demo run

- Best clean `CIFAR-10` result was `ConvNeXt-Tiny` with `accuracy = 0.927` and `F1 = 0.927`.
- Best clean `BreastMNIST` result was `EfficientNet-B0` with `accuracy = 0.885`, `F1 = 0.924`, and `AUROC = 0.892`.
- Fastest model in the benchmark was `MobileNetV3`, reaching about `84.27 items/sec` on CIFAR-style inference and `80.99 items/sec` on BreastMNIST.
- The corruption-robust training ablation materially helped `MobileNetV3`:
  - `CIFAR-10` robustness drop improved from `0.265` to `0.154`
  - `BreastMNIST` robustness drop improved from `0.193` to `0.061`
- The robustness gain came with a modest clean-accuracy trade-off, which is exactly the kind of deployment decision the benchmark is designed to expose.
- `ConvNeXt-Tiny` delivered the strongest raw performance but was by far the heaviest model, at `111.281 MB`, `27.82M` parameters, and the slowest latency profile.

## Leaderboard highlights

| Dataset | Model | Variant | Accuracy | F1 | AUROC | Latency ms | Size MB | Robustness drop |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CIFAR-10 | ConvNeXt-Tiny | baseline | 0.927 | 0.927 | 0.996 | 2763.54 | 111.281 | 0.254 |
| CIFAR-10 | ResNet18 | baseline | 0.827 | 0.827 | 0.974 | 858.49 | 44.706 | 0.348 |
| CIFAR-10 | EfficientNet-B0 | baseline | 0.823 | 0.823 | 0.985 | 679.78 | 16.030 | 0.254 |
| CIFAR-10 | MobileNetV3 | baseline | 0.817 | 0.815 | 0.984 | 379.74 | 16.808 | 0.265 |
| CIFAR-10 | MobileNetV3 | robust_train | 0.783 | 0.780 | 0.977 | 379.74 | 16.808 | 0.154 |
| BreastMNIST | EfficientNet-B0 | baseline | 0.885 | 0.924 | 0.892 | 687.91 | 16.030 | 0.114 |
| BreastMNIST | MobileNetV3 | baseline | 0.853 | 0.901 | 0.855 | 395.10 | 16.808 | 0.193 |
| BreastMNIST | MobileNetV3 | robust_train | 0.840 | 0.895 | 0.844 | 395.10 | 16.808 | 0.061 |
| BreastMNIST | ConvNeXt-Tiny | baseline | 0.840 | 0.891 | 0.850 | 2355.14 | 111.281 | 0.165 |
| BreastMNIST | ResNet18 | baseline | 0.801 | 0.869 | 0.848 | 881.91 | 44.706 | 0.096 |

## Robustness examples

### CIFAR-10 best-model confusion matrix
![CIFAR Confusion Matrix](outputs/demo/cifar-10/best_model_confusion_matrix.png)

### CIFAR-10 failure-case gallery
![CIFAR Failure Gallery](outputs/demo/cifar-10/failure_case_gallery.png)

### BreastMNIST best-model confusion matrix
![BreastMNIST Confusion Matrix](outputs/demo/breastmnist/best_model_confusion_matrix.png)

### BreastMNIST failure-case gallery
![BreastMNIST Failure Gallery](outputs/demo/breastmnist/failure_case_gallery.png)

## Ablation study

| Dataset | Model | Baseline accuracy | Robust-train accuracy | Baseline robustness drop | Robust-train robustness drop |
| --- | --- | ---: | ---: | ---: | ---: |
| CIFAR-10 | MobileNetV3 | 0.817 | 0.783 | 0.265 | 0.154 |
| BreastMNIST | MobileNetV3 | 0.853 | 0.840 | 0.193 | 0.061 |

Interpretation:

- On both datasets, robust training reduced corruption sensitivity substantially.
- On `BreastMNIST`, the trade-off was especially favorable: only a small clean-performance drop for a large robustness gain.
- On `CIFAR-10`, the robustness gain was strong, but the clean-accuracy penalty was more visible.

## Recommendation

- If you want the **strongest clean predictive performance**, choose `ConvNeXt-Tiny`.
- If you want the **best deployment-minded trade-off**, choose `MobileNetV3` with corruption-robust training.
- If you want the **best clean medical result with moderate size**, choose `EfficientNet-B0`.

Overall recommendation: **MobileNetV3 + robust training** is the most balanced option in this benchmark because it stays fast and compact while sharply improving corruption resilience.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/efficient_robust_cv/models/backbones.py` | pretrained backbone registry |
| `src/efficient_robust_cv/data.py` | CIFAR-10 and BreastMNIST loaders |
| `src/efficient_robust_cv/training/linear_probe.py` | feature extraction and linear-probe fitting |
| `src/efficient_robust_cv/robustness/corruptions.py` | corruption operators |
| `src/efficient_robust_cv/benchmarking/measure.py` | latency, throughput, and memory benchmarking |
| `src/efficient_robust_cv/reports/reporting.py` | charts, reports, confusion matrices, and galleries |
| `src/efficient_robust_cv/pipeline.py` | full experiment orchestration |
| `configs/demo.yaml` | showcase benchmark config |
| `outputs/demo/` | generated leaderboard, plots, reports, and galleries |

## Local setup

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
```

## Run the benchmark

```powershell
.venv\Scripts\robust-cv-bench.exe run-demo --config-path configs\demo.yaml
```

## Testing

```powershell
.venv\Scripts\python.exe -m pytest
```

## Docker

```powershell
docker build -t robust-cv-benchmark .
docker run --rm robust-cv-benchmark
```

## Demo outputs in this repo

- Leaderboard: [outputs/demo/leaderboard.csv](outputs/demo/leaderboard.csv)
- Robustness table: [outputs/demo/robustness_drop_table.csv](outputs/demo/robustness_drop_table.csv)
- Ablation summary: [outputs/demo/ablation_summary.csv](outputs/demo/ablation_summary.csv)
- HTML report: [outputs/demo/final_report.html](outputs/demo/final_report.html)
- Notebook: [notebooks/efficient_robust_cv_benchmark.ipynb](notebooks/efficient_robust_cv_benchmark.ipynb)

## Honest notes

- The benchmark uses **frozen pretrained backbones plus linear probes**, not full end-to-end fine-tuning.
- That was a deliberate choice to keep the benchmark reproducible on CPU while still producing meaningful architecture, efficiency, and robustness comparisons.
- The absolute numbers should be interpreted as **benchmark comparisons**, not as full dataset state-of-the-art claims.

## Resume-ready framing

**Efficient and Robust Computer Vision Benchmark**  
Built a research-style benchmarking framework comparing modern vision backbones across predictive performance, inference efficiency, and corruption robustness, with deployment-focused analysis on CIFAR-10 and BreastMNIST and an ablation showing how robustness training changes the accuracy-efficiency trade-off.

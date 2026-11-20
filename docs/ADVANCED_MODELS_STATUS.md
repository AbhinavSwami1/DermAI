# Advanced AI - Status

| Item | Status |
|---|---|
| Baseline CNNs (MobileNetV3-Large, EfficientNet-B0) | Implemented and evaluated |
| Advanced CNN: ConvNeXt-Tiny | **Trained and evaluated** (run `convnext_tiny_lr1e-4`, results below) |
| Transformer (ViT-B/16, Swin-T supported by `train_advanced.py`) | Not run |
| Ensemble (mean softmax, `compare_experiments.py --ensemble`) | Not evaluated: needs a second run of comparable quality |
| Learning-rate runs (1e-3, 1e-4, 1e-5) | Commands in `docs/EXPERIMENT_RUNBOOK.md`; not run |

## ConvNeXt-Tiny run
Same patient-level split, seed 42, preprocessing, weighted cross-entropy, Adam (lr 1e-4, wd 1e-4), ReduceLROnPlateau, early stopping (patience 5); all 27.8M parameters trainable, ImageNet-pretrained. Best checkpoint chosen by lowest validation loss (epoch 3 of 8 run; 1,176 s on the local device). Test split evaluated once with `--eval-test`.

| Metric | MobileNetV3-Large (fine-tuned, deployed) | ConvNeXt-Tiny |
|---|---|---|
| Validation accuracy | 61.22% | 66.20% |
| Validation macro F1 | 56.53% | 61.88% |
| Test accuracy | 57.39% | 60.43% |
| Test balanced accuracy | not recorded here | 66.33% |
| Test macro F1 | 51.02% | 60.84% |
| Test MEL F1 (10 images) | 28.57% | 64% (recall 8/10) |
| Inference per image | not recorded here | 15.3 ms |

ConvNeXt-Tiny per-class test results: ACK P 0.86 / R 0.57; BCC P 0.78 / R 0.54; MEL P 0.53 / R 0.80; NEV P 0.57 / R 0.88; SCC P 0.17 / R 0.49 (F1 0.25); SEK P 0.79 / R 0.70.

## Observations
- Overfitting: training accuracy reached 96% while validation accuracy was about 77%; validation loss rose from 0.81 (epoch 3) to 1.26 (epoch 8), so early stopping ended training. Validation macro F1 was higher at epoch 7 (66.9%) than at the saved epoch 3 (61.9%), but the selection rule (lowest validation loss) was fixed beforehand and was kept.
- The test accuracy difference (+3.0 points) is about the size of one standard error of a single accuracy estimate on 460 images (about 2 points); the models share the same images, so a paired test would be needed. Treat accuracy as inconclusive.
- The macro F1 difference (+9.8 points) comes largely from MEL, which has only 10 test images, and NEV. It is high-variance.
- SCC remains poor: precision 0.17. The model predicted SCC for 114 images although only 39 are SCC; 54 BCC and 40 ACK images were predicted as SCC. A possible cause is the class-weighted loss favouring rare classes at the expense of majority-class recall; this was not tested.
- Single run, single seed. No claim of clinical reliability.
- The deployed application still uses MobileNetV3-Large. Using ConvNeXt-Tiny would require changes to the inference and Grad-CAM services.

## Blocker for the remaining items
ViT/Swin and LR runs need further local training time; the scripts are ready and compile.

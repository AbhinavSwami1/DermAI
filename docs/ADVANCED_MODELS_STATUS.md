# Advanced AI - Status and Results

| Item | Status |
|---|---|
| Baseline CNNs (MobileNetV3-Large, EfficientNet-B0) | Implemented and evaluated |
| Advanced CNN (ConvNeXt-Tiny) | Trained and evaluated |
| Transformers (ViT-B/16, Swin-T) | Trained and evaluated |
| Ensemble (mean softmax of ConvNeXt-Tiny and ViT-B/16) | Evaluated on validation |
| Hyperparameter experiment (MobileNetV3-Large, lr 1e-3, 1e-4, 1e-5) | Run on validation |

All runs: same patient-level split (1,477 / 361 / 460), seed 42, preprocessing, weighted cross-entropy, Adam (weight decay 1e-4), ReduceLROnPlateau, early stopping (patience 5), ImageNet-pretrained weights, best epoch chosen by lowest validation loss. Models were compared on validation; the test split was evaluated once, only for ConvNeXt-Tiny and ViT-B/16.

## Results

| Run | Architecture | LR | Best / run epochs | Val acc | Val bal. acc | Val macro F1 | Test acc | Test macro F1 | ms per image | Params | Train min |
|---|---|---|---|---|---|---|---|---|---|---|---|
| vit_b16_lr1e-5 | vit_b_16 | 1e-05 | 5 / 10 | 71.75% | 69.63% | 66.04% | 67.39% | 62.46% | 32.9 | 85.8M | 27 |
| convnext_tiny_lr1e-4 | convnext_tiny | 0.0001 | 3 / 8 | 66.20% | 69.91% | 61.88% | 60.43% | 60.84% | 15.3 | 27.8M | 20 |
| swin_t_lr1e-4 | swin_t | 0.0001 | 3 / 8 | 64.82% | 64.52% | 61.74% | - | - | 19.3 | 27.5M | 16 |
| MobileNetV3-Large fine-tuned (deployed, earlier script) | mobilenet_v3_large | 1e-05 | 9 | 61.22% | - | 56.53% | 57.39% | 51.02% | - | 4.2M | - |

## Ensemble

Mean softmax of ConvNeXt-Tiny and ViT-B/16 on validation: accuracy 70.36%, macro F1 64.93%, versus ViT-B/16 alone 71.75% and 66.04%. The ensemble gave no validation gain, so it was not evaluated on the test split.

## ViT-B/16 on the test split (460 images)

| Class | Precision | Recall | F1 | Images |
|---|---|---|---|---|
| ACK | 0.73 | 0.78 | 0.75 | 146 |
| BCC | 0.80 | 0.62 | 0.70 | 169 |
| MEL | 0.60 | 0.60 | 0.60 | 10 |
| NEV | 0.70 | 0.82 | 0.75 | 49 |
| SCC | 0.21 | 0.31 | 0.25 | 39 |
| SEK | 0.67 | 0.70 | 0.69 | 47 |

Accuracy 67.39%, balanced accuracy 63.80%, macro F1 62.46%. Confusion matrix: `docs/figures/training/`.

## Paired comparison on test: ViT-B/16 versus ConvNeXt-Tiny

ViT-B/16 was right and ConvNeXt-Tiny wrong on 76 images; the reverse on 44. Exact McNemar test p = 0.0045. The accuracy difference is unlikely to be chance alone on this test set.
The comparison with the deployed MobileNetV3-Large (test accuracy 57.39%) is not paired because its per-image predictions were evaluated separately.

## Observations

- vit_b16_lr1e-5: training accuracy reached 97% while validation accuracy was 71% at the last epoch; validation loss was lowest at epoch 5, then rose. Early stopping ended training at epoch 10.
- convnext_tiny_lr1e-4: training accuracy reached 96% while validation accuracy was 77% at the last epoch; validation loss was lowest at epoch 3, then rose. Early stopping ended training at epoch 8.
- swin_t_lr1e-4: training accuracy reached 87% while validation accuracy was 76% at the last epoch; validation loss was lowest at epoch 3, then rose. Early stopping ended training at epoch 8.
- Best on validation macro F1: vit_b16_lr1e-5 (66.04%). Validation has 361 images (7 MEL, 23 SCC), so differences of a few points are within noise; each model is a single run with one seed.
- Validation scores of the selected models were optimistic: the test split gave lower values (see the table).
- Class imbalance and rare classes (MEL, SCC) remain the main limitation; per-class results are in the confusion matrices.

## Model selection

- Best research result (selected on validation, confirmed once on test): ViT-B/16.
- Deployed in the application: MobileNetV3-Large fine-tuned. ViT-B/16 is about 20 times larger (85.8M versus 4.2M parameters) and slower per image; Grad-CAM, calibration, tests and Docker setup are built on MobileNetV3-Large, and Grad-CAM for a transformer needs a different implementation.
- No claim of clinical reliability follows from these experiments.


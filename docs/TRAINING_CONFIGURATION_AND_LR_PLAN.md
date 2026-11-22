# DermAI - Current Training Configuration and Learning-Rate Experiment Plan

## 1. Current configuration (from repository docs/scripts)
| Item | Value |
|---|---|
| Architecture / checkpoint | MobileNetV3-Large, `best_mobilenet_v3_large_finetuned.pth` (epoch 9) |
| Pretrained | Yes (ImageNet) |
| Frozen / trainable | Backbone frozen by default; only `model.features[13:]` (`UNFREEZE_FROM = 13`) and the final classification layer `model.classifier[3]` are trainable; all other parameters are frozen in the fine-tuning script |
| Learning rate | Fine-tuning: 1e-5 (`LEARNING_RATE`); initial head training: 1e-4 (`ml/config.yaml`) |
| Batch size | 16 |
| Optimizer | Adam (`finetune_mobilenet_v3_large.py`) |
| Weight decay | 1e-4 |
| Epochs | Max 20 (`EPOCHS`); early stopping patience 5; best checkpoint at epoch 9 |
| Loss | Weighted cross-entropy (weights from training split only) |
| Scheduler / early stopping | ReduceLROnPlateau (patience 2), early stopping (patience 5) on val loss |
| Split | Patient-grouped: 1477 train / 361 val / 460 test |
| Seed | 42 |
| Validation metrics (fine-tuned) | Acc 61.22%, Macro F1 56.53% |
| Test metrics | Acc 57.39%, Macro F1 51.02% |
| Per-epoch training loss/accuracy | Not recorded in this document; see `ml/outputs/.../training_history` |

## 2. Overfitting / underfitting assessment
Cannot be completed from this repository alone. Training-history files and curves live under `ml/outputs/` (not committed). Compare train vs validation loss from those files before stating a conclusion. The drop from validation (61.22%) to test (57.39%) accuracy is small and not by itself evidence of overfitting.

## 3. Proposed learning-rate experiments
Same architecture (MobileNetV3-Large), same split, same seed (42), same augmentation, same weighted loss, same `UNFREEZE_FROM = 13`, same batch size 16. Only `LEARNING_RATE` changes. The test split is not used for tuning; selection uses validation loss and validation macro F1.

| Experiment ID | Start | LR | Frozen / unfrozen | Split | Seed | Batch | Optimizer | Epochs | Metrics |
|---|---|---|---|---|---|---|---|---|---|
| LR-1 | Head-trained checkpoint | 1e-3 | features[13:] + classifier[3] | fold_1 | 42 | 16 | same as current | 20 (early stop 5) | val loss, val acc, val macro F1 |
| LR-2 | Head-trained checkpoint | 1e-4 | same | fold_1 | 42 | 16 | same | 20 (early stop 5) | same |
| LR-3 (current, reference) | Head-trained checkpoint | 1e-5 | same | fold_1 | 42 | 16 | same | 20 (early stop 5) | same; already run (best epoch 9) |

Why each: 1e-5 is the existing fine-tuning setting and serves as the reference. 1e-4 tests faster adaptation of the unfrozen layers. 1e-3 is a deliberately aggressive candidate that may destabilise pretrained features. These are candidates, not expected optimal values. The original checkpoint is preserved; new runs must save to new filenames. LR-1 and LR-2 have not been run.

## 4. Blockers
Training logs/checkpoints are not committed; runs require the local dataset and Apple MPS/GPU.

## 5. Learning-rate experiment results (run 2026-11-22)

MobileNetV3-Large, started from the head-trained baseline checkpoint, `features[13:]` and `classifier[3]` trainable, same split, seed 42, batch size 16, Adam (weight decay 1e-4), up to 20 epochs with early stopping. Only the learning rate changed. Selection used validation only; the test split was not used.

| Run | LR | Best epoch | Val loss at best | Val acc | Val bal. acc | Val macro F1 |
|---|---|---|---|---|---|---|
| mnv3_lr1e-3 | 0.001 | 7 | 1.103 | 65.93% | 60.32% | 58.81% |
| mnv3_lr1e-4 | 0.0001 | 3 | 0.916 | 66.48% | 58.42% | 58.68% |
| mnv3_lr1e-5 | 1e-05 | 1 | 1.273 | 50.69% | 54.34% | 45.16% |

- lr 1e-3 and 1e-4 gave similar validation results (macro F1 difference +0.13 points); the evidence does not separate them. With 1e-3 the validation loss fluctuated strongly between epochs; with 1e-4 it was lowest early (epoch 3) and then rose as training accuracy climbed.
- lr 1e-5 gave the lowest validation scores. The baseline checkpoint itself scored 0.5845 accuracy and 1.156 loss on validation before any training (measured separately), and the best epoch of this run was below that starting point, so training in this script at 1e-5 did not preserve the starting performance. The deployed model was trained at 1e-5 with a different script and reached 61.22% validation accuracy, so this result should not be read as showing that 1e-5 is unsuitable in general.

### Repeat with the feature extractor in eval mode (BatchNorm statistics frozen)

Same settings, plus `--features-eval`, which keeps `model.features` in eval mode during training as `ml/src/training/trainer.py` does.

| Run | LR | Best epoch | Val acc | Val bal. acc | Val macro F1 | Val macro F1 without the flag |
|---|---|---|---|---|---|---|
| mnv3_lr1e-3_fe | 0.001 | 5 | 69.81% | 62.30% | 61.58% | 58.81% |
| mnv3_lr1e-4_fe | 0.0001 | 1 | 63.43% | 57.45% | 54.72% | 58.68% |
| mnv3_lr1e-5_fe | 1e-05 | 9 | 61.50% | 61.47% | 56.69% | 45.16% |

- At lr 1e-5 with the feature extractor in eval mode, validation accuracy was 61.50% (starting checkpoint: 58.45%). This is at or above the starting point and above the run without the flag (50.69%), consistent with BatchNorm statistic updates explaining the earlier degradation; it is one run and does not prove the cause.
- Single run per setting and a small validation set: treat differences of a few points as inconclusive.


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

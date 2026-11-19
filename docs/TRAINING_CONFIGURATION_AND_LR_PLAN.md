# DermAI - Current Training Configuration and Learning-Rate Experiment Plan

## 1. Current configuration (from repository docs/scripts)
| Item | Value |
|---|---|
| Architecture / checkpoint | MobileNetV3-Large, `best_mobilenet_v3_large_finetuned.pth` (epoch 9) |
| Pretrained | Yes (ImageNet) |
| Frozen / trainable | Baseline: backbone frozen, head trained. Fine-tune: see `finetune_mobilenet_v3_large.py` (unfrozen layers: verify in script) |
| Learning rate | 1e-4 (config.yaml); fine-tune LR: verify in script |
| Batch size | 16 |
| Optimizer | Adam |
| Weight decay | 1e-4 |
| Epochs | up to 20 (config.yaml); best at epoch 9 |
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
Same architecture (MobileNetV3-Large), same split, same seed, same augmentation, same weighted loss. Only the learning rate changes. Experiment type: **fine-tune head plus last backbone block** (identical across runs). The test split is not used for tuning.

| Experiment ID | Checkpoint start | LR | Frozen / unfrozen | Split | Seed | Batch | Optimizer | Epochs | Metrics |
|---|---|---|---|---|---|---|---|---|---|
| LR-1 | ImageNet pretrained | 1e-3 | Backbone frozen except last block + head | fold_1 | 42 | 16 | Adam, wd 1e-4 | 20 (early stop 5) | val loss, val acc, val macro F1 |
| LR-2 | ImageNet pretrained | 1e-4 | same | fold_1 | 42 | 16 | Adam, wd 1e-4 | 20 (early stop 5) | same |
| LR-3 | ImageNet pretrained | 1e-5 | same | fold_1 | 42 | 16 | Adam, wd 1e-4 | 20 (early stop 5) | same |

Why each: 1e-3 tests faster adaptation but risks unstable fine-tuning; 1e-4 is the current reference; 1e-5 tests slower, more conservative updates that may reduce forgetting of pretrained features. These are candidates, not expected optimal values. Original checkpoint is preserved; new runs save to separate filenames.

## 4. Blockers
Training logs/checkpoints are not committed; runs require the local dataset and Apple MPS/GPU.

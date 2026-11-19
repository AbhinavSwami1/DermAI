# Advanced AI - Status

| Item | Status |
|---|---|
| Baseline CNNs (MobileNetV3-Large, EfficientNet-B0) | Implemented and evaluated |
| Advanced CNN (e.g. ConvNeXt-Tiny or ResNet50) | Not implemented |
| Transformer (ViT-B/16, DeiT-S, Swin-T) | Not implemented |
| Ensemble | Not evaluated (needs a second validated model first) |
| Hyperparameter optimisation | Planned: `docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md` |

## Blocker
No advanced-model training has been run. Training requires the local PAD-UFES-20 splits and an accelerator; the repository contains no data or checkpoints. Training time on a laptop (MPS) for ConvNeXt-Tiny/ViT on 1,477 images is feasible but unverified.

## Path to completion
1. Add `ml/src/models/convnext_tiny.py` using `torchvision.models.convnext_tiny` with a 6-class head.
2. Reuse `train_efficientnet_b0.py` structure with identical split, seed, loss and preprocessing.
3. Evaluate on validation for selection, test once. Add to the comparison table in `PHASE5_MODEL_COMPARISON_REPORT.md`.
4. Repeat with `vit_b_16` (or document memory/time limits if it cannot run).

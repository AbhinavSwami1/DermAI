# Experiment Runbook - Advanced Models and Learning-Rate Runs

All runs use `ml/scripts/train_advanced.py`: same patient-level split, seed 42, preprocessing, weighted cross-entropy (weights from the training split), Adam (wd 1e-4), ReduceLROnPlateau, early stopping (patience 5), best checkpoint by lowest validation loss. Existing checkpoints are never overwritten (the script refuses). The test split is used only with `--eval-test`, once per finally selected run.

## 0. Smoke test (about 1 minute, no pretrained download needed)
```
python ml/scripts/train_advanced.py --arch convnext_tiny --lr 1e-4 --trainable all --no-pretrained --max-batches 2 --epochs 1 --run-id smoke
rm -rf ml/outputs/experiments/smoke ml/checkpoints/experiments/smoke.pth
```

## 1. Advanced CNN, Transformer
```
python ml/scripts/train_advanced.py --arch convnext_tiny --lr 1e-4 --trainable all --run-id convnext_tiny_lr1e-4
python ml/scripts/train_advanced.py --arch vit_b_16     --lr 1e-5 --trainable all --run-id vit_b16_lr1e-5
# optional: swin_t, resnet50, densenet121
```
If `vit_b_16` runs out of memory on the available device, record that as the blocker and use `swin_t` instead.

## 2. Learning-rate experiments (MobileNetV3-Large, same settings as `docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md`)
```
for LR in 1e-3 1e-4 1e-5; do
  python ml/scripts/train_advanced.py --arch mobilenet_v3_large --lr $LR --trainable unfreeze_from --unfreeze-from 13 \
    --init-checkpoint ml/checkpoints/mobilenet/best_mobilenet_v3_large.pth --run-id mnv3_lr$LR
done
```
Use the same baseline checkpoint path that `finetune_mobilenet_v3_large.py` uses (`BASELINE_CHECKPOINT`). The existing fine-tuned checkpoint is preserved.

## 3. Compare and ensemble
```
python ml/scripts/compare_experiments.py                                   # writes docs/EXPERIMENT_RESULTS.md
python ml/scripts/compare_experiments.py --ensemble convnext_tiny_lr1e-4 mnv3_lr1e-4
```
Select the model on validation results. Then evaluate only the chosen run(s) on test: rerun that run with a new `--run-id` and `--eval-test`, or train once with `--eval-test` if the choice is already fixed. Ensemble test numbers need `--with-test` and runs trained with `--eval-test`.

## 4. How to interpret
- Compare validation macro F1 and per-class recall (MEL, SCC), not accuracy alone.
- With 361 validation images, differences of a few points are within noise; say "inconclusive" when that is the case.
- None of these results show clinical reliability.

## Status
Scripts are written and compile; they have not been run on the real dataset in this repository's environment. Results table: `docs/EXPERIMENT_RESULTS.md` (generated after runs).

## One-command run (Swin-T, ViT-B/16, learning-rate runs)
```
caffeinate -i bash ml/scripts/run_remaining_experiments.sh
```
Trains `swin_t_lr1e-4`, `vit_b16_lr1e-5`, `mnv3_lr1e-3`, `mnv3_lr1e-4` and `mnv3_lr1e-5`, skips finished runs, and writes `docs/EXPERIMENT_RESULTS.md` (validation results). Then:
```
python ml/scripts/eval_run_on_test.py --run-id <chosen_run>        # test split, once, after selecting on validation
python ml/scripts/compare_experiments.py --ensemble convnext_tiny_lr1e-4 <other_run> --with-test
python ml/scripts/export_figures.py                                 # training curves and confusion matrices into docs/figures/training/
```

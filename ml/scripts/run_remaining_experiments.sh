#!/usr/bin/env bash
# Run from the repository root:  bash ml/scripts/run_remaining_experiments.sh
# Trains the remaining experiments one after another (several hours on a laptop; keep the
# machine awake, e.g. prefix with `caffeinate -i`). Finished runs are skipped; a failed run
# does not stop the others. The test split is NOT used here.
set -u
BASE=ml/checkpoints/mobilenet/best_mobilenet_v3_large.pth
mkdir -p ml/outputs/experiments

run() {
  id=$1; shift
  if [ -f "ml/outputs/experiments/$id/val_metrics.json" ]; then echo "skip $id (finished)"; return; fi
  if [ -f "ml/checkpoints/experiments/$id.pth" ]; then
    echo "partial run $id: delete ml/checkpoints/experiments/$id.pth and ml/outputs/experiments/$id, then rerun"; return
  fi
  echo "=== $id  $(date)"
  python ml/scripts/train_advanced.py --run-id "$id" "$@" || echo "FAILED $id"
}

# 1. Transformers (ViT-B/16 may run out of memory; a failure is recorded as the blocker)
run swin_t_lr1e-4  --arch swin_t   --lr 1e-4 --trainable all
run vit_b16_lr1e-5 --arch vit_b_16 --lr 1e-5 --trainable all --batch-size 8

# 2. Learning-rate experiment: MobileNetV3-Large, same split, seed, loss, unfrozen layers; only lr changes
for LR in 1e-3 1e-4 1e-5; do
  run mnv3_lr$LR --arch mobilenet_v3_large --lr $LR --trainable unfreeze_from --unfreeze-from 13 --init-checkpoint $BASE
done

python ml/scripts/compare_experiments.py
echo "Next: choose on VALIDATION results, then run eval_run_on_test.py --run-id <id> for the chosen runs,"
echo "then: python ml/scripts/compare_experiments.py --ensemble convnext_tiny_lr1e-4 <other_run> --with-test"
echo "and: python ml/scripts/export_figures.py"

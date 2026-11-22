#!/usr/bin/env bash
# Run from the repository root:  bash ml/scripts/run_lr_features_eval.sh
# Repeats the three MobileNetV3 learning-rate runs with model.features kept in eval mode
# (BatchNorm statistics frozen, as the original trainer does). About 6 minutes in total.
set -u
BASE=ml/checkpoints/mobilenet/best_mobilenet_v3_large.pth
for LR in 1e-3 1e-4 1e-5; do
  id=mnv3_lr${LR}_fe
  if [ -f "ml/outputs/experiments/$id/val_metrics.json" ]; then echo "skip $id"; continue; fi
  echo "=== $id  $(date)"
  python ml/scripts/train_advanced.py --run-id "$id" --arch mobilenet_v3_large --lr $LR \
    --trainable unfreeze_from --unfreeze-from 13 --init-checkpoint $BASE --features-eval || echo "FAILED $id"
done
python ml/scripts/write_experiment_docs.py

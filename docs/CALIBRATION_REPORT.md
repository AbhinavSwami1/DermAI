# DermAI - Confidence Calibration Evaluation

## Method
- Checkpoint: `best_mobilenet_v3_large_finetuned.pth` (epoch 9).
- Logits computed with the same eval transform used in evaluation (ImageNet normalisation).
- Temperature scaling (single scalar T) fitted on the **validation split only** (361 images) by minimising NLL.
- Final evaluation on the **held-out test split** (460 images), once.
- Metrics: ECE (10 bins), NLL, Brier score, reliability diagram, high-confidence incorrect predictions (score >= 0.8), ambiguous predictions (top-1 minus top-2 < 0.10).
- Thresholds 0.8 and 0.10 are reporting thresholds only, not clinical rules.

## How to reproduce
```
python ml/scripts/calibration_analysis.py
```
Outputs in `ml/outputs/calibration/`: `calibration_results.json`, `reliability_diagram.png`, `high_confidence_errors_test.csv`.

## Results
Run on the real checkpoint (test accuracy 57.39%, matching the documented evaluation). Temperature fitted on the validation split only; test split evaluated once.

| Metric (test, 460 images) | Uncalibrated | After temperature scaling |
|---|---|---|
| ECE (10 bins) | 0.0739 | 0.0429 |
| NLL | 1.0571 | 1.0427 |
| Brier | 0.5460 | 0.5413 |
| Mean model score | 64.49% | 61.10% |
| Accuracy | 57.39% | 57.39% |
| Fitted T (validation) | 1.0 | 1.135 |

Error analysis (uncalibrated scores, test split):
- Predictions with score >= 0.8: 98, of which 14 were incorrect (accuracy 85.71%).
- Predictions with score < 0.5: accuracy 34.51%.
- Ambiguous predictions (top-1 minus top-2 < 0.10): 67 of 460.
- High-confidence incorrect cases are listed in `ml/outputs/calibration/high_confidence_errors_test.csv`; the reliability diagram is `ml/outputs/calibration/reliability_diagram.png`.

Interpretation: the model is moderately overconfident (mean score 64.5% vs accuracy 57.4%). Higher scores are associated with higher accuracy, but confidently incorrect predictions exist. Temperature scaling gives a modest reduction in ECE; the NLL and Brier improvements are small, and with 460 test images and rare classes this should not be read as a reliable calibration fix.

## Limitations
- Small test set (460 images) and rare classes (MEL, SCC): per-bin estimates are noisy.
- Temperature scaling changes scores, not the predicted class.
- Calibrated scores are still not clinically validated probabilities; no external dataset validation.

## Principal high-confidence errors (test split)
Of 98 predictions with a model score >= 0.8, 14 were incorrect (scores 0.81 to 0.93; see `ml/outputs/calibration/high_confidence_errors_test.csv`). Five of the 14 were true SCC cases, all predicted as ACK (3) or BCC (2). Other errors were ACK predicted as BCC (3) or SCC (1), BCC predicted as NEV, SCC or ACK (1 each), and SEK predicted as BCC or NEV (1 each). The errors are concentrated among ACK, BCC and SCC. None of the 14 involved true MEL or NEV images; this does not show good MEL or NEV performance (MEL test F1 is 28.57%).

The uncalibrated reliability curve lies below the diagonal over most score ranges (overconfidence); temperature scaling (T = 1.135, fitted on validation) brings the mid and high bins close to the diagonal. Low-score bins remain below the diagonal after scaling, and bins at the extremes contain few images, so conclusions about them are weak. Model scores must not be presented as clinically validated probabilities.

Reliability bin counts (test, uncalibrated): 2 / 35 / 76 / 91 / 72 / 86 / 53 / 45 images in the score bins 0.2-0.3 through 0.9-1.0. The lowest bin (2 images) is too small to interpret. In every other bin, observed accuracy is below the mean score, with the largest gaps in the 0.4-0.7 range. Of the 98 predictions scoring 0.8 or higher, 12 of 53 were wrong in the 0.8-0.9 bin and 2 of 45 in the 0.9-1.0 bin.

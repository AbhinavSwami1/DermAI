# Image Quality Threshold Validation

## Current rules (`backend/app/services/image_quality_service.py`, version 1.0.0)
Blur score (Laplacian variance) < 100 flags POSSIBLY_BLURRY; mean brightness < 40 or > 220; dark/bright pixel fraction > 50%. Any flag gives REVIEW_REQUIRED, which blocks prediction.

## Observed issue
During testing, several PAD-UFES-20 test images (processed 224x224 PNGs) were flagged POSSIBLY_BLURRY with scores 78 to 93, while other images scored above 150. Laplacian variance depends on image size and content, so one fixed threshold may reject clear small or smooth images.

## Validation method (`ml/scripts/evaluate_image_quality.py`)
1. Synthetic degradation with known ground truth on a seeded sample of test images: Gaussian blur (sigma 1.5, 3.0), darkening, brightening. Reports detection rate of the expected flag and the false-flag rate on the untouched originals, plus a blur-threshold sweep (20 to 150).
2. Optional manual reference: `--make-template`, label each image good / acceptable / poor after viewing, then `--reference-csv`. Reports sensitivity (poor detected), specificity and agreement.

```
python ml/scripts/evaluate_image_quality.py --n 60
python ml/scripts/evaluate_image_quality.py --make-template
python ml/scripts/evaluate_image_quality.py --reference-csv ml/outputs/quality_validation/reference_template.csv
```
Outputs: `ml/outputs/quality_validation/`.

## Results
Run on 60 randomly sampled test images (seed 42), all 224x224 processed PNGs.

- With the current threshold (100), 26.7% of untouched images were flagged POSSIBLY_BLURRY.
- Blur-score percentiles of untouched images: 5th 36.9, 25th 92.9, median 224.4, 75th 433.4, 95th 1227.0. The wide spread shows the score reflects image texture as well as focus.
- Synthetic blur (Gaussian sigma 1.5 and 3.0) was detected in 100% of cases at thresholds 30 to 150 (98.3% for sigma 1.5 at threshold 20).
- Synthetic darkening was detected as LOW_BRIGHTNESS in 86.7% of cases and brightening as HIGH_BRIGHTNESS in 91.7%. The misses were not inspected.

| Min blur score | Untouched images rejected | Sigma 1.5 detected | Sigma 3.0 detected |
|---|---|---|---|
| 20 | 0.0% | 98.3% | 100% |
| 30 | 5.0% | 100% | 100% |
| 40 | 6.7% | 100% | 100% |
| 50 | 15.0% | 100% | 100% |
| 60 | 18.3% | 100% | 100% |
| 75 | 20.0% | 100% | 100% |
| 100 (current) | 26.7% | 100% | 100% |
| 125 | 35.0% | 100% | 100% |
| 150 | 36.7% | 100% | 100% |

Interpretation: a threshold of 100 detects no more synthetic blur than 30 to 40 but rejects roughly four times as many untouched images. A value near 40 is a candidate. The threshold has not been changed: the flagged untouched images still need manual inspection, and untouched images are assumed acceptable, which may not hold for all of them.

## Limitations
Synthetic blur is not real camera blur; processed 224 px images differ from raw mobile photographs; resolution is checked at upload, not by this service; lesion visibility and background interference are not assessed.

## Manual inspection of untouched images below the current threshold
The 16 untouched test images with blur score below 100 were inspected visually (contact sheet of 224x224 images). Several clear images scored low because they contain little texture: a palm with a pen mark (25), smooth skin with a pen circle (28), a sharp dark mole on smooth skin (44), a sharp mole (79) and a uniform pigmented patch (93). A few images looked soft or low-contrast (20, 37, 42, 67). There is no clean separation near a single score: clear and soft images are mixed between scores 20 and 50.

Conclusion: the Laplacian-variance score reflects texture as well as focus, so it is not reliable as a standalone hard rejection rule. Lowering the threshold from 100 to about 40 reduces false rejections (26.7% to 6.7% of untouched images) but does not remove them. Recommended design: treat possible blur as a warning that the user may override, and reserve rejection for invalid files and extreme exposure. This is a visual review by one reviewer, not a validated reference standard; the manual reference comparison (`--reference-csv`) has not been completed.

## Decision implemented (algorithm version 1.1.0)
- `MIN_BLUR_SCORE` lowered from 100 to 40, chosen from the threshold sweep and the visual review. This is a compromise, not a validated optimum.
- Possible blur is now a **warning**, not a block. Status values: `ACCEPTABLE`, `WARNING` (blur flag only), `REVIEW_REQUIRED` (any brightness or pixel-fraction flag, still blocks prediction).
- For a `WARNING` image the backend returns 409 `IMAGE_QUALITY_WARNING` unless the request includes `acknowledge_quality_warning=true`. The check is enforced on the server for both prediction and Grad-CAM; the frontend shows a "Continue anyway / Choose another image" prompt.
- The acknowledgement itself is not stored; the quality flags remain on the stored assessment and appear in reports.
- Images assessed earlier under version 1.0.0 keep their stored status; blur-only images from before remain `REVIEW_REQUIRED`.
- Limitation: a featureless image (blur score near 0, normal brightness) now yields only a warning and can be analysed after confirmation.

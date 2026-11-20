# Grad-CAM Observations (exploratory)

- Model: `mobilenet_v3_large_finetuned_epoch9`
- Target layer: `model.features[-1]` (last convolutional block of MobileNetV3-Large)
- Images: test split only. Grad-CAM is not lesion segmentation and does not show a prediction is correct.

Automated columns: `border ratio` > 1 means more heat on the outer 20% frame than a uniform map (possible background/artifact focus); blank/saturated flag suspicious maps. They only flag images to inspect.

| Image | True class | Predicted (score) | Border ratio | Coverage >0.5 | Peak (x,y) | Blank | Saturated | Reviewer observation |
|---|---|---|---|---|---|---|---|---|
| PAT_359_4450_86.png | ACK | ACK (98.0%) | 0.98 | 0.29 | (0.93, 0.35) | False | False | Correct, score 98%. Heat is spread over much of the skin with the strongest peak at the right edge; only a small hot spot lies near the pen-marked spot at the centre. The high score is not matched by a clearly lesion-centred map. |
| PAT_134_201_587.png | BCC | BCC (79.0%) | 0.71 | 0.10 | (0.5, 0.5) | False | False | Correct, score 79%. One strong peak at the image centre over the area with visible vessels, with a weaker extension toward the upper right. Plausibly central/lesion-related; no lesion boundary exists to confirm. |
| PAT_233_354_935.png | MEL | NEV (34.1%) | 1.19 | 0.14 | (0.34, 0.93) | False | False | Incorrect (MEL predicted as NEV, 34%). Strongest heat is in the bottom-left corner, away from the pigmented lesion at the centre; the lesion itself has little heat. Suggests attention on background skin. Border ratio 1.19 is the only value above 1. |
| PAT_1453_1567_250.png | NEV | SEK (46.2%) | 0.94 | 0.16 | (0.5, 0.0) | False | False | Incorrect (NEV predicted as SEK, 46%). Heat is along the top edge, upper right and lower left; the lesion at the centre-left is a low-activation (dark blue) region. Attention is outside the lesion. |
| PAT_882_1677_789.png | SCC | ACK (81.0%) | 0.88 | 0.30 | (0.5, 0.49) | False | False | Incorrect (SCC predicted as ACK, 81%). Strong elongated heat runs from the blue pen mark above the lesion down to the crusted lesion, so it covers both. The pen marking may be influencing the score; this is a hypothesis, not demonstrated. |
| PAT_1653_2916_346.png | SEK | SEK (92.8%) | 0.81 | 0.16 | (0.64, 0.64) | False | False | Correct, score 92.8%. Peak lies on the lower-right part of the pigmented patch; the left part of the patch has little heat. Plausibly lesion-related but covers only part of the patch. |

## Summary of observations
Visual review of six test images (one per class), single reviewer, exploratory only. This is not clinical validation and does not show that any prediction is correct.

1. **Does the heatmap change between images?** Yes. Location, shape and extent differ for every image.
2. **Lesion or background?** Mixed. The BCC and SEK examples (and partly the SCC example) show heat over the central/lesion area. In the two incorrect low-score cases (MEL and NEV) the strongest heat lies on skin away from the lesion. The correct ACK case (98%) has diffuse heat with a peak at the image edge.
3. **Alignment.** The overlay matches the original in all six images (for example, heat follows the pen mark in the SCC image).
4. **Blank, saturated or suspicious maps.** None blank or saturated; coverage above 0.5 ranged from 0.10 to 0.30. The ACK map is diffuse and its peak is at the right edge.

Pattern worth testing: several images in this dataset carry pen markings, and the SCC and ACK examples show heat on or near them. A marking-removal or crop experiment would be needed to test whether the model uses them. The automated border ratio only flagged one image (MEL, 1.19) and did not detect the edge peak in the ACK image, so it is a weak screening aid.

## Limitations
- Single target layer; low spatial resolution (7x7 upsampled).
- Explanation of the predicted class, including incorrect predictions.
- No lesion masks exist, so overlap with the lesion cannot be measured quantitatively.

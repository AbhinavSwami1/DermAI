# DermAI - Grad-CAM Localization Evaluation

## 1. Objective

To investigate which image regions influence the predictions
of the trained MobileNetV3-Small classification model using
Gradient-weighted Class Activation Mapping (Grad-CAM).

## 2. Dataset and Model

- Dataset: PAD-UFES-20
- Dataset partition: Fold 1 held-out test set
- Model: MobileNetV3-Small baseline
- Input resolution: 224 x 224 RGB
- Number of visualized samples: 6
- Samples selected: One per diagnostic class
- Target layer: model.features[-1]

## 3. Prediction Results

| Actual Class | Predicted Class | Confidence |
|---|---|---:|
| ACK | ACK | 67.13% |
| BCC | BCC | 63.89% |
| MEL | BCC | 25.97% |
| NEV | NEV | 46.65% |
| SCC | BCC | 38.72% |
| SEK | SEK | 34.75% |

Correct predictions: 4/6.

These results describe only the six selected examples and
must not be interpreted as overall model performance.

## 4. Qualitative Localization Observations

### ACK
The strongest activation was concentrated over the visible
lesion/marking region. This was the cleanest observed example.

### BCC
The strongest hotspots appeared near the right edge and
bottom-left region. Only a smaller activation was observed
near the central lesion area. This may indicate attention
to surrounding skin texture or image context.

### MEL
Activation was concentrated near the lesion centre.
However, the model predicted BCC instead of MEL, suggesting
that attention to the relevant region does not guarantee
correct classification.

### NEV
Most activation was associated with the lesion, with a
smaller additional hotspot in the background.

### SCC
Activation covered part of the area to the left and above
the lesion, but did not fully cover its central and right
regions. The model predicted BCC instead of SCC.

### SEK
The main hotspot was located over the lesion, with an
additional activation blob in the upper-left background.

## 5. Summary

| Class | Observed Focus | Prediction |
|---|---|---|
| ACK | Lesion | Correct |
| BCC | Mostly background/context | Correct |
| MEL | Lesion centre | Incorrect |
| NEV | Lesion and some background | Correct |
| SCC | Partial lesion region | Incorrect |
| SEK | Lesion and some background | Correct |

## 6. Limitations

- Only six examples were visually inspected.
- The observations are qualitative and do not establish
  localization accuracy.
- No ground-truth bounding boxes, segmentation masks,
  polygons or pixel-level lesion annotations were identified
  in the inspected local dataset files.
- Dice, IoU and bounding-box localization metrics therefore
  cannot be calculated reliably.
- Grad-CAM highlights class-discriminative model activations;
  it does not produce verified lesion boundaries.
- Background activation may indicate reliance on contextual
  image features, but six examples are insufficient to prove
  shortcut learning.
- Confidence values are model output probabilities and are
  not necessarily calibrated measures of certainty.

## 7. Integration with Classification Workflow

The localization prototype uses the existing trained
MobileNetV3-Small checkpoint.

Workflow:

1. Load and resize the input image to 224 x 224 RGB.
2. Apply the same ImageNet normalization used during training.
3. Obtain six-class classification logits.
4. Generate a Grad-CAM heatmap from the final feature block.
5. Resize the heatmap and overlay it on the original image.
6. Display the predicted class, confidence and activation map.

The visualization can accompany the classification output
as an experimental explainability component.

It must not be interpreted as a confirmed lesion boundary
or used as independent medical evidence.

## 8. Conclusion

A Grad-CAM prototype was successfully implemented for
MobileNetV3-Small and generated six visual examples,
covering all six PAD-UFES-20 diagnostic classes.

The qualitative review showed lesion-focused activation
in several examples, alongside background activation and
partial lesion coverage in others.

The results demonstrate the feasibility of adding
class-discriminative visual explanations to DermAI's
classification workflow. However, reliable lesion
localization evaluation requires annotated bounding boxes
or segmentation masks and a larger, systematic assessment.

DermAI remains a research prototype and is not a
clinically validated diagnostic system.

## 9. Generated Artifacts

- ml/src/explainability/gradcam.py
- ml/src/explainability/generate_visualizations.py
- ml/outputs/gradcam/gradcam_results.csv
- ml/outputs/gradcam/gradcam_1_ACK.png
- ml/outputs/gradcam/gradcam_2_BCC.png
- ml/outputs/gradcam/gradcam_3_MEL.png
- ml/outputs/gradcam/gradcam_4_NEV.png
- ml/outputs/gradcam/gradcam_5_SCC.png
- ml/outputs/gradcam/gradcam_6_SEK.png

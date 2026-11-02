DermAI — Grad-CAM Localization Evaluation

1. Objective

This report documents the Grad-CAM explainability prototype developed for DermAI.

Gradient-weighted Class Activation Mapping (Grad-CAM) is used to visualize image regions that contribute to a model’s class prediction.

The existing six-image visualization experiment was generated using the MobileNetV3-Small checkpoint.

The current backend Grad-CAM service uses the model-loading workflow associated with the selected MobileNetV3-Large fine-tuned checkpoint. These two implementations and their results must be distinguished.

2. Dataset and Historical Visualization Model

* Dataset: PAD-UFES-20
* Dataset partition: Fold 1 held-out test set
* Historical visualization model: MobileNetV3-Small
* Input resolution: 224 × 224 RGB
* Number of visualized samples: 6
* Samples selected: One per diagnostic class
* Target layer: model.features[-1]

The historical visualization generator references:

ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth

Therefore, the six saved visualizations described in this report belong to the Small checkpoint experiment.

3. Historical Prediction Results

Actual Class	Predicted Class	Confidence
ACK	ACK	67.13%
BCC	BCC	63.89%
MEL	BCC	25.97%
NEV	NEV	46.65%
SCC	BCC	38.72%
SEK	SEK	34.75%

Correct predictions: 4 out of 6.

These results describe only six selected examples. They are not overall classification metrics.

4. Qualitative Localization Observations

ACK

The strongest activation was concentrated over the visible lesion/marking region. This was the cleanest observed example.

BCC

The strongest hotspots appeared near the right edge and bottom-left region. A smaller activation was observed near the central lesion area. This may indicate attention to surrounding skin texture or image context.

MEL

Activation was concentrated near the lesion centre. However, the model predicted BCC instead of MEL. This illustrates that attention to a relevant image region does not guarantee correct classification.

NEV

Most activation was associated with the lesion, with a smaller additional hotspot in the background.

SCC

Activation covered part of the area to the left and above the lesion, but did not fully cover its central and right regions. The model predicted BCC instead of SCC.

SEK

The main hotspot was located over the lesion, with an additional activation region in the upper-left background.

5. Summary

Class	Observed Focus	Prediction
ACK	Lesion	Correct
BCC	Mostly background/context	Correct
MEL	Lesion centre	Incorrect
NEV	Lesion and some background	Correct
SCC	Partial lesion region	Incorrect
SEK	Lesion and some background	Correct

6. Current Backend Integration

The current DermAI backend includes a Grad-CAM service that uses the selected model-loading workflow.

The current selected classification checkpoint is:

ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth

The Grad-CAM service imports the inference model loader and preprocessing workflow rather than relying on the historical standalone Small-model visualization script.

The current workflow includes:

1. Load the selected model and execution device.
2. Decode and preprocess the uploaded image.
3. Apply the model’s expected RGB and ImageNet normalization.
4. Obtain classification outputs.
5. Generate class-discriminative activation maps.
6. Resize and overlay the heatmap on the input image.
7. Return the visualization alongside the classification workflow.

The existing six saved visualizations remain historical Small-model artifacts. They should not be relabelled as Large-model visualizations.

7. Limitations

* Only six historical examples were visually inspected.
* The observations are qualitative and do not establish localization accuracy.
* No ground-truth bounding boxes, segmentation masks, polygons or pixel-level lesion annotations were identified in the inspected local dataset files.
* Dice, IoU and bounding-box localization metrics cannot therefore be calculated reliably.
* Grad-CAM highlights class-discriminative model activations; it does not produce verified lesion boundaries.
* Background activation may indicate reliance on contextual image features, but six examples are insufficient to prove shortcut learning.
* Confidence values are model output probabilities and are not necessarily calibrated measures of certainty.
* No clinical localization validation has been conducted.

8. Interpretation and Safety

Grad-CAM is an experimental explainability technique.

A highlighted region does not prove that the model has identified the medically relevant lesion area.

The heatmap must not be interpreted as a confirmed lesion boundary, segmentation mask or independent medical evidence.

Classification confidence and activation intensity must not be treated as diagnostic certainty.

9. Generated Artifacts

* ml/src/explainability/gradcam.py
* ml/src/explainability/generate_visualizations.py
* ml/outputs/gradcam/gradcam_results.csv
* ml/outputs/gradcam/gradcam_1_ACK.png
* ml/outputs/gradcam/gradcam_2_BCC.png
* ml/outputs/gradcam/gradcam_3_MEL.png
* ml/outputs/gradcam/gradcam_4_NEV.png
* ml/outputs/gradcam/gradcam_5_SCC.png
* ml/outputs/gradcam/gradcam_6_SEK.png

10. Conclusion

The Grad-CAM prototype generated six historical visualizations using the MobileNetV3-Small checkpoint, covering all six PAD-UFES-20 diagnostic classes.

The qualitative review showed lesion-focused activation in several examples, alongside background activation and partial lesion coverage in others.

The current backend also integrates Grad-CAM with the selected MobileNetV3-Large model-loading workflow. However, the existing six saved visualizations remain Small-model results.

Reliable lesion localization evaluation requires annotated bounding boxes or segmentation masks and a larger systematic assessment.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.
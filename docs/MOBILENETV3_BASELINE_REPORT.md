DermAI — MobileNetV3 Baseline Experiment Report

1. Experiment Overview

This document records the historical MobileNetV3-Small baseline experiment and provides context about the subsequently implemented MobileNetV3-Large experiments.

The original Small experiment used transfer learning with a frozen feature extractor and a newly initialized six-class classification layer.

MobileNetV3-Large was later evaluated as a separate architecture and its fine-tuned checkpoint was selected for the current backend inference workflow.

These experiments must not be treated as the same checkpoint or architecture.

This is a research prototype and is not validated for clinical diagnosis or independent medical decision-making.

2. Dataset

Dataset: PAD-UFES-20

Total images: 2,298

Number of classes: 6

Classes:

* ACK
* BCC
* MEL
* NEV
* SCC
* SEK

Patient-wise data partition:

Partition	Images
Training	1,477
Validation	361
Testing	460
Total	2,298

Patient overlap between partitions: Zero.

3. Preprocessing

* Image format: RGB
* Image size: 224 × 224
* Interpolation: LANCZOS
* Input normalization: ImageNet mean and standard deviation
* Training augmentation: Random horizontal flip, vertical flip and rotation up to 15 degrees.

4. Historical Experiment — MobileNetV3-Small

Model Configuration

* Architecture: MobileNetV3-Small
* Pretrained weights: ImageNet
* Number of output classes: 6
* Training device: Apple MPS
* Optimizer: Adam
* Learning rate: 0.0001
* Weight decay: 0.0001
* Batch size: 16
* Maximum epochs: 20
* Loss: Weighted Cross Entropy
* Early stopping patience: 5
* Backbone: Frozen
* Trainable parameters: 6,150

Training Results

* Epochs completed: 20
* Final training loss: 1.0184
* Final training accuracy: 63.57%
* Best validation loss: 1.1003 at epoch 20
* Highest validation accuracy: 62.88% at epoch 15
* Best checkpoint selected using validation loss.

Historical Test Results

The earlier Small baseline experiment recorded the following held-out test results:

* Test accuracy: 55.00%
* Macro precision: approximately 0.49
* Macro recall: approximately 0.52
* Macro F1-score: approximately 0.49
* Weighted F1-score: approximately 0.58

These are historical Small-model results. They are not the test results of the currently selected MobileNetV3-Large checkpoint.

Historical Class-wise Performance

Class	Precision	Recall	F1-score	Support
ACK	0.70	0.58	0.64	146
BCC	0.71	0.58	0.64	169
MEL	0.26	0.60	0.36	10
NEV	0.72	0.67	0.69	49
SCC	0.13	0.28	0.18	39
SEK	0.43	0.43	0.43	47

The historical report contains the original Small experiment’s confusion matrix and class-wise results. These values should be interpreted only in the context of that experiment.

5. Subsequent MobileNetV3-Large Baseline

A separate MobileNetV3-Large baseline experiment was conducted later.

Validation Results

Metric	Result
Accuracy	58.45%
Macro Precision	53.14%
Macro Recall	59.43%
Macro F1-score	53.63%
Weighted F1-score	59.75%

Validation support: 361 images.

6. Fine-Tuned MobileNetV3-Large

The Large architecture was subsequently fine-tuned.

Selected checkpoint:

ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth

Selected epoch: 9.

Validation Results

Metric	Result
Accuracy	61.22%
Macro Precision	56.85%
Macro Recall	61.34%
Macro F1-score	56.53%
Weighted F1-score	63.61%

Held-Out Test Results

Metric	Result
Accuracy	57.39%
Macro Precision	52.44%
Macro Recall	52.70%
Macro F1-score	51.02%
Weighted F1-score	60.12%

Test support: 460 images.

These Large-model results are separate from the historical Small baseline.

7. Generated Artifacts

Historical Small experiment:

* ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth
* ml/outputs/plots/mobilenet_confusion_matrix.png
* ml/outputs/plots/mobilenet_loss_curve.png
* ml/outputs/plots/mobilenet_accuracy_curve.png
* ml/outputs/reports/mobilenet_training_history.csv

Large baseline:

* ml/checkpoints/mobilenet/best_mobilenet_v3_large.pth
* ml/outputs/mobilenet_v3_large/

Fine-tuned Large:

* ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth
* ml/outputs/mobilenet_v3_large_finetuned/

8. Observations and Limitations

* MobileNetV3-Small was the original transfer-learning baseline.
* MobileNetV3-Large was evaluated separately.
* Fine-tuning the Large architecture improved its validation metrics compared with its baseline.
* MEL and SCC remain challenging classes.
* Historical Small results must not be presented as Large-model results.
* The test set must not be repeatedly used for model selection.
* Results are specific to the dataset and experimental partition.
* No external clinical validation has been conducted.

9. Conclusion

The original MobileNetV3-Small baseline established an initial experimental reference for DermAI.

Subsequent experiments evaluated MobileNetV3-Large and EfficientNet-B0. The fine-tuned MobileNetV3-Large checkpoint was selected for the current inference workflow.

The current selected model achieved 57.39% accuracy on the held-out test partition.

DermAI remains an academic research and screening-support prototype, not a clinically validated diagnostic tool.
DermAI — Phase 5: Model Improvement and Comparison

1. Overview

Phase 5 focused on transfer-learning experiments for six-class skin-lesion image classification using the PAD-UFES-20 dataset.

The verified comparison includes:

1. MobileNetV3-Large baseline
2. Fine-tuned MobileNetV3-Large
3. EfficientNet-B0

The objective was to compare model performance using the same patient-safe training and validation partitions.

The selected model for the current backend inference workflow is MobileNetV3-Large Fine-Tuned.

2. Dataset and Experimental Setup

* Dataset: PAD-UFES-20
* Total images: 2,298
* Number of classes: 6
* Training images: 1,477
* Validation images: 361
* Test images: 460
* Training patients: 880
* Validation patients: 220
* Test patients: 273

Patient-level grouping was used to prevent patient overlap between training, validation and test partitions.

The test partition was kept separate from model selection and hyperparameter tuning.

Disease Classes

* ACK
* BCC
* MEL
* NEV
* SCC
* SEK

Common Training Configuration

* Image size: 224 × 224
* Color mode: RGB
* Normalization: ImageNet mean and standard deviation
* Batch size: 16
* Optimizer: Adam
* Weight decay: 0.0001
* Loss function: Weighted Cross Entropy
* Training device: Apple MPS
* Random seed: 42

Class weights were calculated using training data only.

3. Experiment 1 — MobileNetV3-Large Baseline

A pretrained MobileNetV3-Large architecture was used with its feature extractor frozen and a six-class classification layer.

Validation Results

Metric	Result
Accuracy	58.45%
Macro Precision	53.14%
Macro Recall	59.43%
Macro F1-score	53.63%
Weighted F1-score	59.75%

Validation support: 361 images.

4. Experiment 2 — Fine-Tuned MobileNetV3-Large

The pretrained MobileNetV3-Large model was fine-tuned to improve its classification performance.

The selected checkpoint was saved at epoch 9.

Checkpoint Information

* Architecture: MobileNetV3-Large
* Checkpoint: best_mobilenet_v3_large_finetuned.pth
* Selected epoch: 9
* Best validation loss: 1.065688
* Validation accuracy at selected checkpoint: 61.22%
* Input resolution: 224 × 224
* Normalization: ImageNet mean and standard deviation

Validation Results

Metric	Result
Accuracy	61.22%
Macro Precision	56.85%
Macro Recall	61.34%
Macro F1-score	56.53%
Weighted F1-score	63.61%

Validation support: 361 images.

5. Experiment 3 — EfficientNet-B0

A pretrained EfficientNet-B0 architecture was evaluated using transfer learning.

The experiment used the same dataset partition and six-class classification task.

Validation Results

Metric	Result
Accuracy	59.56%
Macro Precision	52.36%
Macro Recall	56.30%
Macro F1-score	52.38%
Weighted F1-score	60.72%

Validation support: 361 images.

6. Model Comparison

The following comparison uses validation results only.

Metric	MobileNetV3-Large Baseline	MobileNetV3-Large Fine-Tuned	EfficientNet-B0
Accuracy	58.45%	61.22%	59.56%
Macro Precision	53.14%	56.85%	52.36%
Macro Recall	59.43%	61.34%	56.30%
Macro F1-score	53.63%	56.53%	52.38%
Weighted F1-score	59.75%	63.61%	60.72%

Fine-tuning MobileNetV3-Large improved all five reported validation metrics compared with its baseline.

7. Selected Model and Held-Out Test Evaluation

MobileNetV3-Large Fine-Tuned was selected for the current DermAI backend inference workflow.

Its selected checkpoint was evaluated on the held-out test partition containing 460 images.

Held-Out Test Results

Metric	Result
Accuracy	57.39%
Macro Precision	52.44%
Macro Recall	52.70%
Macro F1-score	51.02%
Weighted Precision	65.48%
Weighted Recall	57.39%
Weighted F1-score	60.12%

These results are reported separately from validation results.

The held-out test results are an evaluation of the selected checkpoint, not a three-model test-set comparison.

Per-Class Test Performance

Class	Precision	Recall	F1-score	Support
ACK	76.42%	64.38%	69.89%	146
BCC	72.00%	53.25%	61.22%	169
MEL	27.27%	30.00%	28.57%	10
NEV	64.29%	73.47%	68.57%	49
SCC	17.14%	46.15%	25.00%	39
SEK	57.50%	48.94%	52.87%	47

The MEL class has only 10 test samples. Its metrics therefore have substantial uncertainty.

SCC also shows weak precision and F1-score, indicating that further investigation of class imbalance and class-wise errors is necessary.

8. Observations

1. Fine-tuned MobileNetV3-Large achieved the strongest results across all five reported validation metrics.
2. Fine-tuning improved validation accuracy by 2.77 percentage points over the Large baseline.
3. Fine-tuning improved validation macro F1 by 2.90 percentage points.
4. EfficientNet-B0 achieved 59.56% validation accuracy and 52.38% macro F1.
5. The selected Large fine-tuned checkpoint achieved 57.39% accuracy on the held-out test set.
6. MEL and SCC remain challenging classes.
7. Validation and held-out test results differ, highlighting the need to evaluate generalization carefully.

9. Generated Artifacts

Important experiment artifacts are stored under:

* ml/outputs/mobilenet_v3_large/
* ml/outputs/mobilenet_v3_large_finetuned/
* ml/outputs/efficientnet_b0/
* ml/outputs/mobilenet_comparison/
* ml/outputs/reports/

Selected checkpoint:

ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth

Held-out test metrics:

ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json

10. Limitations

* Experiments use PAD-UFES-20 and its patient-grouped partitions.
* External dataset validation has not been conducted.
* MEL has limited representation in the held-out test set.
* SCC performance remains limited.
* Validation performance does not establish clinical reliability.
* The three-model comparison is based on validation metrics.
* Only the selected fine-tuned Large checkpoint has the reported held-out test evaluation in this report.
* No clinical validation has been performed.

11. Conclusion

Phase 5 evaluated MobileNetV3-Large baseline, fine-tuned MobileNetV3-Large and EfficientNet-B0.

Fine-tuned MobileNetV3-Large achieved the strongest validation metrics among these three experiments and was selected for the current backend inference workflow.

The selected checkpoint achieved 57.39% accuracy and 51.02% macro F1 on the held-out test partition.

DermAI remains an academic research prototype. It is not clinically validated and is not intended to provide medical diagnosis or treatment decisions.
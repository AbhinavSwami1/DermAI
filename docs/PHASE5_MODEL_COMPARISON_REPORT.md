# **DermAI — Phase 5: Model Improvement and Comparison**

## **1\. Overview**

Phase 5 focused on improving and comparing deep learning architectures for skin lesion image classification using the PAD-UFES-20 dataset.
Three experiments were conducted:

1. MobileNetV3-Small baseline
2. Fine-tuned MobileNetV3-Small
3. EfficientNet-B0 transfer learning

The objective was to compare model performance using the same patient-safe training and validation partitions.

## **2\. Dataset and Experimental Setup**

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
The test partition was not used for Phase 5 model selection or tuning.

### **Disease Classes**

* ACK
* BCC
* MEL
* NEV
* SCC
* SEK

### **Training Configuration**

* Image size: 224 × 224
* Color mode: RGB
* Preprocessing: ImageNet normalization
* Batch size: 16
* Optimizer: Adam
* Learning rate: 0.0001 for classifier-only training
* Weight decay: 0.0001
* Loss function: Weighted Cross Entropy
* Training device: Apple MPS

Class weights were calculated using training data only.

## **3\. Experiment 1 — MobileNetV3\-Small Baseline**

A pretrained MobileNetV3-Small architecture was used.
The feature extractor was frozen, and the final classification layer was trained for six disease classes.

### **Results**

* Training epochs: 20
* Best validation loss: 1.1003
* Best validation accuracy: 62.88% during training
* Validation accuracy at the best-loss checkpoint: 60.39%
* Validation macro F1-score: 54.00%
* Validation weighted F1-score: 63.00%

The model was also evaluated on the test partition during the earlier baseline experiment:

* Test accuracy: 55.00%
* Test macro F1-score: approximately 0.49
* Test weighted F1-score: approximately 0.58

The test results are retained as historical baseline results and were not used for Phase 5 model selection.

## **4\. Experiment 2 — Fine\-Tuned MobileNetV3\-Small**

The deeper feature extraction blocks (10–12) and classifier were unfrozen.
Differential learning rates were used:

* Feature extractor: 0.00001
* Classifier: 0.0001

### **Results**

* Training epochs: 15
* Best validation loss: 0.9248
* Validation accuracy at the best-loss checkpoint: 59.83%
* Validation macro F1-score: 54.00%
* Validation weighted F1-score: 62.00%

Fine-tuning improved some individual class metrics but did not improve overall macro F1 or validation accuracy compared with the baseline.

## **5\. Experiment 3 — EfficientNet\-B0**

A pretrained EfficientNet-B0 architecture was used.
The complete feature extractor was frozen, and only the final classifier was trained.

### **Training Configuration**

* Maximum epochs: 20
* Completed epochs: 20
* Trainable parameters: 7,686
* Total parameters: 4,015,234
* Training time: approximately 4.14 minutes
* Early stopping patience: 5

### **Training Results**

* Final training accuracy: 65.13%
* Best validation loss: 1.1952 at epoch 20
* Highest validation accuracy: 61.50% at epoch 19

### **Validation Results**

* Accuracy: 61.22%
* Macro precision: 51.81%
* Macro recall: 55.00%
* Macro F1-score: 52.59%
* Weighted F1-score: 61.96%

EfficientNet-B0 achieved the highest validation accuracy among the three experiments, but did not improve macro F1.

## **6\. Model Comparison**

| **Metric** | **MobileNetV3 Baseline** | **MobileNetV3 Fine-Tuned** | **EfficientNet-B0** |
| ------ | -------------------- | ---------------------- | --------------- |
| Accuracy | 60.39% | 59.83% | 61.22% |
| Macro Precision | 55.00% | 53.00% | 51.81% |
| Macro Recall | 61.00% | 60.00% | 55.00% |
| Macro F1 | 54.00% | 54.00% | 52.59% |
| Weighted F1 | 63.00% | 62.00% | 61.96% |

## **7\. Observations**

1. EfficientNet-B0 achieved the highest validation accuracy at 61.22%.
2. MobileNetV3-Small baseline achieved the highest macro recall and weighted F1.
3. MobileNetV3 fine-tuning did not produce an overall improvement.
4. SCC remained a difficult class for all experiments.
5. MEL had very few validation samples, so its class-wise metrics are uncertain.
6. Class imbalance remains an important challenge.
7. Validation accuracy alone is insufficient to judge model performance.

## **8\. Selected Research Baseline**

MobileNetV3-Small baseline is retained as the preferred research baseline because it provides stronger macro recall and weighted F1 than EfficientNet-B0.
EfficientNet-B0 is retained as a comparison experiment because it achieved slightly higher validation accuracy.
No model is claimed to be clinically validated or suitable for autonomous diagnosis.

## **9\. Limitations**

* Experiments use one dataset and one primary patient-safe split.
* The MEL validation support is only seven images.
* SCC performance remains limited.
* The dataset may not represent the full diversity of real-world skin images.
* No external clinical validation has been conducted.
* Test results from the original baseline experiment must not be interpreted as an independent comparison of all three models.

## **10\. Conclusion**

Phase 5 successfully implemented and compared three transfer-learning experiments.
EfficientNet-B0 achieved 61.22% validation accuracy, while MobileNetV3-Small baseline achieved better macro recall and weighted F1.
MobileNetV3-Small is retained as the preferred research baseline, and EfficientNet-B0 remains an alternative architecture for further investigation.
DermAI is an academic research and screening-support project, not an autonomous diagnostic system.
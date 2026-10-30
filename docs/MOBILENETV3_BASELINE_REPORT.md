# DermAI - MobileNetV3-Small Baseline Experiment

## 1. Experiment Overview

This experiment evaluates a pretrained MobileNetV3-Small model
for six-class skin lesion image classification using PAD-UFES-20.

The model uses transfer learning with a frozen feature extractor
and a newly initialized six-class classification layer.

This is a research prototype and is not validated for clinical
diagnosis or independent medical decision-making.

## 2. Dataset

Dataset: PAD-UFES-20

Total images: 2,298

Classes:
- ACK
- BCC
- MEL
- NEV
- SCC
- SEK

Patient-wise data partition:

| Partition | Images |
|---|---:|
| Training | 1,477 |
| Validation | 361 |
| Testing | 460 |
| Total | 2,298 |

Patient overlap between partitions: Zero.

## 3. Preprocessing

- Image format: RGB
- Image size: 224 x 224
- Interpolation: LANCZOS
- Input normalization: ImageNet mean and standard deviation
- Training augmentation: Random horizontal flip, vertical flip,
  and rotation up to 15 degrees.

## 4. Model Configuration

- Architecture: MobileNetV3-Small
- Pretrained weights: ImageNet
- Number of output classes: 6
- Training device: Apple MPS
- Optimizer: Adam
- Learning rate: 0.0001
- Weight decay: 0.0001
- Batch size: 16
- Maximum epochs: 20
- Loss: Weighted Cross Entropy
- Early stopping patience: 5
- Backbone: Frozen
- Trainable parameters: 6,150

## 5. Training Results

- Epochs completed: 20
- Final training loss: 1.0184
- Final training accuracy: 63.57%
- Best validation loss: 1.1003 (Epoch 20)
- Highest validation accuracy: 62.88% (Epoch 15)
- Best checkpoint selected using validation loss.

## 6. Final Test Results

The untouched test partition contained 460 images.

- Test accuracy: 55.00%
- Macro precision: 0.49
- Macro recall: 0.52
- Macro F1-score: 0.49
- Weighted F1-score: 0.58

### Class-wise Performance

| Class | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| ACK | 0.70 | 0.58 | 0.64 | 146 |
| BCC | 0.71 | 0.58 | 0.64 | 169 |
| MEL | 0.26 | 0.60 | 0.36 | 10 |
| NEV | 0.72 | 0.67 | 0.69 | 49 |
| SCC | 0.13 | 0.28 | 0.18 | 39 |
| SEK | 0.43 | 0.43 | 0.43 | 47 |

### Confusion Matrix

Rows represent actual classes and columns represent predictions.

| Actual / Predicted | ACK | BCC | MEL | NEV | SCC | SEK |
|---|---:|---:|---:|---:|---:|---:|
| ACK | 85 | 17 | 2 | 0 | 29 | 13 |
| BCC | 17 | 98 | 2 | 3 | 43 | 6 |
| MEL | 1 | 1 | 6 | 2 | 0 | 0 |
| NEV | 4 | 1 | 8 | 33 | 0 | 3 |
| SCC | 6 | 16 | 0 | 1 | 11 | 5 |
| SEK | 8 | 5 | 5 | 7 | 2 | 20 |

## 7. Observations and Limitations

- SCC has the weakest F1-score at 0.18.
- Several BCC and ACK images are incorrectly classified as SCC.
- MEL has only 10 test images, so its metrics have high uncertainty.
- The dataset has class imbalance.
- The frozen-backbone model is an initial transfer-learning baseline.
- Test results must not be used repeatedly for model selection.
- Results are specific to this dataset and experimental split.

## 8. Generated Artifacts

- ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth
- ml/outputs/plots/mobilenet_confusion_matrix.png
- ml/outputs/plots/mobilenet_loss_curve.png
- ml/outputs/plots/mobilenet_accuracy_curve.png
- ml/outputs/reports/mobilenet_training_history.csv

## 9. Conclusion

The MobileNetV3-Small baseline completed 20 training epochs
and achieved 55.00% accuracy on the held-out test partition.

The results establish an initial experimental baseline for
DermAI. Further research can investigate fine-tuning,
augmentation strategies, alternative architectures, and
class-wise performance improvements.

This system is a research and screening prototype, not a
clinically validated diagnostic tool.

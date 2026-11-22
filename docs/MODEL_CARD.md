# DermAI Model Card - mobilenet_v3_large_finetuned_epoch9

Research prototype. Not clinically validated; not a diagnostic device.

## Model package
| Item | Value |
|---|---|
| Version identifier | `mobilenet_v3_large_finetuned_epoch9` |
| Architecture | MobileNetV3-Large (torchvision), ImageNet-pretrained, final linear layer replaced (6 outputs) |
| Checkpoint | `ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth` (not in Git; override with `DERMAI_MODEL_CHECKPOINT`) |
| Class-to-index mapping | 0 ACK (actinic keratosis), 1 BCC (basal cell carcinoma), 2 MEL (melanoma), 3 NEV (nevus), 4 SCC (squamous cell carcinoma), 5 SEK (seborrheic keratosis); the checkpoint stores `class_names` and loading fails if they differ |
| Input | RGB, 224 x 224 |
| Normalisation | ImageNet mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]` |
| Output | softmax scores over the 6 classes, Top-3 list |

## Training
Dataset PAD-UFES-20 (2,298 images), patient-level split 1,477 / 361 / 460 (train / validation / test), seed 42. Weighted cross-entropy (weights from the training split), Adam, learning rate 1e-5, weight decay 1e-4, batch size 16, up to 20 epochs, ReduceLROnPlateau (patience 2), early stopping (patience 5), backbone frozen except `features[13:]` and `classifier[3]`, starting from the head-trained baseline. Best checkpoint (epoch 9) selected on validation loss. Augmentation on training data only. Details: `docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md`.

## Performance (single run)
| | Accuracy | Macro F1 |
|---|---|---|
| Validation | 61.22% | 56.53% |
| Test (460 images) | 57.39% | 51.02% |

Calibration (test): mean score 64.5% versus accuracy 57.4%; ECE 0.0739, 0.0429 after temperature scaling (T = 1.135, fitted on validation). Of 98 predictions scoring 0.8 or higher, 14 were wrong. Rare classes (MEL, SCC) have few samples and low F1. See `docs/CALIBRATION_REPORT.md`.

## Intended use and limits
Intended for research and decision-support demonstration on skin photographs. Not for diagnosis, treatment decisions, severity or risk assessment, or lesion segmentation. Scores are not clinically validated probabilities. No external validation; small dataset; photographs from one source population. Grad-CAM is a low-resolution explanation, not a lesion outline.

## Sample structured inference response
Real application output for test image `PAT_359_4450_86.png` (true class ACK), 2026-11-19; identifiers omitted.
```
{
  "model_version": "mobilenet_v3_large_finetuned_epoch9",
  "architecture": "MobileNetV3-Large",
  "predicted_label": "ACK",
  "confidence": 0.9804,
  "class_scores": {"ACK": 0.9804, "BCC": 0.0085, "MEL": 0.0003, "NEV": 0.0001, "SCC": 0.0057, "SEK": 0.0050},
  "top_predictions": [
    {"rank": 1, "class_name": "ACK", "score": 0.9804},
    {"rank": 2, "class_name": "BCC", "score": 0.0085},
    {"rank": 3, "class_name": "SCC", "score": 0.0057}
  ],
  "status": "completed",
  "created_at": "2026-11-19T10:40:45Z"
}
```
Other results from the same session: BCC image predicted BCC (79.0%); NEV image predicted SEK (46.2%); SCC image predicted ACK (81.0%).

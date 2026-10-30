\#\# Phase 2: Image Preprocessing
Status: COMPLETED
\#\#\# Implemented
\- Image loading with PIL\.
\- Conversion of images to RGB\.
\- Resizing to 224x224 using LANCZOS interpolation\.
\- Pixel normalization to the range \[0\, 1\]\.
\- Batch preprocessing with recursive subfolder support\.
\- Processed images saved in PNG format\.
\#\#\# Dataset Processing Results
\- Dataset: PAD\-UFES\-20
\- Original images: 2\,298
\- Successfully processed: 2\,298
\- Failed images: 0
\- Verified images: 2\,298
\- Image dimensions: 224x224
\- Color mode: RGB
\- Output format: PNG
\#\#\# Validation
All 2,298 processed images were independently verified.
No invalid images were found.
\#\#\# Output
ml/datasets/processed/pad\_ufes\_20/
Note: Processed image files are excluded from GitHub.
Normalization is applied during model input preparation.

## **Phase 5: Model Improvement and Comparison — Completed**

Three transfer-learning experiments were conducted using the PAD-UFES-20 dataset.

### **Experiments**

1. MobileNetV3-Small baseline
2. Fine-tuned MobileNetV3-Small
3. EfficientNet-B0 transfer learning

### **Validation Comparison**

| **Metric** | **MobileNetV3 Baseline** | **Fine-Tuned MobileNetV3** | **EfficientNet-B0** |
| ------ | -------------------- | ---------------------- | --------------- |
| Accuracy | 60.39% | 59.83% | 61.22% |
| Macro Precision | 55.00% | 53.00% | 51.81% |
| Macro Recall | 61.00% | 60.00% | 55.00% |
| Macro F1 | 54.00% | 54.00% | 52.59% |
| Weighted F1 | 63.00% | 62.00% | 61.96% |

### **Outcome**

* EfficientNet-B0 achieved the highest validation accuracy.
* MobileNetV3-Small baseline achieved the highest macro recall and weighted F1.
* MobileNetV3-Small baseline remains the preferred research baseline.
* Fine-tuning did not improve overall validation performance.

### **Artifacts**

* `docs/PHASE5_MODEL_COMPARISON_REPORT.md`
* `ml/outputs/reports/phase5_model_comparison.csv`
* `ml/checkpoints/efficientnet/best_efficientnet_b0.pth` (ignored by Git)

### **Limitations**

The test partition was not used for Phase 5 model selection. Results are based on one patient-safe validation split. External clinical validation has not been performed.
DermAI remains an academic research and screening-support project, not an autonomous diagnostic system.
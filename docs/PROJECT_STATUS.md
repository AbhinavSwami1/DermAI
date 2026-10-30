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
## **Phase 6: Lesion Localization and Explainability — Completed**

### Annotation Audit

The locally available PAD-UFES-20 and Fitzpatrick17k dataset files
were inspected for spatial annotations.

- Image-level diagnostic labels are available.
- No bounding-box coordinates or segmentation masks were identified
  in the inspected local dataset files.
- Lesion measurements and anatomical body-region metadata are not
  pixel-level localization annotations.

### Approach

Grad-CAM was implemented using the trained MobileNetV3-Small
baseline checkpoint.

The prototype generates class-discriminative activation heatmaps
and overlays them on the original input images.

### Qualitative Evaluation

Six held-out test examples were visualized, one from each
PAD-UFES-20 diagnostic class.

- Generated visualizations: 6
- Correct classifications among these examples: 4
- Lesion-focused activation was observed in several examples.
- Background activation and partial lesion coverage were also
  observed.
- Correct classification did not always imply reliable
  lesion-focused activation.

These six examples are illustrative and do not establish
localization performance.

### Evaluation Limitations

No ground-truth spatial annotations were available in the
inspected local dataset files. Therefore, Dice, IoU and
bounding-box localization metrics could not be calculated.

Grad-CAM is an explainability visualization, not a verified
lesion segmentation or boundary-detection method.

### Artifacts

- `docs/GRADCAM_LOCALIZATION_REPORT.md`
- `ml/src/explainability/gradcam.py`
- `ml/src/explainability/generate_visualizations.py`
- `ml/outputs/gradcam/` (generated visualizations and CSV;
  excluded from Git if covered by `.gitignore`)

### Conclusion

The Grad-CAM prototype was integrated with the existing
classification workflow as an experimental explainability
component. Further evaluation with spatially annotated data
and a larger sample is required.

DermAI remains an academic research prototype and is not
a clinically validated diagnostic system.

---

## W2.3 — FastAPI Backend Foundation

### Implemented Components

- Initialized the FastAPI application.
- Added root endpoint: `GET /`.
- Added health endpoint: `GET /health`.
- Added image upload endpoint: `POST /api/v1/upload`.
- Implemented JPEG and PNG image format validation.
- Added a maximum upload size limit of 10 MB.
- Added minimum image dimensions validation of 224 x 224 pixels.
- Added corrupted and unsupported image rejection.
- Implemented UUID-based filenames for uploaded images.
- Added original image storage under `backend/storage/original/`.

### Automated Testing

Created automated API tests using pytest and FastAPI TestClient.

| Test Case | Result |
|---|---|
| Valid PNG upload | Passed |
| Valid JPEG upload | Passed |
| Corrupted image rejection | Passed |
| Unsupported GIF rejection | Passed |
| Small image rejection | Passed |
| Oversized file rejection | Passed |

**Test Summary:** 6 passed, 0 failed.

### Current Limitations

- Database integration is pending.
- User authentication and authorization are pending.
- Uploaded images are stored locally.
- Case and prediction records are not yet created.
- Image upload validation does not establish diagnostic accuracy.

### Conclusion

The initial FastAPI backend and image upload validation workflow
have been implemented and tested successfully. Database
integration, authentication, and model inference API integration
remain future development tasks.

DermAI is an academic research prototype and is not a clinically
validated diagnostic system.

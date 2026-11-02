DermAI — Project Status

Last updated: November 2026
Project type: Academic research prototype
Selected model: Fine-tuned MobileNetV3-Large
Model version: mobilenet_v3_large_finetuned_epoch9

1. Project Overview

DermAI is a research-oriented skin lesion image analysis prototype developed using PAD-UFES-20 and Fitzpatrick17k datasets.

The system includes:

* Image upload and validation.
* User authentication and authorization.
* Case and image management.
* Image quality assessment.
* Deep-learning-based classification.
* Prediction history and persistence.
* Grad-CAM explainability visualizations.
* Research performance dashboards.

DermAI is not clinically validated and must not be used as a substitute for professional medical diagnosis or treatment.

2. Dataset Audit

PAD-UFES-20

Property	Audited result
Original images	2,298
Metadata columns	26
Unique patients	1,373
Unique lesions	1,641
Patient-lesion combinations	1,891
Successfully matched images	2,298
Missing or unlisted images	0

The dataset audit report records image readability, file formats, dimensions, diagnostic labels, missing metadata and duplicate-risk checks.

Dataset splitting

A patient-grouped, stratified five-fold splitting approach was implemented to reduce patient-level leakage.

The selected split contains:

Partition	Images	Patients
Training	1,477	880
Validation	361	220
Testing	460	273
Total	2,298	1,373

The selected split was checked for patient and image overlap.

Reference: docs/PAD_UFES_20_AUDIT_REPORT.md

Note: Diagnostic class counts should be taken from the verified dataset audit, not inferred from the held-out test distribution.

3. Image Preprocessing

Standalone preprocessing utility

File: ml/src/preprocessing/image_preprocessing.py

Implemented operations:

* Image loading using Pillow.
* RGB conversion.
* Resizing to 224 × 224 using LANCZOS.
* Pixel scaling from 0–255 to 0–1.
* Batch preprocessing with recursive subfolder support.

The dataset processing report records 2,298 successfully processed images and zero failures.

Output directory:

ml/datasets/processed/pad_ufes_20/

Processed image files are excluded from Git.

Actual model training transformations

File: ml/src/data/augmentations.py

Training:

* Random horizontal flip.
* Random vertical flip.
* Random rotation up to 15 degrees.
* Tensor conversion.
* ImageNet normalization.

Validation and testing:

* Tensor conversion.
* ImageNet normalization.

The training and evaluation scripts explicitly pass these transformations to DermAIDataset.

Backend inference transformations

File: backend/app/services/inference_service.py

* EXIF orientation correction.
* RGB conversion.
* Resize to 224 × 224 using LANCZOS.
* Tensor conversion.
* ImageNet normalization.

The standalone preprocessing utility’s 0–1 scaling is distinct from the ImageNet-normalized model input pipeline.

4. Model Training and Evaluation

Selected model

Fine-tuned MobileNetV3-Large

* Architecture: MobileNetV3-Large.
* Input size: 224 × 224.
* Number of classes: 6.
* Selected checkpoint: ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth
* Model version: mobilenet_v3_large_finetuned_epoch9
* Best checkpoint selected using validation loss.

Held-out test performance

Evaluation artifact:

ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json

Metric	Test result
Test samples	460
Accuracy	57.39%
Macro Precision	52.44%
Weighted Precision	65.48%
Macro Recall	52.70%
Weighted Recall	57.39%
Macro F1-score	51.02%
Weighted F1-score	60.12%

Per-class test F1-score

Class	F1-score
ACK	69.89%
BCC	61.22%
MEL	28.57%
NEV	68.57%
SCC	25.00%
SEK	52.87%

Performance varies across classes, and minority-class performance remains a limitation.

Validation comparison

The saved validation comparison for MobileNetV3-Large shows:

Metric	Baseline	Fine-tuned
Accuracy	58.45%	61.22%
Macro Precision	53.14%	56.85%
Macro Recall	59.43%	61.34%
Macro F1	53.63%	56.53%
Weighted F1	59.75%	63.61%

These are validation results, not held-out test results.

EfficientNet-B0 was also implemented as a separate transfer-learning experiment. Model comparisons must retain their evaluation split and metric provenance.

Evaluation artifacts

ml/outputs/mobilenet_v3_large_finetuned/

Includes:

* Test metrics JSON.
* Test classification report.
* Test confusion matrix.
* Test predictions.
* Validation classification report.
* Validation confusion matrix.
* Training history.
* Accuracy and loss curves.

5. Grad-CAM Explainability

Grad-CAM is integrated into the backend prediction workflow.

Selected checkpoint: Fine-tuned MobileNetV3-Large, epoch 9.

Implementation:

* ml/src/explainability/gradcam.py
* ml/src/explainability/generate_visualizations.py
* backend/app/services/gradcam_service.py

The system generates class-discriminative activation heatmaps and overlays.

The local dataset audit did not identify ground-truth segmentation masks or bounding-box annotations in the inspected files. Therefore, Grad-CAM visualizations are qualitative explanations and not verified lesion segmentation.

Dice, IoU and localization accuracy must not be claimed without suitable spatial ground truth.

Reference: docs/GRADCAM_LOCALIZATION_REPORT.md

6. FastAPI Backend

Implemented components:

* FastAPI application.
* Root and health endpoints.
* User registration and profile APIs.
* Case creation and retrieval APIs.
* Image upload and retrieval APIs.
* Prediction API.
* Grad-CAM API.
* PostgreSQL persistence.
* Image validation and local storage.

Image upload validation

* JPEG and PNG validation.
* Maximum upload size: 10 MB.
* Minimum dimensions: 224 × 224.
* Corrupt and unsupported image rejection.
* UUID-based storage filenames.
* Original image storage under backend storage.

7. PostgreSQL Database

Database: derm_ai_db

SQLAlchemy ORM models:

1. Users
2. Roles
3. User Roles
4. Cases
5. Images
6. Model Versions
7. Predictions
8. Refresh Tokens
9. Image Quality Assessments

Migration history

Revision	Description
244e263f1f95	Initial DermAI schema
cf242a5da3ba	Refresh token table
e93c9c1565a8	Image quality assessments

Current revision:

e93c9c1565a8 (head)

Alembic verification:

No new upgrade operations detected.

This confirms no pending schema differences were detected at the time of verification.

8. Authentication and Security

Implemented:

* Argon2 password hashing.
* JWT access tokens.
* Protected API endpoints.
* Authenticated user dependency.
* Case and image ownership enforcement.
* Role-based access control.
* Patient role assignment.
* Administrator role provisioning.
* Refresh token generation and hashed storage.
* Refresh token rotation.
* Token-family tracking and reuse detection.
* Logout and token revocation.
* Login rate limiting.

Authentication configuration

Setting	Configuration
Access token algorithm	HS256
Access token expiration	30 minutes
Refresh token expiration	7 days
Refresh token storage	SHA-256 hash
Refresh token delivery	HttpOnly cookie
Login rate limit	5 attempts per minute

Remaining security considerations

* Redis-backed shared rate-limit storage for multi-worker deployments.
* CSRF protection review.
* HTTPS enforcement in production.
* Additional production security and deployment hardening.

9. Frontend Integration

The React frontend provides:

* User authentication.
* Image selection and preview.
* Image quality feedback.
* Prediction display.
* Class-score visualization.
* Grad-CAM visualization.
* Prediction history.
* Research performance dashboard.
* Research-only disclaimer.

Frontend production build was successfully verified using:

npm run build

10. Automated Testing

Latest verified backend test command:

PYTHONPATH="$PWD:$PWD/backend" pytest -q backend/tests/

Result:

73 passed, 0 failed.

Two non-blocking deprecation warnings were reported.

Frontend TypeScript checking and Vite production build also passed.

11. Known Limitations and Future Work

* The model is not clinically validated.
* Test accuracy and class-wise performance require further improvement.
* Minority-class performance remains limited.
* External dataset validation is required.
* Image quality thresholds are heuristic and require calibration.
* Grad-CAM is not a segmentation model.
* Production deployment requires additional security hardening.
* Performance, latency and clinical utility require separate evaluation.

12. Overall Project Status

The DermAI research prototype includes a working frontend, FastAPI backend, PostgreSQL persistence, authentication, image quality assessment, MobileNetV3-Large inference and Grad-CAM visualization.

The selected model has been evaluated on a held-out test partition of 460 images.

The implementation has passed 73 backend automated tests, and the frontend production build has been verified.

Final status: Research prototype implemented; further model evaluation, external validation and production hardening remain necessary.

Medical disclaimer: DermAI is an academic research prototype, not a clinically validated diagnostic system. Its predictions must not be used to make medical decisions.
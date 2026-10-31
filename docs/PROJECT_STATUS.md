Phase 2: Image Preprocessing

Status: COMPLETED

Implemented

* Image loading with PIL.
* Conversion of images to RGB.
* Resizing to 224x224 using LANCZOS interpolation.
* Pixel normalization to the range [0, 1].
* Batch preprocessing with recursive subfolder support.
* Processed images saved in PNG format.

Dataset Processing Results

* Dataset: PAD-UFES-20
* Original images: 2,298
* Successfully processed: 2,298
* Failed images: 0
* Verified images: 2,298
* Image dimensions: 224x224
* Color mode: RGB
* Output format: PNG

Validation

All 2,298 processed images were independently verified.
No invalid images were found.

Output

ml/datasets/processed/pad_ufes_20/

Note: Processed image files are excluded from GitHub. Normalization is applied during model input preparation.

⸻

Phase 5: Model Improvement and Comparison — Completed

Three transfer-learning experiments were conducted using the PAD-UFES-20 dataset.

Experiments

1. MobileNetV3-Small baseline
2. Fine-tuned MobileNetV3-Small
3. EfficientNet-B0 transfer learning

Validation Comparison

Metric	MobileNetV3 Baseline	Fine-Tuned MobileNetV3	EfficientNet-B0
Accuracy	60.39%	59.83%	61.22%
Macro Precision	55.00%	53.00%	51.81%
Macro Recall	61.00%	60.00%	55.00%
Macro F1	54.00%	54.00%	52.59%
Weighted F1	63.00%	62.00%	61.96%

Outcome

* EfficientNet-B0 achieved the highest validation accuracy.
* MobileNetV3-Small baseline achieved the highest macro recall and weighted F1.
* MobileNetV3-Small baseline remains the preferred research baseline.
* Fine-tuning did not improve overall validation performance.

Artifacts

* docs/PHASE5_MODEL_COMPARISON_REPORT.md
* ml/outputs/reports/phase5_model_comparison.csv
* ml/checkpoints/efficientnet/best_efficientnet_b0.pth (ignored by Git)

Limitations

The test partition was not used for Phase 5 model selection. Results are based on one patient-safe validation split. External clinical validation has not been performed.

DermAI remains an academic research and screening-support project, not an autonomous diagnostic system.

⸻

Phase 6: Lesion Localization and Explainability — Completed

Annotation Audit

The locally available PAD-UFES-20 and Fitzpatrick17k dataset files were inspected for spatial annotations.

* Image-level diagnostic labels are available.
* No bounding-box coordinates or segmentation masks were identified in the inspected local dataset files.
* Lesion measurements and anatomical body-region metadata are not pixel-level localization annotations.

Approach

Grad-CAM was implemented using the trained MobileNetV3-Small baseline checkpoint.

The prototype generates class-discriminative activation heatmaps and overlays them on the original input images.

Qualitative Evaluation

Six held-out test examples were visualized, one from each PAD-UFES-20 diagnostic class.

* Generated visualizations: 6
* Correct classifications among these examples: 4
* Lesion-focused activation was observed in several examples.
* Background activation and partial lesion coverage were also observed.
* Correct classification did not always imply reliable lesion-focused activation.

These six examples are illustrative and do not establish localization performance.

Evaluation Limitations

No ground-truth spatial annotations were available in the inspected local dataset files. Therefore, Dice, IoU and bounding-box localization metrics could not be calculated.

Grad-CAM is an explainability visualization, not a verified lesion segmentation or boundary-detection method.

Artifacts

* docs/GRADCAM_LOCALIZATION_REPORT.md
* ml/src/explainability/gradcam.py
* ml/src/explainability/generate_visualizations.py
* ml/outputs/gradcam/ (generated visualizations and CSV; excluded from Git if covered by .gitignore)

Conclusion

The Grad-CAM prototype was integrated with the existing classification workflow as an experimental explainability component. Further evaluation with spatially annotated data and a larger sample is required.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

⸻

W2.3 — FastAPI Backend Foundation

Implemented Components

* Initialized the FastAPI application.
* Added root endpoint: GET /.
* Added health endpoint: GET /health.
* Added image upload endpoint: POST /api/v1/upload.
* Implemented JPEG and PNG image format validation.
* Added a maximum upload size limit of 10 MB.
* Added minimum image dimensions validation of 224 x 224 pixels.
* Added corrupted and unsupported image rejection.
* Implemented UUID-based filenames for uploaded images.
* Added original image storage under backend/storage/original/.

Automated Testing

Created automated API tests using pytest and FastAPI TestClient.

Test Case	Result
Valid PNG upload	Passed
Valid JPEG upload	Passed
Corrupted image rejection	Passed
Unsupported GIF rejection	Passed
Small image rejection	Passed
Oversized file rejection	Passed

Test Summary: 6 passed, 0 failed.

Current Limitations

* Database integration is pending.
* User authentication and authorization are pending.
* Uploaded images are stored locally.
* Case and prediction records are not yet created.
* Image upload validation does not establish diagnostic accuracy.

Conclusion

The initial FastAPI backend and image upload validation workflow have been implemented and tested successfully. Database integration, authentication, and model inference API integration remain future development tasks.

DermAI is an academic research prototype and is not a clinically validated diagnostic system.

⸻

W2.4 — PostgreSQL Database Integration

Implemented Components

* Created a dedicated PostgreSQL database named derm_ai_db.
* Integrated PostgreSQL with SQLAlchemy ORM.
* Implemented database engine and session management.
* Created seven SQLAlchemy ORM models:
    * Users
    * Roles
    * User Roles
    * Cases
    * Images
    * Model Versions
    * Predictions
* Implemented primary keys, foreign keys, and unique constraints.
* Configured UUID-based identifiers.
* Added PostgreSQL JSONB support for prediction class scores.
* Integrated Alembic for database schema migrations.
* Generated and successfully applied the initial database migration.
* Configured database connection using environment variables through backend/.env.
* Added alembic to backend requirements.

Database Tables

Table	Purpose
users	Stores user account information
roles	Stores available user roles
user_roles	Maps users to roles
cases	Stores user-associated cases
images	Stores uploaded image metadata
model_versions	Tracks model versions
predictions	Stores model prediction records

Database Verification

Verification	Result
PostgreSQL connection	Passed
SQLAlchemy connection	Passed
ORM model registration	7 tables loaded
Database migration	Applied successfully
Database tables	7 application tables created
Foreign-key relationships	6 verified
Alembic migration status	Current revision verified
Environment-based configuration	Passed

Migration Revision: 244e263f1f95
Database: derm_ai_db

Current Limitations

* User authentication and authorization are pending.
* API endpoints are not yet integrated with database operations.
* Image upload currently stores files locally.
* Case and prediction records are not yet automatically created through API workflows.
* Model inference API integration is pending.
* Database migration and schema creation do not establish diagnostic accuracy.

Conclusion

The PostgreSQL database foundation has been implemented using SQLAlchemy and Alembic. Seven database tables, their primary and foreign-key relationships, and environment-based database configuration have been successfully established and verified.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

W2.5 — FastAPI and PostgreSQL CRUD Integration

Status: Completed

Implemented:

* PostgreSQL database session dependency using SQLAlchemy.
* User registration API with Argon2 password hashing.
* Pydantic request and response schemas.
* Case creation and retrieval APIs.
* Image upload integrated with PostgreSQL metadata persistence.
* Image-to-case foreign key relationship.
* Image validation and local file storage.
* Isolated PostgreSQL test database for automated testing.

API Endpoints

Method	Endpoint	Purpose
POST	/api/v1/users/register	Register user
POST	/api/v1/cases	Create case
GET	/api/v1/users/{owner_id}/cases	Retrieve user cases
GET	/api/v1/cases/{case_id}	Retrieve individual case
POST	/api/v1/upload	Upload image and save metadata

Testing

* Total automated tests: 15
* Passed: 15
* Failed: 0

Security limitation: Authentication, authorization, and ownership enforcement are still pending. Current case endpoints are development-stage APIs and are not production-ready for access control.

## W2.6 — JWT Authentication and Authorization

Status: Completed

### Implemented Features

* JWT-based access token generation using PyJWT.
* Configurable JWT secret, algorithm, and token expiration.
* User login API with email and password verification.
* Argon2 password hash verification.
* HTTP Bearer token authentication.
* Current authenticated user dependency.
* Protected user profile endpoint.
* Case ownership enforcement.
* Authenticated case creation.
* Prevention of cross-user case access.
* Protected image upload endpoint.
* Prevention of image uploads to another user's case.
* Authentication and authorization test coverage.

### Authentication API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/v1/auth/login | Authenticate user and generate JWT |
| GET | /api/v1/users/me | Retrieve authenticated user profile |

### Authorization

* Unauthenticated requests to protected endpoints are rejected.
* Users can create cases only for themselves.
* Users can retrieve only their own cases.
* Users cannot access another user's cases.
* Image uploads require authentication.
* Images can only be uploaded to cases owned by the authenticated user.
* Invalid or expired tokens are rejected.

### Security Measures

* Argon2 password hashing.
* JWT access tokens using HS256.
* Configurable 30-minute access token expiration.
* JWT secret stored in backend/.env.
* Environment template contains only a placeholder secret.
* Password hashes are excluded from API responses.

### Automated Testing

* Case API tests: 7 passed.
* Image upload tests: 8 passed.
* User API tests: 8 passed.
* Role API tests: 5 passed.
* Database tests: 1 passed.
* Total tests: 29 passed.
* Failed tests: 0.

### Current Limitations

* Role-based authorization (RBAC), default Patient assignment, and Administrator role provisioning are completed.
* Refresh token and logout/revocation mechanisms are pending.
* Image files are currently stored locally.
* Model inference API integration is pending.
* Additional production security hardening is required.

### Conclusion

JWT authentication, ownership-based authorization, and role-based access control (RBAC) have been integrated into the DermAI FastAPI backend. Public registration automatically assigns the Patient role, while only Administrators can assign additional roles. The first Administrator has been provisioned through a controlled database operation. These workflows have been verified through 29 automated tests.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.


W2.8 — Login Rate Limiting

Status: Completed

Implemented Features

* Integrated SlowAPI for API rate limiting.
* Configured login endpoint to allow a maximum of 5 attempts per minute per client IP.
* Requests exceeding the configured limit receive HTTP 429 (Too Many Requests).
* Configured rate-limit exception handling in the FastAPI application.
* Enabled rate-limit response headers.
* Used direct client IP identification without trusting forwarded IP headers by default.
* Added automated login rate-limit security testing.
* Added rate-limiter reset fixtures to maintain test isolation.

Security Configuration

Setting	Configuration
Protected endpoint	POST /api/v1/auth/login
Maximum attempts	5
Time window	1 minute
Rate-limit library	SlowAPI 0.1.10
Exceeded limit response	HTTP 429
Client identification	Direct IP address

Automated Testing

* Login rate-limit security test: 1 passed.
* Case API tests: 7 passed.
* Image upload tests: 8 passed.
* User API tests: 8 passed.
* Role API tests: 5 passed.
* Database tests: 1 passed.
* Total automated tests: 30 passed.
* Failed tests: 0.

Current Limitations

* Rate-limit storage is currently process-local. Redis-backed shared storage should be configured before deploying across multiple workers or servers.
* Refresh token and logout/revocation mechanisms are pending.
* Image files are currently stored locally.
* Model inference API integration is pending.
* Additional production security hardening is required.

Conclusion

Login rate limiting has been integrated into the DermAI FastAPI backend using SlowAPI. The login endpoint limits clients to five attempts per minute and rejects excess requests with HTTP 429. The complete backend test suite passes all 30 automated tests.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

## W2.9 — Refresh Token Lifecycle Management

**Status: Completed**

### Implemented Features

- Database-backed refresh token management.
- Cryptographically secure opaque refresh token generation.
- SHA-256 hashing before PostgreSQL storage.
- Seven-day refresh token expiration.
- HttpOnly refresh token cookies.
- Refresh token rotation after successful refresh requests.
- Token-family tracking using UUIDs.
- Refresh token reuse detection and family revocation.
- Logout with refresh token revocation and cookie clearing.
- Unique JWT ID (`jti`) claims for access tokens.

### Authentication Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate and issue access and refresh tokens |
| POST | `/api/v1/auth/refresh` | Rotate refresh token and issue a new access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token and clear authentication cookie |

### Security Configuration

| Setting | Configuration |
|---|---|
| Access token algorithm | HS256 |
| Access token expiration | 30 minutes |
| Refresh token expiration | 7 days |
| Refresh token storage | SHA-256 hash |
| Refresh token delivery | HttpOnly cookie |
| Cookie SameSite | Lax |
| Cookie Secure | Configurable |
| Token rotation | Enabled |
| Reuse detection | Enabled |
| Token-family revocation | Enabled |

### Automated Testing

- Refresh token persistence: passed.
- Refresh token expiration: passed.
- Refresh token rotation: passed.
- Token-family revocation: passed.
- Secure refresh cookie: passed.
- Refresh API: passed.
- Logout and cookie clearing: passed.
- Refresh token replay protection: passed.
- Complete backend regression suite: **38 passed, 0 failed**.

### Security Limitations

- Previously issued access JWTs remain valid until expiration, even after logout.
- CSRF protections require additional review before production deployment.
- Redis-backed rate-limit storage is recommended for multi-worker deployments.
- HTTPS and the Secure cookie attribute must be enforced in production.

### Conclusion

The DermAI backend now supports refresh token generation, hashed database storage, token rotation, reuse detection, token-family revocation, and logout.

All 38 backend automated tests pass.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

---

# W3.0 — Deep Learning Model Inference API Integration

### Model Integration

- Integrated the trained MobileNetV3-Small baseline checkpoint.
- Checkpoint: `ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth`.
- Implemented lazy model loading and inference-device selection (CUDA, Apple MPS, or CPU).
- Added RGB image preprocessing and resizing to 224×224.
- Applied ImageNet normalization.
- Added six-class probability generation using softmax.

### Class Mapping

| Index | Class |
|---|---|
| 0 | ACK |
| 1 | BCC |
| 2 | MEL |
| 3 | NEV |
| 4 | SCC |
| 5 | SEK |

### Prediction API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/predictions/{image_id}` | Generate and save a prediction for an uploaded image |

- Requires authentication.
- Verifies image ownership before inference.
- Validates the stored image before processing.
- Saves prediction results and class scores in PostgreSQL.
- Associates predictions with a registered model version.
- Returns predicted class, confidence, class scores, model metadata, and timestamp.
- Includes a research-only disclaimer.

### Dependencies

- PyTorch 2.15.0
- Torchvision 0.29.2

### Automated Testing

- Inference preprocessing: passed.
- Six-class probability output: passed.
- Empty and corrupted image rejection: passed.
- Prediction generation and database persistence: passed.
- Authentication enforcement: passed.
- Image ownership protection: passed.
- Non-existent image rejection: passed.
- Inference failure handling (HTTP 503): passed.
- Storage path traversal protection: passed.
- Complete backend regression suite: **48 passed, 0 failed**.

Two non-blocking deprecation warnings remain in the test environment.

### Research Limitations

- Predictions are experimental model outputs, not confirmed diagnoses.
- The model was evaluated on the PAD-UFES-20 dataset; generalization to other populations and image sources is not established.
- The prediction API does not establish clinical validity or diagnostic safety.
- Production deployment requires further security, performance, and deployment validation.

### Conclusion

W3.0 integrates the MobileNetV3-Small research baseline into the authenticated DermAI backend, with image preprocessing, six-class inference, database persistence, and model-version tracking.

The complete backend test suite passes with 48 tests and zero failures.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

---

# W3.1 — Grad-CAM Explainability API Integration

### Explainability Integration

- Integrated the existing Grad-CAM implementation into the backend.
- Reused the trained MobileNetV3-Small baseline checkpoint.
- Target convolutional layer: `model.features[-1]`.
- Implemented gradient-based class activation heatmap generation.
- Applied ReLU and min-max normalization to the activation map.
- Resized the heatmap to match the original image dimensions.
- Generated colored overlays using the JET colormap with 45% opacity.
- Added EXIF orientation correction for uploaded images.
- Implemented hook cleanup and model gradient cleanup.
- Added a shared execution lock to synchronize normal prediction and Grad-CAM operations on the cached model.

### Grad-CAM API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/predictions/{image_id}/gradcam` | Generate a Grad-CAM visualization for an uploaded image |

- Requires authentication.
- Verifies image ownership before visualization.
- Validates stored images before processing.
- Returns the visualization as a PNG response.
- Uses `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.
- Does not create duplicate prediction records.
- Does not permanently store generated visualizations.
- Includes a research-only disclaimer in the response headers.

### Implementation Files

- `backend/app/services/gradcam_service.py`
- `backend/app/api/predictions.py`
- `backend/tests/test_predictions.py`
- Existing implementation: `ml/src/explainability/gradcam.py`

### Dependencies

- NumPy 2.4.6
- Matplotlib 3.11.2
- Pillow

### Automated Testing

- Grad-CAM PNG response generation: passed.
- PNG content type and response headers: passed.
- Authentication enforcement: passed.
- Image ownership protection: passed.
- Non-existent image rejection: passed.
- Grad-CAM generation failure handling (HTTP 503): passed.
- Storage path traversal protection: passed.
- Full backend regression suite: **54 passed, 0 failed**.

Two non-blocking deprecation warnings remain in the test environment.

### Research Limitations

- Grad-CAM visualizations represent model activation patterns, not verified lesion boundaries.
- Heatmaps do not establish the model's clinical reasoning or diagnostic correctness.
- Visualizations generated from synthetic images are pipeline tests, not meaningful medical results.
- Clinical validity, diagnostic safety, and generalization remain unestablished.
- Further evaluation is required before any clinical application.

### Conclusion

W3.1 integrates Grad-CAM explainability into the authenticated DermAI backend through a dedicated visualization API.

The implementation reuses the trained MobileNetV3-Small baseline and returns PNG overlays without modifying the existing prediction workflow.

The complete backend test suite passes with 54 tests and zero failures.

DermAI remains an academic research prototype and is not a clinically validated diagnostic system.

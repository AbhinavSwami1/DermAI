DermAI — System Architecture and Database ER Diagrams

1. Project Overview

DermAI is a research-oriented skin lesion image analysis prototype. It provides image upload, image quality assessment, machine-learning inference, prediction history, and Grad-CAM visual explanations.

The system is not clinically validated and must not be used as a substitute for professional medical diagnosis or treatment.

2. Technology Stack

Layer	Technology
Frontend	React, TypeScript, Vite, Tailwind CSS
Backend	Python, FastAPI
Database	PostgreSQL
ORM	SQLAlchemy
Database migrations	Alembic
Authentication	JWT, Argon2 password hashing
Machine learning	PyTorch, Torchvision
Selected model	Fine-tuned MobileNetV3-Large
Image processing	Pillow, Torchvision
Explainability	Grad-CAM

3. System Architecture

The following diagram represents the major application components and their interactions.

flowchart TB
    U["User"] --> FE["React + TypeScript Frontend"]
    FE --> API["FastAPI Backend"]
    API --> AUTH["Authentication and Authorization"]
    API --> UPLOAD["Image Upload API"]
    API --> CASE["Case Management API"]
    API --> PRED["Prediction API"]
    API --> HISTORY["Image and Prediction History API"]
    AUTH --> SEC["JWT and Password Security"]
    AUTH --> DB[("PostgreSQL Database")]
    UPLOAD --> VALID["Image Validation"]
    VALID --> QUALITY["Image Quality Assessment"]
    VALID --> STORAGE["Image File Storage"]
    QUALITY --> DB
    CASE --> DB
    HISTORY --> DB
    PRED --> INFER["Inference Service"]
    STORAGE --> INFER
    INFER --> PRE["Image Preprocessing"]
    PRE --> MODEL["Fine-tuned MobileNetV3-Large"]
    MODEL --> RESULT["Prediction and Class Scores"]
    RESULT --> DB
    RESULT --> FE
    PRED --> EXPLAIN["Grad-CAM Service"]
    EXPLAIN --> MODEL
    EXPLAIN --> HEATMAP["Grad-CAM Visualization"]
    HEATMAP --> FE

Architecture Components

Component	Responsibility
React Frontend	User interface, image upload, predictions, history and visualizations
FastAPI Backend	API routing, request validation and application logic
Authentication	User registration, login, token validation and authorization
Image Upload API	Image validation and upload processing
Image Quality Assessment	Calculates image-quality indicators and quality status
Image File Storage	Stores uploaded image files
PostgreSQL	Stores users, cases, image metadata, predictions and related records
Inference Service	Loads the selected model and performs classification
Preprocessing	Converts uploaded images into model-compatible tensors
MobileNetV3-Large	Produces six-class prediction scores
Grad-CAM Service	Generates class-discriminative activation visualizations

4. Image Processing and Inference Pipeline

The selected model’s backend inference pipeline performs the following operations:

1. Read uploaded image bytes.
2. Correct EXIF orientation.
3. Convert the image to RGB.
4. Resize the image to 224 × 224 pixels using LANCZOS interpolation.
5. Convert the image into a PyTorch tensor.
6. Apply ImageNet normalization.
7. Run MobileNetV3-Large inference.
8. Generate six-class probability scores.
9. Return the predicted class, confidence, class scores and model version.

Training and Evaluation Transformations

Training transformations:

* Random horizontal flip.
* Random vertical flip.
* Random rotation up to 15 degrees.
* Tensor conversion.
* ImageNet normalization.

Validation and testing transformations:

* Tensor conversion.
* ImageNet normalization.

The separate ml/src/preprocessing/image_preprocessing.py utility performs RGB conversion, 224 × 224 resizing and pixel scaling from 0–255 to 0–1.

This standalone utility is distinct from the selected model’s ImageNet-normalized training and inference pipeline.

Model Configuration

Configuration	Value
Selected architecture	MobileNetV3-Large
Model type	Fine-tuned transfer-learning model
Input dimensions	224 × 224
Number of output classes	6
Normalization	ImageNet mean and standard deviation
Checkpoint	ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth
Model version	mobilenet_v3_large_finetuned_epoch9

5. Database ER Diagram

The DermAI database contains nine SQLAlchemy ORM model tables. The following diagram represents their primary relationships.

erDiagram
    USERS ||--o{ CASES : owns
    USERS ||--o{ USER_ROLES : assigned
    ROLES ||--o{ USER_ROLES : contains
    USERS ||--o{ REFRESH_TOKENS : has
    CASES ||--o{ IMAGES : contains
    IMAGES ||--o{ PREDICTIONS : produces
    IMAGES ||--o{ IMAGE_QUALITY_ASSESSMENTS : receives
    MODEL_VERSIONS ||--o{ PREDICTIONS : used_for
    REFRESH_TOKENS o|--o{ REFRESH_TOKENS : replaces
    USERS {
        uuid user_id PK
        string email UK
        text password_hash
        string full_name
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    ROLES {
        uuid role_id PK
        string role_name UK
        text description
    }
    USER_ROLES {
        uuid user_id PK, FK
        uuid role_id PK, FK
        datetime assigned_at
    }
    CASES {
        uuid case_id PK
        uuid owner_id FK
        string status
        datetime created_at
        datetime updated_at
    }
    IMAGES {
        uuid image_id PK
        uuid case_id FK
        string original_filename
        string mime_type
        bigint file_size_bytes
        text storage_key UK
        integer width
        integer height
        datetime uploaded_at
    }
    MODEL_VERSIONS {
        uuid model_version_id PK
        string model_name
        string version
        string architecture
        text checkpoint_reference
        datetime created_at
    }
    PREDICTIONS {
        uuid prediction_id PK
        uuid image_id FK
        uuid model_version_id FK
        string predicted_label
        float confidence
        jsonb class_scores
        string status
        datetime created_at
    }
    REFRESH_TOKENS {
        uuid token_id PK
        uuid user_id FK
        string token_hash UK
        uuid family_id
        datetime expires_at
        datetime created_at
        datetime revoked_at
        uuid replaced_by_token_id FK
    }
    IMAGE_QUALITY_ASSESSMENTS {
        uuid assessment_id PK
        uuid image_id FK
        float blur_score
        float brightness_mean
        float dark_pixel_percentage
        float bright_pixel_percentage
        string quality_status
        jsonb quality_flags
        string algorithm_version
        datetime assessed_at
    }

Database Table Descriptions

Table	Purpose
users	Stores user account details and password hashes
roles	Stores available application roles
user_roles	Maps users to their assigned roles
cases	Stores user-owned cases
images	Stores uploaded image metadata and storage references
model_versions	Tracks model names, architectures and checkpoint references
predictions	Stores classification results and class scores
refresh_tokens	Stores hashed refresh tokens and token lifecycle information
image_quality_assessments	Stores image-quality measurements and assessment results

Important Relationships

* One user can own multiple cases.
* One user can have multiple role assignments.
* One role can be assigned to multiple users.
* One case can contain multiple images.
* One image can have multiple prediction records.
* One model version can be associated with multiple predictions.
* One image can have multiple quality assessment records.
* One user can have multiple refresh tokens.
* A refresh token can reference its replacement token through replaced_by_token_id.

6. Database Migration Verification

The database migration chain was verified using Alembic.

Revision	Migration
244e263f1f95	Initial DermAI schema
cf242a5da3ba	Refresh tokens
e93c9c1565a8	Image quality assessments

Verified current database revision:

e93c9c1565a8 (head)

Alembic schema comparison result:

No new upgrade operations detected.

This indicates that Alembic detected no pending schema differences between the configured SQLAlchemy metadata and the database at the time of verification.

7. Model Evaluation Summary

The selected model is the fine-tuned MobileNetV3-Large checkpoint.

Its held-out test evaluation was performed on 460 samples.

Metric	Test result
Test samples	460
Accuracy	57.39%
Macro Precision	52.44%
Macro Recall	52.70%
Macro F1-score	51.02%
Weighted F1-score	60.12%

These results represent performance on the evaluated PAD-UFES-20 test partition. They do not establish clinical accuracy or generalization to other populations.

8. Research Limitations

* The system is a research prototype, not a clinically validated diagnostic system.
* Prediction confidence is not equivalent to diagnostic certainty.
* Grad-CAM visualizations indicate model activation patterns and do not represent precise lesion segmentation.
* Image quality assessment uses algorithmic heuristics and is not a clinically validated image-quality standard.
* Model performance should be interpreted using held-out test evaluation and per-class metrics.
* Minority-class performance remains a limitation.
* External dataset validation and clinical evaluation would be required before any real-world medical use.
* Additional security and deployment hardening are required before production deployment.

9. Conclusion

DermAI integrates a React frontend, FastAPI backend, PostgreSQL database, authenticated image-management workflows, image-quality assessment, MobileNetV3-Large inference and Grad-CAM explainability.

The architecture and database schema document the current research prototype implementation and its major component relationships.

Project status: Research prototype implemented; further model evaluation, external validation and production hardening remain necessary.

Medical disclaimer: DermAI is not a clinically validated diagnostic system. Its predictions must not be used to make medical decisions.
DermAI — Database Schema Design

1. Objective

This document describes the implemented relational database schema for DermAI, covering user accounts, role-based access, case management, image uploads, model version tracking, prediction history, refresh-token management and image-quality assessments.

The database design supports the project’s requirements for secure user access, image management, model inference records and research traceability.

Implementation status: The database schema is implemented using PostgreSQL and SQLAlchemy, with Alembic migrations.

2. Database Technology

Component	Implementation
Database	PostgreSQL
ORM	SQLAlchemy
Migration tool	Alembic
Primary key strategy	UUID
Timestamp handling	Timezone-aware timestamps
Flexible prediction data	JSONB
Authentication	JWT-based authentication
Password hashing	Argon2
Refresh-token storage	SHA-256 token hashes

The database connection and session management are implemented in backend/app/core/database.py.

SQLAlchemy models are defined in backend/app/models.py.

3. Entity Relationship Diagram

The following ER diagram represents the implemented database structure.

erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    USERS ||--o{ CASES : owns
    CASES ||--o{ IMAGES : contains
    IMAGES ||--o{ PREDICTIONS : analyzed_in
    MODEL_VERSIONS ||--o{ PREDICTIONS : used_for
    USERS ||--o{ REFRESH_TOKENS : owns
    IMAGES ||--o{ IMAGE_QUALITY_ASSESSMENTS : assessed_by
    REFRESH_TOKENS o|--o| REFRESH_TOKENS : replaces
    USERS {
        uuid user_id PK
        string email UK
        string password_hash
        string full_name
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    ROLES {
        uuid role_id PK
        string role_name UK
        string description
    }
    USER_ROLES {
        uuid user_id PK, FK
        uuid role_id PK, FK
        timestamptz assigned_at
    }
    CASES {
        uuid case_id PK
        uuid owner_id FK
        string status
        timestamptz created_at
        timestamptz updated_at
    }
    IMAGES {
        uuid image_id PK
        uuid case_id FK
        string original_filename
        string mime_type
        bigint file_size_bytes
        string storage_key UK
        integer width
        integer height
        timestamptz uploaded_at
    }
    MODEL_VERSIONS {
        uuid model_version_id PK
        string model_name
        string version
        string architecture
        string checkpoint_reference
        timestamptz created_at
    }
    PREDICTIONS {
        uuid prediction_id PK
        uuid image_id FK
        uuid model_version_id FK
        string predicted_label
        float confidence
        jsonb class_scores
        string status
        timestamptz created_at
    }
    REFRESH_TOKENS {
        uuid token_id PK
        uuid user_id FK
        string token_hash UK
        uuid family_id
        timestamptz expires_at
        timestamptz created_at
        timestamptz revoked_at
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
        timestamptz assessed_at
    }

4. Table and Field Definitions

4.1 USERS

Stores registered application user accounts.

Field	Data Type	Constraint	Description
user_id	UUID	Primary Key	Unique user identifier
email	VARCHAR	Unique	User login email
password_hash	TEXT	Not Null	Securely hashed password
full_name	VARCHAR	Not Null	User’s full name
is_active	BOOLEAN	Not Null	Account activation status
created_at	TIMESTAMPTZ	Not Null	Account creation timestamp
updated_at	TIMESTAMPTZ	Not Null	Last update timestamp

Passwords are stored as Argon2 hashes, never as plaintext.

4.2 ROLES

Stores the roles supported by the application.

Field	Data Type	Constraint	Description
role_id	UUID	Primary Key	Unique role identifier
role_name	VARCHAR	Unique	Role name
description	TEXT	Nullable	Role description

The roles table supports role-based access control.

4.3 USER_ROLES

Associates users with their assigned roles.

Field	Data Type	Constraint	Description
user_id	UUID	Composite Primary Key, Foreign Key	References USERS
role_id	UUID	Composite Primary Key, Foreign Key	References ROLES
assigned_at	TIMESTAMPTZ	Not Null	Role assignment timestamp

The combination of user_id and role_id forms a composite primary key.

This table implements a many-to-many relationship between users and roles.

4.4 CASES

Stores case-management information.

Field	Data Type	Constraint	Description
case_id	UUID	Primary Key	Unique case identifier
owner_id	UUID	Foreign Key	References USERS
status	VARCHAR	Not Null	Current case status
created_at	TIMESTAMPTZ	Not Null	Case creation timestamp
updated_at	TIMESTAMPTZ	Not Null	Last update timestamp

Each case belongs to a user. A user can own multiple cases.

Case ownership is used by the backend to enforce access restrictions.

4.5 IMAGES

Stores metadata and storage references for uploaded images.

Field	Data Type	Constraint	Description
image_id	UUID	Primary Key	Unique image identifier
case_id	UUID	Foreign Key	References CASES
original_filename	VARCHAR	Not Null	Original uploaded filename
mime_type	VARCHAR	Not Null	Verified media type
file_size_bytes	BIGINT	Not Null	Uploaded image size
storage_key	TEXT	Unique	Internal storage reference
width	INTEGER	Nullable	Image width
height	INTEGER	Nullable	Image height
uploaded_at	TIMESTAMPTZ	Not Null	Upload timestamp

Image files are stored separately from database records. The database stores image metadata and internal storage references.

The upload pipeline validates supported file types, file size and image decoding before accepting an image.

4.6 MODEL_VERSIONS

Maintains information about the AI models used for image analysis.

Field	Data Type	Constraint	Description
model_version_id	UUID	Primary Key	Unique model-version identifier
model_name	VARCHAR	Not Null	Model name
version	VARCHAR	Not Null	Model version
architecture	VARCHAR	Not Null	Model architecture
checkpoint_reference	TEXT	Nullable	Model checkpoint reference
created_at	TIMESTAMPTZ	Not Null	Registration timestamp

This table supports model-version traceability for prediction records.

The currently selected research model is MobileNetV3-Large Fine-Tuned, using the epoch 9 checkpoint.

4.7 PREDICTIONS

Stores actual model inference records.

Field	Data Type	Constraint	Description
prediction_id	UUID	Primary Key	Unique prediction identifier
image_id	UUID	Foreign Key	References IMAGES
model_version_id	UUID	Foreign Key	References MODEL_VERSIONS
predicted_label	VARCHAR	Not Null	Predicted class
confidence	DOUBLE PRECISION	Nullable	Model confidence score
class_scores	JSONB	Nullable	Per-class prediction scores
status	VARCHAR	Not Null	Prediction processing status
created_at	TIMESTAMPTZ	Not Null	Prediction timestamp

Only actual model inference outputs should be stored. Placeholder or fabricated predictions must not be recorded.

4.8 REFRESH_TOKENS

Stores hashed refresh-token records used by the authentication system.

Field	Data Type	Constraint	Description
token_id	UUID	Primary Key	Unique token identifier
user_id	UUID	Foreign Key	References USERS
token_hash	VARCHAR	Unique	SHA-256 hash of refresh token
family_id	UUID	Indexed	Token-family identifier
expires_at	TIMESTAMPTZ	Not Null	Token expiration timestamp
created_at	TIMESTAMPTZ	Not Null	Token creation timestamp
revoked_at	TIMESTAMPTZ	Nullable	Token revocation timestamp
replaced_by_token_id	UUID	Self-referencing Foreign Key	Replacement refresh token

The table supports refresh-token rotation and token-family tracking.

Raw refresh tokens are not stored in the database. Only their hashes are persisted.

The self-referencing relationship allows a rotated token to reference its replacement.

4.9 IMAGE_QUALITY_ASSESSMENTS

Stores image-quality measurements generated during image assessment.

Field	Data Type	Constraint	Description
assessment_id	UUID	Primary Key	Unique assessment identifier
image_id	UUID	Foreign Key	References IMAGES
blur_score	DOUBLE PRECISION	Nullable	Image sharpness-related score
brightness_mean	DOUBLE PRECISION	Nullable	Mean image brightness
dark_pixel_percentage	DOUBLE PRECISION	Nullable	Percentage of dark pixels
bright_pixel_percentage	DOUBLE PRECISION	Nullable	Percentage of bright pixels
quality_status	VARCHAR	Not Null	Quality assessment result
quality_flags	JSONB	Nullable	Quality-related flags
algorithm_version	VARCHAR	Not Null	Quality algorithm version
assessed_at	TIMESTAMPTZ	Not Null	Assessment timestamp

This table records image-quality assessment results separately from image metadata.

The quality assessment uses heuristic image measurements. These measurements are not clinically validated or equivalent to expert human assessment.

5. Relationships Between Tables

1. USERS → CASES: One-to-Many. A user can own multiple cases.
2. USERS → USER_ROLES: One-to-Many. A user can have multiple role assignments.
3. ROLES → USER_ROLES: One-to-Many. A role can be assigned to multiple users.
4. CASES → IMAGES: One-to-Many. A case can contain multiple images.
5. IMAGES → PREDICTIONS: One-to-Many. An image can have multiple prediction records.
6. MODEL_VERSIONS → PREDICTIONS: One-to-Many. A model version can be associated with multiple predictions.
7. USERS → REFRESH_TOKENS: One-to-Many. A user can have multiple refresh-token records.
8. IMAGES → IMAGE_QUALITY_ASSESSMENTS: One-to-Many. An image can have multiple quality assessments.
9. REFRESH_TOKENS → REFRESH_TOKENS: Self-referencing relationship used to track token replacement.

The USER_ROLES table implements the many-to-many relationship between USERS and ROLES.

6. Design Rationale

* UUID identifiers: Provide unique identifiers for application entities.
* Relational integrity: Primary and foreign keys maintain consistency between related records.
* Separate image storage: Large image files are stored outside relational database records.
* Prediction history: Prediction records are separated from case and image records.
* Model version tracking: Helps identify the model associated with a prediction.
* JSONB: Supports flexible storage of class scores and quality flags.
* Role-based access: Supports different levels of application access.
* Refresh-token rotation: Supports session renewal and token revocation.
* Quality assessment history: Keeps image-quality measurements associated with uploaded images.

7. Privacy and Security Considerations

* Passwords are stored using Argon2 hashing.
* Refresh tokens are stored as SHA-256 hashes.
* JWT-based authentication protects restricted API routes.
* Case ownership is checked before allowing access to case resources.
* Internal image storage paths are not intended to be exposed to unauthorized users.
* Database credentials and application secrets are managed through environment configuration.
* Uploaded images are validated before storage.
* Access to uploaded images is restricted through backend authorization.
* Only necessary user information should be collected.
* Public research datasets and de-identified images are used for model development.

Production deployment still requires a separate security review, including deployment-specific access controls and configuration.

8. Database Migration History

Database schema changes are managed using Alembic.

The implemented migration chain is:

Revision	Description
244e263f1f95	Create initial DermAI schema
cf242a5da3ba	Add refresh_tokens table
e93c9c1565a8	Add image_quality_assessments table

Current Alembic revision: e93c9c1565a8 (head)

The migration files are located in:

backend/migrations/versions/

The Alembic configuration is maintained in alembic.ini.

9. Implementation and Verification Status

Component	Status
PostgreSQL database selection	Implemented
SQLAlchemy ORM models	Implemented
Initial seven-table schema	Implemented
Refresh-token table	Implemented
Image-quality assessment table	Implemented
Primary and foreign keys	Implemented
Entity relationships	Implemented
Alembic migrations	Implemented
Database connection and session management	Implemented
Migration head verification	Verified
ORM metadata comparison	Verified

The following verification commands were successfully executed during project development:

alembic current
alembic history
alembic check

The alembic check command reported:

No new upgrade operations detected.

This indicates that Alembic detected no pending schema changes between the current SQLAlchemy metadata and the database at the time of verification.

10. Assumptions and Limitations

* PostgreSQL is the primary relational database.
* SQLAlchemy is used for ORM-based database operations.
* Alembic manages database schema migrations.
* Image files are stored separately from database metadata.
* A case can contain multiple images.
* An image can have multiple prediction and quality-assessment records.
* Prediction records are generated from actual model inference.
* Authentication and authorization are enforced by the backend.
* Image-quality measurements are heuristic and have not been clinically validated.
* DermAI is an academic research prototype, not a clinically validated diagnostic system.

11. Verification Checklist

* PostgreSQL database configured.
* SQLAlchemy models implemented.
* Nine database tables defined.
* Primary keys defined.
* Foreign-key relationships implemented.
* User-case ownership represented.
* Image metadata and storage references represented.
* Prediction history represented.
* Model-version tracking represented.
* Refresh-token management represented.
* Image-quality assessment records represented.
* Alembic migration chain implemented.
* Current migration head verified.
* No pending ORM metadata changes detected during verification.
* Passwords and refresh tokens are stored as hashes.
* No fabricated prediction values are recorded.

⸻

Document status: Updated to reflect the implemented DermAI database schema.
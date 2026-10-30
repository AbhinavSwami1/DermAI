# **DermAI — Database Schema Design**

## **1\. Objective**

This document defines the proposed relational database schema for DermAI case management, image uploads, user access and prediction history.
The design follows the DermAI Software Requirements Specification (SRS) and addresses assignment W2.2.

## **2\. Database Selection**

* **Database:** PostgreSQL
* **ORM planned for implementation:** SQLAlchemy
* **Primary keys:** UUID
* **Timestamp format:** TIMESTAMPTZ
* **Flexible prediction scores:** JSONB

This document describes the proposed database design. The database tables have not yet been implemented.

## **3\. Entity Relationship Diagram**

```
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    USERS ||--o{ CASES : owns
    CASES ||--o{ IMAGES : contains
    IMAGES ||--o{ PREDICTIONS : analyzed_in
    MODEL_VERSIONS ||--o{ PREDICTIONS : used_for

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
```

## **4\. Table and Field Definitions**

### **4.1 USERS**

Stores registered application user accounts.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| user\_id | UUID | Primary Key | Unique user identifier |
| email | VARCHAR(255) | Unique, Not Null | User login email |
| password\_hash | TEXT | Not Null | Securely hashed password |
| full\_name | VARCHAR(150) | Not Null | User’s full name |
| is\_active | BOOLEAN | Not Null | Account activation status |
| created\_at | TIMESTAMPTZ | Not Null | Account creation timestamp |
| updated\_at | TIMESTAMPTZ | Not Null | Last update timestamp |

Passwords must never be stored in plaintext.

### **4.2 ROLES**

Stores the different roles supported by the DermAI system.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| role\_id | UUID | Primary Key | Unique role identifier |
| role\_name | VARCHAR(60) | Unique, Not Null | Role name |
| description | TEXT | Nullable | Description of the role |

Proposed roles:

* Patient / General User
* Dermatologist / Clinician
* Medical Researcher
* Data Scientist / ML Engineer
* Administrator

### **4.3 USER\_ROLES**

Associates users with their assigned roles.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| user\_id | UUID | Primary Key, Foreign Key | References USERS |
| role\_id | UUID | Primary Key, Foreign Key | References ROLES |
| assigned\_at | TIMESTAMPTZ | Not Null | Role assignment timestamp |

The combination of user\_id and role\_id forms a composite primary key.
This table supports a many-to-many relationship between users and roles.

### **4.4 CASES**

Stores case-management information.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| case\_id | UUID | Primary Key | Unique case identifier |
| owner\_id | UUID | Foreign Key, Not Null | References USERS |
| status | VARCHAR(40) | Not Null | Current case status |
| created\_at | TIMESTAMPTZ | Not Null | Case creation timestamp |
| updated\_at | TIMESTAMPTZ | Not Null | Last update timestamp |

Proposed case statuses:

* created
* uploaded
* processing
* completed
* failed

Each case belongs to one user, while one user can own multiple cases.

### **4.5 IMAGES**

Stores metadata and storage references for uploaded images.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| image\_id | UUID | Primary Key | Unique image identifier |
| case\_id | UUID | Foreign Key, Not Null | References CASES |
| original\_filename | VARCHAR(255) | Not Null | Original uploaded filename |
| mime\_type | VARCHAR(100) | Not Null | Verified media type |
| file\_size\_bytes | BIGINT | Not Null | Image file size |
| storage\_key | TEXT | Unique, Not Null | Internal storage reference |
| width | INTEGER | Nullable | Image width |
| height | INTEGER | Nullable | Image height |
| uploaded\_at | TIMESTAMPTZ | Not Null | Upload timestamp |

Image files are stored separately in filesystem or object storage. The database stores their metadata and storage references.
A single case can contain multiple images.

### **4.6 MODEL\_VERSIONS**

Maintains information about the AI models used for image analysis.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| model\_version\_id | UUID | Primary Key | Unique model identifier |
| model\_name | VARCHAR(100) | Not Null | Model name |
| version | VARCHAR(60) | Not Null | Model version |
| architecture | VARCHAR(100) | Not Null | Model architecture |
| checkpoint\_reference | TEXT | Nullable | Model checkpoint reference |
| created\_at | TIMESTAMPTZ | Not Null | Registration timestamp |

This table helps track which model version generated a prediction.

### **4.7 PREDICTIONS**

Stores prediction history after actual model inference.

| **Field** | **Data Type** | **Constraint** | **Description** |
| ----- | --------- | ---------- | ----------- |
| prediction\_id | UUID | Primary Key | Unique prediction identifier |
| image\_id | UUID | Foreign Key, Not Null | References IMAGES |
| model\_version\_id | UUID | Foreign Key, Not Null | References MODEL\_VERSIONS |
| predicted\_label | VARCHAR(100) | Not Null | Actual predicted class |
| confidence | DOUBLE PRECISION | Nullable | Model confidence score |
| class\_scores | JSONB | Nullable | Per-class prediction scores |
| status | VARCHAR(40) | Not Null | Prediction processing status |
| created\_at | TIMESTAMPTZ | Not Null | Prediction timestamp |

Only actual model inference outputs should be stored. No fabricated or placeholder predictions should be recorded.

## **5\. Relationships Between Tables**

1. **USERS → CASES:** One-to-Many. A user can create multiple cases.
2. **USERS → USER\_ROLES:** One-to-Many. A user can have multiple role assignments.
3. **ROLES → USER\_ROLES:** One-to-Many. A role can be assigned to multiple users.
4. **CASES → IMAGES:** One-to-Many. A case can contain multiple images.
5. **IMAGES → PREDICTIONS:** One-to-Many. An image can have multiple prediction records.
6. **MODEL\_VERSIONS → PREDICTIONS:** One-to-Many. A model version can generate multiple predictions.

The USER\_ROLES table implements the many-to-many relationship between USERS and ROLES.

## **6\. Design Rationale**

* **UUID identifiers:** Provide unique identifiers for users, cases, images and predictions.
* **Relational integrity:** Primary and foreign keys maintain consistency between related records.
* **Separate image storage:** Large image files are stored outside the relational database.
* **Prediction history:** Prediction records are separated from case records to maintain analysis history.
* **Model version tracking:** Helps identify the model used for each prediction.
* **JSONB:** Supports flexible storage of per-class prediction scores.
* **Role-based access:** Supports different levels of access for users, clinicians, researchers and administrators.

## **7\. Privacy and Security Considerations**

* Passwords must be stored using secure password hashing.
* Case ownership must be checked before allowing access to case records.
* Internal image storage paths must not be exposed to unauthorized users.
* Only necessary user information should be collected.
* Public research datasets or de-identified images should be used during development.
* Database credentials must be stored in environment variables.
* Access to uploaded images must be restricted.
* Sensitive patient information must be protected from unauthorized access.

## **8\. Assumptions and Limitations**

* PostgreSQL is the proposed primary database.
* SQLAlchemy is the planned ORM.
* Image files are stored separately from database records.
* A case may contain multiple images.
* Prediction records are created only after actual model inference.
* Backend authentication and authorization will enforce user access restrictions.
* This document describes the proposed schema and does not represent an implemented database.

## **9\. Implementation Status**

| **Component** | **Status** |
| --------- | ------ |
| Database selection | Designed |
| Entity identification | Designed |
| ER diagram | Designed |
| Table and field definitions | Designed |
| Primary and foreign keys | Designed |
| Relationships | Designed |
| Design rationale | Documented |
| Privacy and security considerations | Documented |
| SQLAlchemy implementation | Pending |
| PostgreSQL connection | Pending |
| Database migrations | Pending |

## **10\. Verification Checklist**

* Every table has a defined primary key.
* Foreign keys reference the appropriate entities.
* Case ownership is represented through owner\_id.
* Image records reference their corresponding cases.
* Prediction records reference an image and model version.
* Timestamps and case statuses are represented.
* Passwords are stored as hashes rather than plaintext.
* Image files are separated from database metadata.
* No fabricated prediction values are stored.

***

<br>

# DermAI API Contract

Base URL (local): `http://127.0.0.1:8001`. Interactive documentation: `/docs` (OpenAPI at `/openapi.json`). All routes below are under `/api/v1` except `/health`.

## Conventions
- JSON requests use `Content-Type: application/json`; image upload uses `multipart/form-data`.
- Protected routes need `Authorization: Bearer <access_token>`. The access token comes from `POST /api/v1/auth/login`; a refresh token is stored in an HTTP-only cookie and used by `POST /api/v1/auth/refresh`.
- Errors return `{"detail": ...}`. `detail` is a string, or an object for quality-check conflicts: `{"code", "message", "quality_status", "quality_flags", ...}`.
- Identifiers are UUIDs. Timestamps are ISO 8601 (UTC).
- Ownership is enforced on the server: a case, image, prediction or report that belongs to another user returns 404, not 403.

## Common error codes
| Code | Meaning |
|---|---|
| 400 | Invalid upload (unsupported format, undecodable, too small) |
| 401 | Missing, invalid or expired token |
| 403 | Authenticated but role not permitted |
| 404 | Resource does not exist or is not owned by the caller |
| 409 | Prediction blocked by image quality (`IMAGE_QUALITY_WARNING` or review required) |
| 413 | File larger than 10 MB |
| 422 | Validation error (bad UUID, bad date range, bad parameter) |
| 429 | Rate limit exceeded |
| 500 / 503 | Storage, database or inference failure; no result is fabricated |

## Typical flow (curl)
```
curl -X POST $B/api/v1/users/register -H 'Content-Type: application/json' -d '{"full_name":"A User","email":"a@example.com","password":"Strong#Pass1"}'
curl -X POST $B/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"a@example.com","password":"Strong#Pass1"}'     # -> access_token
curl -X POST $B/api/v1/cases -H "Authorization: Bearer $T"                                                                         # -> case_id
curl -X POST $B/api/v1/upload -H "Authorization: Bearer $T" -F case_id=$CASE -F file=@lesion.png                                    # -> image_id
curl $B/api/v1/images/$IMG/quality -H "Authorization: Bearer $T"                                                                     # quality status
curl -X POST "$B/api/v1/predictions/$IMG" -H "Authorization: Bearer $T"                                                              # add ?acknowledge_quality_warning=true after a WARNING
curl -X POST "$B/api/v1/predictions/$IMG/gradcam" -H "Authorization: Bearer $T" -o gradcam.png
curl "$B/api/v1/images/$IMG/processed" -H "Authorization: Bearer $T" -o model_input.png
curl "$B/api/v1/predictions/history?page=1&page_size=10&date_from=2026-11-01" -H "Authorization: Bearer $T"
curl "$B/api/v1/reports/$PRED?format=pdf" -H "Authorization: Bearer $T" -o report.pdf
```

## Example prediction response (real application output, 2026-11-19; identifiers omitted)
```
{
  "prediction_id": "<uuid>", "image_id": "<uuid>", "model_version_id": "<uuid>",
  "model_name": "DermAI MobileNetV3-Large Fine-tuned",
  "model_version": "mobilenet_v3_large_finetuned_epoch9",
  "architecture": "MobileNetV3-Large",
  "predicted_label": "ACK", "confidence": 0.9804,
  "class_scores": {"ACK": 0.9804, "BCC": 0.0085, "MEL": 0.0003, "NEV": 0.0001, "SCC": 0.0057, "SEK": 0.0050},
  "top_predictions": [
    {"rank": 1, "class_name": "ACK", "score": 0.9804},
    {"rank": 2, "class_name": "BCC", "score": 0.0085},
    {"rank": 3, "class_name": "SCC", "score": 0.0057}
  ],
  "status": "completed", "created_at": "2026-11-19T10:40:45Z",
  "disclaimer": "Research prototype output only..."
}
```
Scores are softmax outputs, not clinically validated probabilities.

## Example quality-warning conflict (409)
```
{"detail": {"code": "IMAGE_QUALITY_WARNING", "message": "This image has a quality warning ...",
            "quality_status": "WARNING", "quality_flags": ["POSSIBLY_BLURRY"], "algorithm_version": "1.1.0"}}
```

## Endpoints (generated from the code)

### GET /api/v1/admin/users

List registered users with their roles (administrator only).

- Tag: Administration
- Authentication: Bearer token, roles: 
- Success: 200

### DELETE /api/v1/admin/users/{user_id}/roles/{role_name}

Remove one role from a user (administrator only).

- Tag: Administration
- Authentication: Bearer token, roles: 
- Parameter `user_id` (path, UUID, required)
- Parameter `role_name` (path, RoleName, required)
- Success: 200
- Errors raised in this handler: 400 Administrators cannot remove their own Administrator role.; 404 Role assignment not found.; 500 Unable to remove the role.

### POST /api/v1/auth/login

- Tag: Authentication
- Authentication: none
- Rate limit: '5/minute'
- Request body (JSON): `LoginRequest`
- Success: 200, response `TokenResponse`
- Errors raised in this handler: 401 Invalid email or password.; 403 Account is inactive.

### POST /api/v1/auth/refresh

- Tag: Authentication
- Authentication: none
- Success: 200, response `TokenResponse`
- Errors raised in this handler: 401 Invalid, expired, or revoked refresh token.; 401 Refresh token is missing.; 401 User account is unavailable.

### POST /api/v1/auth/logout

- Tag: Authentication
- Authentication: none
- Success: 200

### POST /api/v1/cases

- Tag: Cases
- Authentication: Bearer token
- Success: 201, response `CaseResponse`

### GET /api/v1/users/{owner_id}/cases

- Tag: Cases
- Authentication: Bearer token
- Parameter `owner_id` (path, UUID, required)
- Success: 200, response `list[CaseResponse]`
- Errors raised in this handler: 403 You cannot access another user's cases.

### GET /api/v1/cases/{case_id}

- Tag: Cases
- Authentication: Bearer token
- Parameter `case_id` (path, UUID, required)
- Success: 200, response `CaseResponse`
- Errors raised in this handler: 404 Case not found.

### PATCH /api/v1/cases/{case_id}/notes

- Tag: Cases
- Authentication: Bearer token
- Parameter `case_id` (path, UUID, required)
- Request body (JSON): `CaseNotesUpdate`
- Success: 200, response `CaseResponse`
- Errors raised in this handler: 404 Case not found.; 500 Unable to save case notes.

### GET /api/v1/dashboard/clinician

- Tag: Dashboards
- Authentication: Bearer token, roles: 
- Success: 200

### GET /api/v1/dashboard/admin

- Tag: Dashboards
- Authentication: Bearer token, roles: 
- Success: 200

### GET /api/v1/dashboard/research

De-identified aggregates only: no user, case or image identifiers are returned.

- Tag: Dashboards
- Authentication: Bearer token, roles: 
- Success: 200

### GET /api/v1/images/{image_id}/quality

- Tag: Images
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Success: 200, response `dict`
- Errors raised in this handler: 404 Image or quality assessment not found.

### GET /api/v1/images/{image_id}/file

Return the original stored image (owner only).

- Tag: Images
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Success: 200

### GET /api/v1/images/{image_id}/processed

Return the model input (resized, before normalisation) for an owned image.

- Tag: Images
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Success: 200
- Errors raised in this handler: 422 Unable to preprocess the stored image.

### GET /api/v1/images/{image_id}/processed/info

Describe the preprocessing steps applied to an owned image.

- Tag: Images
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Success: 200
- Errors raised in this handler: 422 Unable to preprocess the stored image.

### GET /api/v1/insights/model-info

Deployed model version and class list (any signed-in user).

- Tag: Insights
- Authentication: Bearer token
- Success: 200

### GET /api/v1/insights/model-metrics

Saved evaluation metrics (research and staff roles only).

- Tag: Insights
- Authentication: Bearer token, roles: 
- Success: 200

### GET /api/v1/notifications

- Tag: Notifications
- Authentication: Bearer token
- Success: 200

### GET /api/v1/predictions/history

Return paginated prediction history belonging to the

- Tag: Predictions
- Authentication: Bearer token
- Parameter `page` (query, int, default 1)
- Parameter `page_size` (query, int, default 10)
- Parameter `date_from` (query, date | None, default None)
- Parameter `date_to` (query, date | None, default None)
- Success: 200, response `PredictionHistoryResponse`
- Errors raised in this handler: 422 date_from must not be after date_to.

### POST /api/v1/predictions/{image_id}

- Tag: Predictions
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Parameter `acknowledge_quality_warning` (query, bool, default False)
- Success: 201, response `PredictionResponse`
- Errors raised in this handler: 500 Unable to save prediction.; 503 Model inference is currently unavailable.

### POST /api/v1/predictions/{image_id}/gradcam

- Tag: Predictions
- Authentication: Bearer token
- Parameter `image_id` (path, UUID, required)
- Parameter `acknowledge_quality_warning` (query, bool, default False)
- Success: 200
- Errors raised in this handler: 503 Grad-CAM visualization is currently unavailable.

### GET /api/v1/reports/{prediction_id}

Export a saved analysis (owner only). Built from stored DB values.

- Tag: Reports
- Authentication: Bearer token
- Parameter `prediction_id` (path, UUID, required)
- Parameter `format` (query, Literal['pdf', 'json', 'csv'], default 'pdf')
- Success: 200

### GET /api/v1/roles/me

- Tag: Role Management
- Authentication: Bearer token
- Success: 200, response `UserRoleResponse`

### POST /api/v1/roles/users/{user_id}

- Tag: Role Management
- Authentication: Bearer token, roles: 
- Parameter `user_id` (path, UUID, required)
- Request body (JSON): `RoleAssignmentRequest`
- Success: 200, response `UserRoleResponse`
- Errors raised in this handler: 404 User not found.; 409 Unable to assign the requested role.

### POST /api/v1/upload

- Tag: Image Upload
- Authentication: Bearer token
- Parameter `case_id` (form, UUID, required)
- Parameter `file` (file, UploadFile, required)
- Success: 201, response `ImageResponse`
- Errors raised in this handler: 400 dynamic message; 404 Case not found.; 500 Unable to store image or save image metadata.

### POST /api/v1/users/register

- Tag: Users
- Authentication: none
- Request body (JSON): `UserCreate`
- Success: 201, response `UserResponse`
- Errors raised in this handler: 409 Email is already registered.; 409 Unable to register user. Email or role may already exist.

### GET /api/v1/users/me

- Tag: Users
- Authentication: Bearer token
- Success: 200, response `UserResponse`

## Schemas (from `backend/app/schemas.py`)

**UserCreate**

- `email: EmailStr`
- `password: str = Field(min_length=8, max_length=128)`
- `full_name: str = Field(min_length=2, max_length=150)`

**UserResponse**

- `user_id: UUID`
- `email: EmailStr`
- `full_name: str`
- `is_active: bool`
- `created_at: datetime`

**CaseCreate**

- `owner_id: UUID`

**CaseResponse**

- `case_id: UUID`
- `owner_id: UUID`
- `status: str`
- `created_at: datetime`
- `updated_at: datetime`
- `clinical_notes: str | None = None`
- `follow_up_date: date | None = None`

**CaseNotesUpdate**

- `clinical_notes: str | None = Field(default=None, max_length=2000)`
- `follow_up_date: date | None = None`

**ImageResponse**

- `image_id: UUID`
- `case_id: UUID`
- `original_filename: str`
- `mime_type: str`
- `file_size_bytes: int`
- `storage_key: str`
- `width: int | None`
- `height: int | None`
- `uploaded_at: datetime`

**LoginRequest**

- `email: EmailStr`
- `password: str = Field(min_length=8, max_length=128)`

**TokenResponse**

- `access_token: str`
- `token_type: str = 'bearer'`

**RoleAssignmentRequest**

- `role_name: Literal['Patient', 'Dermatologist', 'Medical Researcher', 'Data Scientist', 'Administrator']`

**RoleResponse**

- `role_id: UUID`
- `role_name: str`
- `description: str | None`

**UserRoleResponse**

- `user_id: UUID`
- `roles: list[str]`

**PredictionResponse**

- `prediction_id: UUID`
- `image_id: UUID`
- `model_version_id: UUID`
- `model_name: str`
- `model_version: str`
- `architecture: str`
- `predicted_label: str`
- `confidence: float`
- `class_scores: dict[str, float]`
- `status: str`
- `created_at: datetime`
- `disclaimer: str`
- `top_predictions: list[dict] | None = None`

**PredictionHistoryItem**

- `prediction_id: UUID`
- `case_id: UUID`
- `image_id: UUID`
- `original_filename: str`
- `predicted_label: str`
- `confidence: float | None`
- `class_scores: dict[str, float] | None`
- `status: str`
- `model_version_id: UUID`
- `model_name: str`
- `model_version: str`
- `architecture: str`
- `created_at: datetime`
- `top_predictions: list[dict] | None = None`

**PredictionHistoryResponse**

- `items: list[PredictionHistoryItem]`
- `total: int`
- `page: int`
- `page_size: int`
- `total_pages: int`
- `disclaimer: str`


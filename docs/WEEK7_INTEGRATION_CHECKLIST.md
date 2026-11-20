# Week 7 - Integration Notes and Checklist

## New backend endpoints (all require a Bearer token)
| Method | Route | Purpose | Errors |
|---|---|---|---|
| GET | `/api/v1/reports/{prediction_id}?format=pdf\|json\|csv` | Export a saved analysis (owner only) | 401, 404, 422 |
| GET | `/api/v1/images/{image_id}/file` | Original stored image (owner only) | 401, 404 |
| GET | `/api/v1/insights/model-metrics` | Saved evaluation metrics from `ml/outputs` | 401 |
| GET | `/api/v1/dashboard/clinician` | Aggregate counts (Dermatologist, Administrator) | 401, 403 |
| GET | `/api/v1/dashboard/admin` | Users/usage counts (Administrator) | 401, 403 |

Prediction responses and history items now include `top_predictions` (rank, class_name, score) computed from the stored model scores. The analysis timestamp is the stored `created_at`.

## Frontend
Landing page, Register, Login, application (Root.tsx separates landing from authenticated app); report export buttons on result and history; Compare Analyses; Staff Dashboards; Research Insights loaded from the backend.

## Workflow verification (run and tick locally)
- [ ] Landing -> Register -> Login -> app
- [ ] Upload image -> quality check shown -> prediction + Top-3 -> Grad-CAM
- [ ] Analysis appears in History; reopening shows saved record
- [ ] PDF/CSV/JSON export opens and matches the record
- [ ] Compare two analyses
- [ ] Staff dashboards: 403 message for Patient role; data for Administrator

## Added in round 2
| Method | Route | Purpose |
|---|---|---|
| PATCH | `/api/v1/cases/{case_id}/notes` | Save clinical notes (max 2000 chars) and follow-up date; owner only (404 otherwise) |
| GET | `/api/v1/predictions/history?date_from=&date_to=` | UTC date filter, inclusive; 422 if from > to |
| GET | `/api/v1/notifications` | Alerts derived from the user's own records (low model score, image-quality review, follow-up due/upcoming); nothing is stored |

Alembic migration `a7c4d9e2b6f1` adds `cases.clinical_notes` and `cases.follow_up_date`: run `alembic upgrade head`.

## Known incomplete / blockers
- Notifications have no read/unread state and no email/SMS delivery.
- Advanced CNN/Transformer/ensemble and LR runs: scripts ready, not run (`docs/EXPERIMENT_RUNBOOK.md`).
- Image-quality threshold validation and Grad-CAM observations: scripts ready, results not recorded (`docs/IMAGE_QUALITY_VALIDATION.md`, `ml/scripts/gradcam_observations.py`).
- Dashboard home page still shows static dataset constants (`researchStats`, `conditions` in `App.tsx`) taken from the dataset audit; they should be moved to the backend.
- Staff dashboards need a user with the Administrator/Dermatologist role (assign via roles API).
- Calibration, advanced models, and LR experiments require local training data (see their docs).
- DB-backed tests for notes, date filter and notifications are in `backend/tests/test_case_notes.py` (written; run `pytest` locally). Report/dashboard/insights endpoints have no DB-backed tests.
- Screenshots and demo recording must be captured manually.

## Image quality behaviour (version 1.1.0)
Possible blur gives a `WARNING` that the user must acknowledge (`acknowledge_quality_warning=true`); brightness and pixel-fraction flags still block prediction (`REVIEW_REQUIRED`). See `docs/IMAGE_QUALITY_VALIDATION.md`.

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

## Known incomplete / blockers
- Clinical notes on cases, date filtering in history, and follow-up reminders are not implemented.
- Dashboard home page still shows static dataset constants (`researchStats`, `conditions` in `App.tsx`) taken from the dataset audit; they should be moved to the backend.
- Staff dashboards need a user with the Administrator/Dermatologist role (assign via roles API).
- Calibration, advanced models, and LR experiments require local training data (see their docs).
- Backend DB-backed tests for the new endpoints are not written; pure report tests are in `backend/tests/test_reports.py`.
- Screenshots and demo recording must be captured manually.

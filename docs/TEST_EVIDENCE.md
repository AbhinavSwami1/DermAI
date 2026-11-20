# DermAI - Test Evidence

Automated: `PYTHONPATH="$PWD:$PWD/backend" pytest -q backend/tests/` gave **81 passed** (2026-11-20, local PostgreSQL). Manual results are from the running application with real PAD-UFES-20 test images (2026-11-19/20). Responsible: A. Swami.

## A. Functional testing
| Test case | Evidence | Result |
|---|---|---|
| Registration and login | `test_user_registration_success`, refresh-token and login tests; manual register and login | Pass |
| Image upload | `test_valid_png_upload`, `test_valid_jpeg_upload`; manual upload | Pass |
| Image validation | `test_unsupported_gif_rejected`, `test_small_image_rejected`, `test_oversized_file_rejected` | Pass |
| Image preprocessing | `test_preprocessing_output_shape_and_type` | Pass |
| Model inference | `test_successful_prediction_and_database_persistence` (stubbed model); manual run with the real checkpoint (e.g. ACK 98.0%, BCC 79.0%) | Pass |
| Prediction result display | manual: class, score, Top-3, timestamp, Grad-CAM | Pass |
| Saving analysis records | `test_successful_prediction_and_database_persistence`; manual history | Pass |
| Retrieving history | `test_prediction_history_*` (4 tests) | Pass |
| Opening previous analyses | manual (history, compare screen) | Pass |
| Report generation and export | `test_exports_match_record`; manual PDF, CSV, JSON download | Pass |
| Case notes, date filter, notifications | `test_case_notes.py` (4 tests); UI not yet recorded | Pass (API) / UI pending |
| Blur warning acknowledgement | two tests in `test_predictions.py`; UI not yet recorded | Pass (API) / UI pending |

## B. Negative testing
| Test case | Evidence | Result |
|---|---|---|
| Unsupported image format | `test_unsupported_gif_rejected` | Pass |
| Corrupted image | upload, quality and prediction `test_corrupted_image_rejected` | Pass |
| Empty upload | quality and prediction `test_empty_image_rejected` | Pass |
| Oversized image | `test_oversized_file_rejected` | Pass |
| Missing or unavailable checkpoint | only inference failure is tested (`test_prediction_inference_failure_returns_503`); a missing-file case is not | Partial |
| Database connection failure | not tested | Not tested |
| Unauthorized record access | other-user case, image, history, prediction and Grad-CAM tests; missing token tests | Pass |
| Invalid API parameters | `test_prediction_history_rejects_invalid_pagination`; date-range 422 test | Pass |
| Path traversal in storage reference | `test_prediction_blocks_path_traversal`, Grad-CAM equivalent | Pass |
| Poor-quality image blocks prediction | `test_prediction_blocks_review_required_image` | Pass |

## C. Integration testing
| Test case | Evidence | Result |
|---|---|---|
| Frontend to backend | manual end-to-end workflow in the browser | Pass |
| Backend to model | manual real-checkpoint inference and Grad-CAM | Pass |
| Backend to database | pytest against PostgreSQL | Pass |
| Report from saved records | manual export from history records | Pass |
| Operation inside Docker | configuration written, not run (`docs/DOCKER_DEPLOYMENT.md`) | Not run |

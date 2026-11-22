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

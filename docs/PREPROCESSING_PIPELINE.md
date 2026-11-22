# DermAI - Preprocessing Pipeline

Describes what the implemented code does, in order. Sources: `backend/app/services/image_validation.py`, `image_quality_service.py`, `inference_service.py`, `processed_image.py`, `ml/src/data/augmentations.py`.

| Step | What happens | Parameters (from code) |
|---|---|---|
| 1. Receive and preserve | Upload is stored unchanged under a generated storage key; filename, MIME type, size and time are saved with the image record, linked to the case | original is never modified |
| 2. Validate and decode | Format is checked on the decoded content (not the extension), then size and dimensions | allowed formats `{"JPEG", "PNG"}`; max file size `10 * 1024 * 1024`; min width `224`, min height `224`; corrupt, empty and unsupported files return 400 |
| 3. Orientation | EXIF orientation is applied once (`ImageOps.exif_transpose`) | no EXIF: unchanged |
| 4. Quality assessment | Blur (Laplacian variance), mean brightness, dark and bright pixel fractions; status ACCEPTABLE, WARNING (blur only) or REVIEW_REQUIRED (exposure flags) | version `"1.1.0"`; min blur `40.0`; brightness `40.0` to `220.0`; dark/bright pixel limit `50.0` / `50.0` percent |
| 5. Colour | Converted to 3-channel RGB (`convert("RGB")`): grayscale is expanded; alpha is dropped without compositing | channel order RGB |
| 6. Resize | Direct resize to 224 x 224, LANCZOS interpolation | aspect ratio is not preserved (image is stretched) |
| 7. Normalise | `ToTensor` scales to 0-1, then ImageNet mean `[0.485, 0.456, 0.406]` and std `[0.229, 0.224, 0.225]`; applied once, at inference | checkpoint metadata is checked against these values on load |
| 8. Processed output | Not persisted. The exact step 3, 5 and 6 result is regenerated on demand from the stored original (`GET /api/v1/images/{image_id}/processed`, version 1.0.0) and shown in the result screen | deterministic: same input gives the same PNG |

Training uses the same resize and normalisation (`ml/src/data/augmentations.py`). Augmentation (random flips, rotation up to 15 degrees) is applied to the training split only; validation, test and inference use no augmentation.

## Verification
- `backend/tests/test_processed_image.py`: output is 224 x 224 RGB PNG, deterministic, grayscale and RGBA become RGB, EXIF orientation applied once, invalid bytes raise an error, and the size constant equals the inference service constant.
- Upload and quality tests cover valid JPEG/PNG, unsupported format, corrupted, empty, small and oversized files.

## Limitations
- Stretching to 224 x 224 can distort lesion shape for non-square photos; a crop or padding strategy was not evaluated.
- Contrast is not measured; lesion visibility and background interference (hair, markings) are not assessed.
- Alpha channels are dropped rather than composited onto a documented background.
- Quality thresholds are heuristics validated only on synthetic degradation (`docs/IMAGE_QUALITY_VALIDATION.md`).

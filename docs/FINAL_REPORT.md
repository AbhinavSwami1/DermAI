# DermAI - Consolidated Report (Milestones 1 to 4, initial)

DermAI is an academic research prototype for skin-image analysis on PAD-UFES-20 (2,298 images, 6 classes: ACK, BCC, MEL, NEV, SCC, SEK). Predictions are informational, are not a medical diagnosis, and have not been clinically validated.

## 1. Features implemented and demonstrated
| Area | Status |
|---|---|
| Landing page, register, login, token refresh, roles | Implemented, demonstrated |
| Case creation, image upload, ownership checks | Implemented, demonstrated, 81 tests pass |
| Image quality assessment (blur, brightness, exposure) | Implemented, demonstrated; threshold validated on synthetic degradation (section 4) |
| Preprocessing (224x224, ImageNet normalisation) | Implemented |
| Classification (MobileNetV3-Large fine-tuned) with Top-3 and timestamp | Implemented, demonstrated |
| Grad-CAM (original, heatmap, overlay) | Implemented, demonstrated |
| Prediction history, individual records, comparison screen | Implemented, demonstrated |
| PDF, CSV, JSON report export | Implemented, demonstrated |
| Case notes, follow-up date, history date filter, notifications | Implemented, API tested; UI demonstration pending |
| Clinician and administrator dashboards | Implemented (role-protected, real counts); demonstrated only as the 403 case for a Patient user |
| Docker configuration | Written, not built or run |
| Severity / risk classification | Not implemented: dataset has no severity labels (section 6) |
| Lesion detection / segmentation | Not implemented: dataset has image-level labels only (`docs/GRADCAM_LOCALIZATION_REPORT.md`) |

## 2. Model experiments
Same patient-level split (1,477 / 361 / 460), seed 42, weighted cross-entropy.
| Model | Val acc | Val macro F1 | Test acc | Test macro F1 |
|---|---|---|---|---|
| MobileNetV3-Large fine-tuned (deployed) | 61.22% | 56.53% | 57.39% | 51.02% |
| ConvNeXt-Tiny (lr 1e-4, best epoch 3) | 66.20% | 61.88% | 60.43% | 60.84% |
MobileNetV3-Large versus EfficientNet-B0: see `docs/PHASE5_MODEL_COMPARISON_REPORT.md`. ConvNeXt-Tiny details and caveats: `docs/ADVANCED_MODELS_STATUS.md`. Accuracy differences are about one standard error on 460 images and are inconclusive; the macro F1 gain depends heavily on MEL (10 test images). SCC remains poor (ConvNeXt precision 0.17). ConvNeXt-Tiny is not deployed. Transformer, ensemble and learning-rate runs were not executed (scripts and plan: `docs/EXPERIMENT_RUNBOOK.md`).

## 3. Confidence and calibration (MobileNetV3-Large, test split)
ECE 0.0739 to 0.0429 after temperature scaling (T = 1.135, fitted on validation only); NLL 1.057 to 1.043. Score at or above 0.8: 98 predictions, 14 incorrect (accuracy 85.7%); score below 0.5: accuracy 34.5%; 67 ambiguous predictions (top-1 minus top-2 below 0.10). The model is overconfident (mean score 64.5% versus accuracy 57.4%). Details: `docs/CALIBRATION_REPORT.md`.

## 4. Image-quality validation
On 60 test images the original blur threshold (100) flagged 26.7% of untouched images; a threshold of 40 flagged 6.7% with equal detection of synthetic blur. A visual review found no clean separation (clear low-texture images scored low). Blur is therefore a warning that the user must acknowledge; exposure problems still block prediction (version 1.1.0). The manual-reference comparison was not completed. See `docs/IMAGE_QUALITY_VALIDATION.md`.

## 5. Explainability (six test images, exploratory)
Heatmaps differ per image and stay aligned. They centre on the lesion for the BCC and SEK examples; for the incorrect MEL and NEV cases the heat lies mostly away from the lesion; in the SCC example it overlaps a pen mark. No map was blank or saturated. This does not prove correctness; a marking-removal experiment would be needed to test a pen-mark shortcut. See `docs/GRADCAM_OBSERVATIONS.md`.

## 6. Risk and severity
Not feasible with PAD-UFES-20: labels are disease names only, with no severity, stage, outcome or urgency. No risk score is shown. See `docs/RISK_SEVERITY_FEASIBILITY_REPORT.md`.

## 7. Testing
81 automated tests pass; manual workflow checks and the full matrix are in `docs/TEST_EVIDENCE.md`.

## 8. Known limitations
- Small dataset and test set; rare classes (MEL, SCC) have very few samples; no external validation.
- Scores are softmax outputs, not clinical probabilities; confidently incorrect predictions occur.
- Grad-CAM is low-resolution (7x7 upsampled) and is not segmentation.
- Quality metrics are proxies; lesion visibility and background interference are not assessed.
- The warning acknowledgement is enforced but not stored.
- Dashboard dataset distribution is a static reference from the audit report.
- Notifications have no read state or external delivery.

## 9. Unfinished work and blockers
- Docker build and containerised workflow not executed (`docs/DOCKER_DEPLOYMENT.md`).
- ViT/Swin, ensemble and learning-rate experiments not run (training time and hardware).
- Manual reference labelling for quality validation not done.
- Responsive layout (tablet/mobile) not systematically checked.
- Screenshots and a demonstration recording must be captured from the running application and attached separately.
- Not deployed to a public host; no HTTPS configured.

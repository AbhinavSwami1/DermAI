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
| Preprocessed model-input view (regenerated on demand, not stored) | Implemented |
| Prediction history, individual records, comparison screen | Implemented, demonstrated |
| PDF, CSV, JSON report export | Implemented, demonstrated |
| Case notes, follow-up date, history date filter, notifications | Implemented, API tested; UI demonstration pending |
| Clinician and administrator dashboards | Implemented (role-protected, real counts); demonstrated for the Patient role (access denied) and the Administrator role |
| Docker configuration | Written, not built or run |
| Severity / risk classification | Not implemented: dataset has no severity labels (section 6) |
| Lesion detection / segmentation | Not implemented: dataset has image-level labels only (`docs/GRADCAM_LOCALIZATION_REPORT.md`) |

## 2. Model experiments

Same patient-level split (1,477 / 361 / 460), seed 42 and weighted cross-entropy for every run. Models were compared on validation; the test split was evaluated once, only for the two finalists (ConvNeXt-Tiny and ViT-B/16).

| Model | Val acc | Val macro F1 | Test acc | Test macro F1 | ms per image | Params |
|---|---|---|---|---|---|---|
| MobileNetV3-Large fine-tuned (deployed) | 61.22% | 56.53% | 57.39% | 51.02% | - | 4.2M |
| ConvNeXt-Tiny | 66.20% | 61.88% | 60.43% | 60.84% | 15.3 | 27.8M |
| Swin-T | 64.82% | 61.74% | - | - | 19.3 | 27.5M |
| ViT-B/16 | 71.75% | 66.04% | 67.39% | 62.46% | 32.9 | 85.8M |

MobileNetV3-Large versus EfficientNet-B0: `docs/PHASE5_MODEL_COMPARISON_REPORT.md`.

- ViT-B/16 had the best validation macro F1 (66.04%) and, among the models evaluated on test, the best test accuracy (67.39%) and macro F1 (62.46%).
- ViT-B/16 was right and ConvNeXt-Tiny wrong on 76 test images, the reverse on 44 (exact McNemar p = 0.0045); single seed, one dataset.
- SCC remains weak for ViT-B/16 on test: precision 0.21, recall 0.31 (39 images). MEL has only 10 test images.
- Ensemble (mean softmax of ConvNeXt-Tiny and ViT-B/16): validation accuracy 70.36%, macro F1 64.93%, versus ViT-B/16 alone 71.75% and 66.04%. No validation gain, so it was not evaluated on test.

Learning-rate experiment (MobileNetV3-Large, only the learning rate changed, validation macro F1):

| LR | BatchNorm in training mode | Feature extractor in eval mode (original trainer) |
|---|---|---|
| 0.001 | 58.81% (acc 65.93%) | 61.58% (acc 69.81%) |
| 0.0001 | 58.68% (acc 66.48%) | 54.72% (acc 63.43%) |
| 1e-05 | 45.16% (acc 50.69%) | 56.69% (acc 61.50%) |

- With the feature extractor in eval mode, lr 1e-5 gave 61.50% validation accuracy, close to the deployed model (61.22%); without it the run fell to 50.69%, below the starting checkpoint (58.45%). This is consistent with BatchNorm statistic updates causing the degradation (one run per setting).
- The ranking of learning rates differed between the two setups, so the experiment is inconclusive about the best learning rate. Details: `docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md`.

- Overfitting: training accuracy reached 87% to 97% while validation accuracy stayed at 65% to 77%; validation loss was lowest at epoch 3 to 5 and early stopping ended each run.
- Selected model: ViT-B/16 is the best research result. MobileNetV3-Large stays deployed: it is far smaller (4.2M versus 85.8M parameters) and faster, and Grad-CAM, calibration, tests and the Docker setup are built on it. Full tables: `docs/ADVANCED_MODELS_STATUS.md`. No clinical reliability is claimed.

## 3. Confidence and calibration (MobileNetV3-Large, test split)
ECE 0.0739 to 0.0429 after temperature scaling (T = 1.135, fitted on validation only); NLL 1.057 to 1.043. Score at or above 0.8: 98 predictions, 14 incorrect (accuracy 85.7%); score below 0.5: accuracy 34.5%; 67 ambiguous predictions (top-1 minus top-2 below 0.10). The model is overconfident (mean score 64.5% versus accuracy 57.4%). Details: `docs/CALIBRATION_REPORT.md`.

## 4. Image-quality validation
On 60 test images the original blur threshold (100) flagged 26.7% of untouched images; a threshold of 40 flagged 6.7% with equal detection of synthetic blur. A visual review found no clean separation (clear low-texture images scored low). Blur is therefore a warning that the user must acknowledge; exposure problems still block prediction (version 1.1.0). The manual-reference comparison was not completed. See `docs/IMAGE_QUALITY_VALIDATION.md`.

## 5. Explainability (six test images, exploratory)
Heatmaps differ per image and stay aligned. They centre on the lesion for the BCC and SEK examples; for the incorrect MEL and NEV cases the heat lies mostly away from the lesion; in the SCC example it overlaps a pen mark. No map was blank or saturated. This does not prove correctness; a marking-removal experiment would be needed to test a pen-mark shortcut. See `docs/GRADCAM_OBSERVATIONS.md`.

## 6. Risk and severity
Not feasible with PAD-UFES-20: labels are disease names only, with no severity, stage, outcome or urgency. No risk score is shown. See `docs/RISK_SEVERITY_FEASIBILITY_REPORT.md`.

## 7. Testing
90 automated tests pass; manual workflow checks and the full matrix are in `docs/TEST_EVIDENCE.md`.

## 8. Known limitations
- Small dataset and test set; rare classes (MEL, SCC) have very few samples; no external validation.
- Scores are softmax outputs, not clinical probabilities; confidently incorrect predictions occur.
- Grad-CAM is low-resolution (7x7 upsampled) and is not segmentation.
- Quality metrics are proxies; lesion visibility and background interference are not assessed.
- The warning acknowledgement is enforced but not stored.
- Dashboard dataset distribution is a static reference from the audit report.
- Notifications have no read state or external delivery.
- Experiments are single runs with one seed on a small validation set; checkpoints are chosen by validation loss, which can pick an epoch with lower validation F1.

## 9. Unfinished work and blockers
- Docker build and containerised workflow not executed (`docs/DOCKER_DEPLOYMENT.md`).
- Manual reference labelling for quality validation not done.
- Responsive layout (tablet/mobile) not systematically checked.
- Screenshots and a demonstration recording must be captured from the running application and attached separately.
- Not deployed to a public host; no HTTPS configured.


## 10. Design decisions (answers to the Milestone 3 questions)
- **Result screen versus history screen.** The result screen shows the analysis just produced in full: prediction, model score, Top-3, quality status, the preprocessed model input, Grad-CAM and export buttons. The history lists saved records (date, file, class, score, model version) and opens any record for its details and exports; the compare screen places two saved records side by side.
- **Visible immediately versus on demand.** Immediately: predicted class, model score, Top-3, analysis time and the limitation statement. On demand: Grad-CAM (requested after the prediction is saved), model input, exports, case notes and comparison.
- **If Grad-CAM is unavailable.** The analysis does not fail. Grad-CAM is a separate request made after the prediction is saved; a failure shows an error for the visualisation only and the prediction record remains.
- **If the model is updated.** An old prediction is never replaced. A new analysis creates a new record linked to its model version; history shows the version, and the compare screen warns when two records used different versions.
- **Distinguishing analyses on different dates.** Each analysis has its own prediction id, a UTC creation timestamp, and its image and case ids; history is ordered by time and can be filtered by date.
- **Only real outputs are shown.** Results, scores, Top-3, dashboards and exports are read from saved prediction records written by the inference service. Two panels are static and labelled as such: the dataset class distribution (from the dataset audit) and the model information panel.
- **Preprocessed image.** Shown in the result screen, regenerated deterministically from the stored original; it is not stored separately (`docs/PREPROCESSING_PIPELINE.md`).

# DermAI - Risk and Severity Feasibility Assessment

## 1. Dataset label audit (PAD-UFES-20)
| Item | Finding |
|---|---|
| Diagnostic labels | 6 classes: ACK, BCC, MEL, NEV, SCC, SEK (disease names only) |
| Severity grade | Not present |
| Disease stage / Breslow thickness / TNM | Not present |
| Clinical outcome / follow-up | Not present |
| Urgency / triage label | Not present |
| Clinical annotations available | Patient/lesion metadata (age, region, symptoms, Fitzpatrick type); biopsy-confirmed diagnosis for part of the data |
| Lesion masks / bounding boxes | Not found in the audited files |

Verify against `docs/PAD_UFES_20_AUDIT_REPORT.md` and the metadata CSV columns before submission.

## 2. Feasibility conclusion
**Low / moderate / high severity classification is NOT feasible with the current dataset.**
- A disease name is not a severity grade. The same class (e.g. BCC, MEL) spans a wide range of severity.
- No source documentation in the project provides a clinically validated mapping from these classes to severity.
- Model confidence must not substitute for severity: it measures the model's score for a class, not clinical seriousness.
- Therefore no risk score or risk category is implemented. This is an accepted outcome.

## 3. Confidence is evaluated separately
See `docs/CALIBRATION_REPORT.md` and `ml/scripts/calibration_analysis.py` (reliability diagram, ECE, high-confidence errors, ambiguous predictions).

## 4. Responsible output for the prediction screen
Display: predicted class, model score, Top-3 predictions, model version, analysis timestamp, Grad-CAM (if available), image-quality status, and the statement:
"AI predictions are informational and are not a substitute for professional medical assessment. Model scores are not clinically validated probabilities. No severity or risk assessment is provided."

## 5. Data needed in future to support risk analysis
- Clinician-assigned severity or urgency labels per lesion, with documented criteria.
- Staging/outcome data (histopathology grade, follow-up outcomes).
- A project-defined research protocol approved by a clinical supervisor.
- Larger external validation set including more MEL and SCC cases.

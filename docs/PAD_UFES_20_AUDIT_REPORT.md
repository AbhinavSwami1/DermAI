# DermAI - PAD-UFES-20 Dataset Audit Report

## 1. Dataset Overview

- Dataset: PAD-UFES-20
- Total images: 2298
- Unique patients: 1373
- Unique patient-lesion combinations: 1891
- Metadata columns: 26

## 2. Disease Class Distribution

diagnostic
BCC    845
ACK    730
NEV    244
SEK    235
SCC    192
MEL     52

## 3. Image Matching

- Total image files: 2298
- Matched metadata records: 2298
- Missing images: 0
- Unlisted images: 0

## 4. Image Quality

- Readable images: 2298
- Unreadable images: 0
- Image formats: PNG
- Color modes: RGB and RGBA
- Image dimensions: Variable

## 5. Patient and Lesion Analysis

- Unique patients: 1373
- Unique lesions: 1641
- Patient-lesion combinations: 1891
- Combinations with conflicting diagnostic labels: 0

Note: lesion_id is not globally unique. Use the combination
(patient_id, lesion_id) for lesion-level analysis.

## 6. Cross-Validation Strategy

- Method: StratifiedGroupKFold
- Number of folds: 5
- Random state: 42
- Grouping column: patient_id
- Target column: diagnostic

## 7. Leakage Verification

- Patient overlap between train and test: 0
- Image overlap between train and test: 0
- All six classes present in every test fold: Yes

## 8. Important Considerations

- MEL is the smallest class, with only 52 images.
- Class imbalance must be considered during model training.
- Patient-level grouping must be preserved in future experiments.
- These dataset checks do not establish clinical validity or model accuracy.

## 9. Conclusion

The PAD-UFES-20 dataset has been audited for metadata,
image availability, image quality, disease distribution,
patient-level grouping, and cross-validation leakage.

Five reproducible patient-safe folds were generated
and independently verified.

This dataset is ready for the next stage of controlled
preprocessing and model experimentation.
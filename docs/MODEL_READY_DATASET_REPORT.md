\# DermAI \- Model Ready Dataset Report
\#\# 1\. Dataset Overview
Dataset: PAD-UFES-20
Total Images: 2298
Number of Disease Classes: 6
Image Format: PNG
Image Dimensions: 224 x 224
Color Mode: RGB
Tensor Format: PyTorch CHW
Data Type: float32
Pixel Range: 0 to 1
\#\# 2\. Disease Classes
\| Class \| Label \|
\|\-\-\-\|\-\-\-:\|
\| ACK \| 0 \|
\| BCC \| 1 \|
\| MEL \| 2 \|
\| NEV \| 3 \|
\| SCC \| 4 \|
\| SEK \| 5 \|
\#\# 3\. Dataset Splitting
Patient-level grouping was used to prevent
patient overlap between partitions.
\| Partition \| Images \|
\|\-\-\-\|\-\-\-:\|
\| Training \| 1477 \|
\| Validation \| 361 \|
\| Testing \| 460 \|
\| Total \| 2298 \|
Outer split:
\- StratifiedGroupKFold
\- 5 folds
\- Random state: 42
Selected outer fold: 1
Inner split:
\- GroupShuffleSplit
\- Validation size: 20%
\- Random state: 42
Patient overlap between training, validation,
and testing partitions: 0.
Note: The inner validation split is group-based
but not stratified.
\#\# 4\. Image Augmentation
Training transformations:
\- Random horizontal flip
\- Random vertical flip
\- Random rotation up to 15 degrees
\- Conversion to PyTorch tensor
Validation and testing:
\- Conversion to PyTorch tensor only
\- No random augmentation
\#\# 5\. PyTorch Dataset and DataLoaders
Custom Dataset:
DermAIDataset
Batch size: 16
\| Partition \| Images \| Batches \|
\|\-\-\-\|\-\-\-:\|\-\-\-:\|
\| Training \| 1477 \| 93 \|
\| Validation \| 361 \| 23 \|
\| Testing \| 460 \| 29 \|
All three DataLoaders were tested successfully.
Verified image batch shape:
[16, 3, 224, 224]
Verified label batch shape:
[16]
Image dtype: float32
Label dtype: int64
\#\# 6\. Important Dataset Considerations
\- The dataset contains class imbalance\.
\- MEL has only 52 images overall\.
\- Training and validation metrics must be interpreted
 carefully for underrepresented classes.
\- The testing partition must remain untouched
 during model training and model selection.
\- Patient\-level splitting is used to reduce
 data leakage.
\#\# 7\. Phase 3 Status
Model-ready dataset preparation: COMPLETED
Data loading and batch verification: PASSED
Model training: NOT STARTED
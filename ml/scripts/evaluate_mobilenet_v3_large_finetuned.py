import sys
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import torch

from torch.utils.data import DataLoader

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_score,
    recall_score,
    f1_score,
)

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"

sys.path.insert(0, str(ML_ROOT / "src"))

from data.dataset import DermAIDataset
from data.augmentations import eval_transform
from models.mobilenet_large import create_mobilenet_v3_large


SPLIT_DIR = (
    ML_ROOT / "datasets" / "splits" /
    "fold_1_train_val_test"
)

IMAGE_DIR = (
    ML_ROOT / "datasets" / "processed" /
    "pad_ufes_20"
)

CHECKPOINT_PATH = (
    ML_ROOT / "checkpoints" / "mobilenet" /
    "best_mobilenet_v3_large_finetuned.pth"
)

OUTPUT_DIR = (
    ML_ROOT / "outputs" /
    "mobilenet_v3_large_finetuned"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]

CLASS_TO_IDX = {
    name: index
    for index, name in enumerate(CLASS_NAMES)
}

BATCH_SIZE = 16


# --------------------------------------------------
# DEVICE
# --------------------------------------------------

def get_device():

    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


# --------------------------------------------------
# LOAD TEST DATASET ONLY
# --------------------------------------------------

def load_test_dataset():

    test_csv = SPLIT_DIR / "test.csv"

    if not test_csv.is_file():
        raise FileNotFoundError(
            f"Test split not found: {test_csv}"
        )

    df = pd.read_csv(test_csv)

    required_columns = [
        "patient_id",
        "lesion_id",
        "img_id",
        "diagnostic",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in test CSV: {missing_columns}"
        )

    df["image_path"] = df["img_id"].apply(
        lambda image_id: str(
            IMAGE_DIR / str(image_id)
        )
    )

    df["label"] = df["diagnostic"].map(
        CLASS_TO_IDX
    )

    if df["label"].isna().any():
        raise ValueError(
            "Unknown diagnostic labels found in test dataset."
        )

    df["label"] = df["label"].astype(int)

    missing_images = df[
        ~df["image_path"].map(
            lambda path: Path(path).is_file()
        )
    ]

    if not missing_images.empty:
        raise FileNotFoundError(
            f"{len(missing_images)} test images are missing."
        )

    print("\nTest dataset loaded successfully.")
    print("Test images:", len(df))

    print("\nTest class distribution:")
    print(
        df["diagnostic"].value_counts().sort_index()
    )

    return df


# --------------------------------------------------
# LOAD CHECKPOINT
# --------------------------------------------------

def load_model(device):

    if not CHECKPOINT_PATH.is_file():
        raise FileNotFoundError(
            f"Checkpoint not found: {CHECKPOINT_PATH}"
        )

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location="cpu",
        weights_only=True
    )

    if checkpoint.get("architecture") != "mobilenet_v3_large":
        raise ValueError(
            "Checkpoint architecture does not match MobileNetV3-Large."
        )

    if checkpoint.get("class_names") != CLASS_NAMES:
        raise ValueError(
            "Checkpoint class order does not match evaluation class order."
        )

    model = create_mobilenet_v3_large(
        pretrained=False
    )

    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=True
    )

    model = model.to(device)
    model.eval()

    print("\nCheckpoint loaded successfully.")
    print("Architecture:", checkpoint["architecture"])
    print("Checkpoint epoch:", checkpoint["epoch"])
    print(
        "Checkpoint validation loss:",
        checkpoint["validation_loss"]
    )
    print(
        "Checkpoint validation accuracy:",
        checkpoint["validation_accuracy"]
    )

    return model, checkpoint


# --------------------------------------------------
# MAIN TEST EVALUATION
# --------------------------------------------------

def main():

    print("\n========================================")
    print("DERMAI - FINAL HELD-OUT TEST EVALUATION")
    print("MobileNetV3-Large Fine-Tuned")
    print("========================================")

    print("\nIMPORTANT:")
    print("Only the held-out test split will be evaluated.")
    print("No training or checkpoint modification will occur.")

    device = get_device()

    print("\nEvaluation device:", device)

    # Load test split only.
    df = load_test_dataset()

    dataset = DermAIDataset(
        df,
        transform=eval_transform
    )

    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    # Load selected checkpoint.
    model, checkpoint = load_model(device)

    all_labels = []
    all_predictions = []
    all_probabilities = []

    # --------------------------------------------------
    # INFERENCE
    # --------------------------------------------------

    print("\nRunning test inference...")

    with torch.inference_mode():

        for batch_index, (images, labels) in enumerate(loader):

            images = images.to(device)

            outputs = model(images)

            probabilities = torch.softmax(
                outputs,
                dim=1
            )

            predictions = outputs.argmax(dim=1)

            all_labels.extend(
                labels.numpy().tolist()
            )

            all_predictions.extend(
                predictions.cpu().numpy().tolist()
            )

            all_probabilities.extend(
                probabilities.cpu().numpy().tolist()
            )

            print(
                f"Processed batch {batch_index + 1}/{len(loader)}"
            )

    # --------------------------------------------------
    # METRICS
    # --------------------------------------------------

    accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    precision_macro = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    precision_weighted = precision_score(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0
    )

    recall_macro = recall_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    recall_weighted = recall_score(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0
    )

    f1_macro = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    f1_weighted = f1_score(
        all_labels,
        all_predictions,
        average="weighted",
        zero_division=0
    )

    print("\n========================================")
    print("FINAL HELD-OUT TEST RESULTS")
    print("========================================")

    print(f"Test images:       {len(all_labels)}")
    print(f"Accuracy:          {accuracy:.4f}")
    print(f"Macro Precision:   {precision_macro:.4f}")
    print(f"Weighted Precision:{precision_weighted:.4f}")
    print(f"Macro Recall:      {recall_macro:.4f}")
    print(f"Weighted Recall:   {recall_weighted:.4f}")
    print(f"Macro F1:          {f1_macro:.4f}")
    print(f"Weighted F1:       {f1_weighted:.4f}")

    # --------------------------------------------------
    # CLASSIFICATION REPORT
    # --------------------------------------------------

    report_dict = classification_report(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        zero_division=0,
        output_dict=True
    )

    report_text = classification_report(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        zero_division=0
    )

    print("\n========================================")
    print("PER-CLASS CLASSIFICATION REPORT")
    print("========================================")

    print(report_text)

    pd.DataFrame(report_dict).transpose().to_csv(
        OUTPUT_DIR / "test_classification_report.csv"
    )

    # --------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------

    cm = confusion_matrix(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES)))
    )

    pd.DataFrame(
        cm,
        index=CLASS_NAMES,
        columns=CLASS_NAMES
    ).to_csv(
        OUTPUT_DIR / "test_confusion_matrix.csv"
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=CLASS_NAMES
    )

    fig, ax = plt.subplots(figsize=(9, 8))

    display.plot(
        ax=ax,
        cmap="Blues",
        values_format="d",
        xticks_rotation=45
    )

    plt.title(
        "MobileNetV3-Large Fine-Tuned - Test Confusion Matrix"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "test_confusion_matrix.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------
    # SAVE TEST PREDICTIONS
    # --------------------------------------------------

    results = df[
        [
            "patient_id",
            "lesion_id",
            "img_id",
            "diagnostic"
        ]
    ].copy()

    results["true_label"] = [
        CLASS_NAMES[index]
        for index in all_labels
    ]

    results["predicted_label"] = [
        CLASS_NAMES[index]
        for index in all_predictions
    ]

    results["correct"] = (
        results["true_label"] ==
        results["predicted_label"]
    )

    for index, class_name in enumerate(CLASS_NAMES):

        results[f"probability_{class_name}"] = [
            row[index]
            for row in all_probabilities
        ]

    results.to_csv(
        OUTPUT_DIR / "test_predictions.csv",
        index=False
    )

    # --------------------------------------------------
    # SAVE METADATA
    # --------------------------------------------------

    metrics = {
        "experiment": "MobileNetV3-Large Fine-Tuned",
        "architecture": checkpoint["architecture"],
        "checkpoint_epoch": checkpoint["epoch"],
        "checkpoint_validation_loss": checkpoint["validation_loss"],
        "checkpoint_validation_accuracy": checkpoint["validation_accuracy"],
        "evaluation_split": "held_out_test",
        "test_samples": len(all_labels),
        "accuracy": accuracy,
        "macro_precision": precision_macro,
        "weighted_precision": precision_weighted,
        "macro_recall": recall_macro,
        "weighted_recall": recall_weighted,
        "macro_f1": f1_macro,
        "weighted_f1": f1_weighted,
        "class_names": CLASS_NAMES,
        "seed": checkpoint.get("seed"),
        "image_size": checkpoint.get("image_size"),
        "normalization": checkpoint.get("normalization"),
        "disclaimer": (
            "Research-only results. Not clinically validated. "
            "Not intended for medical diagnosis or treatment."
        )
    }

    with open(
        OUTPUT_DIR / "test_metrics.json",
        "w"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    print("\n========================================")
    print("TEST EVALUATION COMPLETED")
    print("========================================")

    print("\nSaved outputs:")

    print(OUTPUT_DIR / "test_classification_report.csv")
    print(OUTPUT_DIR / "test_confusion_matrix.csv")
    print(OUTPUT_DIR / "test_confusion_matrix.png")
    print(OUTPUT_DIR / "test_predictions.csv")
    print(OUTPUT_DIR / "test_metrics.json")

    print("\nTest dataset evaluated exactly once by this script.")

    print(
        "\nDISCLAIMER: Research-only evaluation. "
        "Not clinically validated and not suitable "
        "for diagnosis or treatment."
    )


if __name__ == "__main__":
    main()
import sys
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"

sys.path.insert(0, str(ML_ROOT / "src"))

from data.dataset import DermAIDataset
from data.augmentations import eval_transform
from models.mobilenet_large import create_mobilenet_v3_large


SPLIT_DIR = ML_ROOT / "datasets" / "splits" / "fold_1_train_val_test"
IMAGE_DIR = ML_ROOT / "datasets" / "processed" / "pad_ufes_20"

CHECKPOINT_PATH = (
    ML_ROOT / "checkpoints" / "mobilenet" /
    "best_mobilenet_v3_large.pth"
)

OUTPUT_DIR = ML_ROOT / "outputs" / "mobilenet_v3_large"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]

CLASS_TO_IDX = {
    name: index for index, name in enumerate(CLASS_NAMES)
}

BATCH_SIZE = 16


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def main():

    device = get_device()
    print("Evaluation device:", device)

    # Load validation split ONLY.
    df = pd.read_csv(SPLIT_DIR / "validation.csv")

    df["image_path"] = df["img_id"].apply(
        lambda image_id: str(IMAGE_DIR / str(image_id))
    )

    df["label"] = df["diagnostic"].map(CLASS_TO_IDX)

    if df["label"].isna().any():
        raise ValueError("Unknown labels found in validation dataset.")

    df["label"] = df["label"].astype(int)

    if not df["image_path"].map(
        lambda path: Path(path).is_file()
    ).all():
        raise FileNotFoundError("Validation images are missing.")

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

    # Load model architecture.
    model = create_mobilenet_v3_large(pretrained=False)

    checkpoint = torch.load(
        CHECKPOINT_PATH,
        map_location="cpu",
        weights_only=True
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    print("Checkpoint epoch:", checkpoint["epoch"])
    print("Checkpoint validation loss:",
          checkpoint["validation_loss"])

    all_labels = []
    all_predictions = []

    with torch.inference_mode():

        for images, labels in loader:

            images = images.to(device)

            outputs = model(images)
            predictions = outputs.argmax(dim=1)

            all_labels.extend(labels.numpy().tolist())
            all_predictions.extend(
                predictions.cpu().numpy().tolist()
            )

    # Metrics
    accuracy = accuracy_score(
        all_labels, all_predictions
    )

    precision_macro = precision_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    recall_macro = recall_score(
        all_labels,
        all_predictions,
        average="macro",
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

    print("\n========== VALIDATION RESULTS ==========")
    print(f"Accuracy:        {accuracy:.4f}")
    print(f"Macro Precision: {precision_macro:.4f}")
    print(f"Macro Recall:    {recall_macro:.4f}")
    print(f"Macro F1:        {f1_macro:.4f}")
    print(f"Weighted F1:     {f1_weighted:.4f}")

    print("\n========== CLASSIFICATION REPORT ==========")

    report = classification_report(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        zero_division=0
    )

    print(report)

    report_dict = classification_report(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        zero_division=0,
        output_dict=True
    )

    pd.DataFrame(report_dict).transpose().to_csv(
        OUTPUT_DIR / "validation_classification_report.csv"
    )

    # Confusion matrix
    cm = confusion_matrix(
        all_labels,
        all_predictions,
        labels=list(range(len(CLASS_NAMES)))
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

    plt.title("MobileNetV3-Large Validation Confusion Matrix")
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "validation_confusion_matrix.png",
        dpi=300
    )

    plt.close()

    # Save predictions for error analysis.
    results = df[["patient_id", "lesion_id", "img_id", "diagnostic"]].copy()

    results["true_label"] = [
        CLASS_NAMES[index] for index in all_labels
    ]

    results["predicted_label"] = [
        CLASS_NAMES[index] for index in all_predictions
    ]

    results["correct"] = (
        results["true_label"] == results["predicted_label"]
    )

    results.to_csv(
        OUTPUT_DIR / "validation_predictions.csv",
        index=False
    )

    print("\nSaved validation outputs in:")
    print(OUTPUT_DIR)

    print("\nTest dataset was NOT loaded or evaluated.")


if __name__ == "__main__":
    main()
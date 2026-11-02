import random
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"

sys.path.insert(0, str(ML_ROOT / "src"))

from data.dataset import DermAIDataset
from data.augmentations import train_transform, eval_transform
from models.efficientnet_b0 import create_efficientnet_b0
from training.loss import calculate_class_weights, create_weighted_loss
from training.trainer import train_one_epoch, validate_one_epoch


SPLIT_DIR = ML_ROOT / "datasets" / "splits" / "fold_1_train_val_test"
IMAGE_DIR = ML_ROOT / "datasets" / "processed" / "pad_ufes_20"

CHECKPOINT_DIR = ML_ROOT / "checkpoints" / "efficientnet"
OUTPUT_DIR = ML_ROOT / "outputs" / "efficientnet_b0"

CHECKPOINT_PATH = CHECKPOINT_DIR / "best_efficientnet_b0.pth"


# Configuration
SEED = 42
NUM_CLASSES = 6
BATCH_SIZE = 16
EPOCHS = 20
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
PATIENCE = 5

CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]

CLASS_TO_IDX = {
    name: index for index, name in enumerate(CLASS_NAMES)
}


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def select_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")

    if torch.cuda.is_available():
        return torch.device("cuda")

    return torch.device("cpu")


def load_split(filename):
    df = pd.read_csv(SPLIT_DIR / filename)

    df["image_path"] = df["img_id"].apply(
        lambda image_id: str(IMAGE_DIR / str(image_id))
    )

    df["label"] = df["diagnostic"].map(CLASS_TO_IDX)

    if df["label"].isna().any():
        raise ValueError(f"Unknown labels in {filename}")

    df["label"] = df["label"].astype(int)

    missing = df["image_path"].apply(
        lambda path: not Path(path).is_file()
    )

    if missing.any():
        raise FileNotFoundError(
            f"{missing.sum()} images missing in {filename}"
        )

    return df


class EarlyStopping:
    def __init__(self, patience=5):
        self.patience = patience
        self.best_loss = float("inf")
        self.counter = 0

    def update(self, validation_loss):
        if validation_loss < self.best_loss:
            self.best_loss = validation_loss
            self.counter = 0
            return True

        self.counter += 1
        return False

    def should_stop(self):
        return self.counter >= self.patience


def main():

    set_seed(SEED)
    device = select_device()

    print("\n====================================")
    print("DERMAI - EfficientNet-B0 Training")
    print("====================================")
    print("Device:", device)
    print("Seed:", SEED)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if CHECKPOINT_PATH.exists():
        raise FileExistsError(
            f"Checkpoint already exists: {CHECKPOINT_PATH}\n"
            "Move or rename it before starting a new run."
        )

    # Load train and validation only.
    train_df = load_split("train.csv")
    val_df = load_split("validation.csv")

    print("\nDataset sizes:")
    print("Train:", len(train_df))
    print("Validation:", len(val_df))
    print("Test: reserved for final evaluation")

    train_dataset = DermAIDataset(
        train_df,
        transform=train_transform
    )

    val_dataset = DermAIDataset(
        val_df,
        transform=eval_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )

    # Model
    print("\nLoading pretrained EfficientNet-B0...")

    model = create_efficientnet_b0(pretrained=True)

    # Freeze the feature extractor.
    for parameter in model.parameters():
        parameter.requires_grad = False

    # Train only the final classification layer.
    for parameter in model.classifier[1].parameters():
        parameter.requires_grad = True

    model = model.to(device)

    trainable_parameters = [
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    print(
        "Trainable parameters:",
        sum(p.numel() for p in trainable_parameters)
    )

    # Loss and optimizer
    class_weights = calculate_class_weights(
        train_df,
        num_classes=NUM_CLASSES
    )

    criterion = create_weighted_loss(
        class_weights,
        device
    )

    optimizer = torch.optim.Adam(
        trainable_parameters,
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2
    )

    early_stopping = EarlyStopping(
        patience=PATIENCE
    )

    # Training loop
    history = []

    for epoch in range(1, EPOCHS + 1):

        print(f"\nEpoch {epoch}/{EPOCHS}")

        train_loss, train_accuracy = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device
        )

        val_loss, val_accuracy = validate_one_epoch(
            model,
            val_loader,
            criterion,
            device
        )

        scheduler.step(val_loss)

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"Train Loss: {train_loss:.4f} | "
            f"Train Accuracy: {train_accuracy:.4f}"
        )

        print(
            f"Val Loss: {val_loss:.4f} | "
            f"Val Accuracy: {val_accuracy:.4f}"
        )

        print(f"Learning Rate: {current_lr:.7f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "learning_rate": current_lr
        })

        # Save best checkpoint based on validation loss.
        improved = early_stopping.update(val_loss)

        if improved:

            torch.save({
                "architecture": "efficientnet_b0",
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "epoch": epoch,
                "validation_loss": val_loss,
                "validation_accuracy": val_accuracy,
                "class_names": CLASS_NAMES,
                "class_to_idx": CLASS_TO_IDX,
                "seed": SEED,
                "image_size": 224,
                "normalization": "ImageNet mean/std",
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "weight_decay": WEIGHT_DECAY,
                "training_strategy": "frozen_backbone_classifier_only"
            }, CHECKPOINT_PATH)

            print("Best checkpoint saved!")

        if early_stopping.should_stop():
            print("\nEarly stopping triggered.")
            break

    # Save training history.
    history_df = pd.DataFrame(history)

    history_csv = OUTPUT_DIR / "training_history.csv"
    history_df.to_csv(history_csv, index=False)

    # Loss curve
    plt.figure(figsize=(9, 5))
    plt.plot(
        history_df["epoch"],
        history_df["train_loss"],
        label="Training Loss"
    )
    plt.plot(
        history_df["epoch"],
        history_df["val_loss"],
        label="Validation Loss"
    )
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("EfficientNet-B0 Loss")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "loss_curve.png", dpi=300)
    plt.close()

    # Accuracy curve
    plt.figure(figsize=(9, 5))
    plt.plot(
        history_df["epoch"],
        history_df["train_accuracy"],
        label="Training Accuracy"
    )
    plt.plot(
        history_df["epoch"],
        history_df["val_accuracy"],
        label="Validation Accuracy"
    )
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("EfficientNet-B0 Accuracy")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "accuracy_curve.png", dpi=300)
    plt.close()

    print("\n====================================")
    print("TRAINING COMPLETED")
    print("====================================")
    print("Best checkpoint:", CHECKPOINT_PATH)
    print("Training history:", history_csv)
    print("Output directory:", OUTPUT_DIR)
    print("\nTest dataset was NOT used.")


if __name__ == "__main__":
    main()
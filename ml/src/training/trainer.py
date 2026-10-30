import torch
import torch.nn as nn


def freeze_backbone(model):
    # Freeze all model parameters
    for param in model.parameters():
        param.requires_grad = False

    # Unfreeze final classification layer
    for param in model.classifier[3].parameters():
        param.requires_grad = True

    return model


def get_trainable_parameters(model):
    return [
        param
        for param in model.parameters()
        if param.requires_grad
    ]

def train_one_epoch(model, loader, criterion, optimizer, device):

    model.train()

    # Keep frozen feature extractor in evaluation mode
    model.features.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

        predictions = outputs.argmax(dim=1)

        correct += (predictions == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_accuracy = correct / total

    return epoch_loss, epoch_accuracy

def validate_one_epoch(model, loader, criterion, device):

    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    with torch.inference_mode():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)

            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_accuracy = correct / total

    return epoch_loss, epoch_accuracy

from pathlib import Path


class EarlyStopping:

    def __init__(self, patience=5, min_delta=0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float("inf")
        self.counter = 0
        self.should_stop = False

    def __call__(self, validation_loss):

        if validation_loss < self.best_loss - self.min_delta:
            self.best_loss = validation_loss
            self.counter = 0

        else:
            self.counter += 1

            if self.counter >= self.patience:
                self.should_stop = True


def save_checkpoint(model, optimizer, epoch, val_loss, path):

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "validation_loss": val_loss
    }, path)

    print(f"Best checkpoint saved: {path}")
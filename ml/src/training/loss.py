import torch
import torch.nn as nn


def calculate_class_weights(dataframe, num_classes=6):

    class_counts = (
        dataframe["label"]
        .value_counts()
        .sort_index()
    )

    weights = len(dataframe) / (
        num_classes * class_counts
    )

    return torch.tensor(
        weights.values,
        dtype=torch.float32
    )


def create_weighted_loss(class_weights, device):

    class_weights = class_weights.to(device)

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    return criterion
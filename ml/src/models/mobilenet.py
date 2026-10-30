import torch
import torch.nn as nn
from torchvision import models


NUM_CLASSES = 6


def create_mobilenet_model(pretrained=True):

    if pretrained:
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
    else:
        weights = None

    model = models.mobilenet_v3_small(
        weights=weights
    )

    # Replace the final classification layer
    input_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        input_features,
        NUM_CLASSES
    )

    return model
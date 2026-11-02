import torch.nn as nn
from torchvision import models

NUM_CLASSES = 6


def create_efficientnet_b0(pretrained=True):

    weights = (
        models.EfficientNet_B0_Weights.DEFAULT
        if pretrained
        else None
    )

    model = models.efficientnet_b0(weights=weights)

    input_features = model.classifier[1].in_features

    model.classifier[1] = nn.Linear(
        input_features,
        NUM_CLASSES
    )

    return model
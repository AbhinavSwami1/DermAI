import torch.nn as nn
from torchvision import models

NUM_CLASSES = 6


def create_mobilenet_v3_large(pretrained=True):
    """
    Create MobileNetV3-Large for six-class DermAI classification.

    Args:
        pretrained: Use ImageNet pretrained weights if True.

    Returns:
        MobileNetV3-Large model with a six-class classification head.
    """

    weights = (
        models.MobileNet_V3_Large_Weights.DEFAULT
        if pretrained
        else None
    )

    model = models.mobilenet_v3_large(weights=weights)

    input_features = model.classifier[3].in_features

    model.classifier[3] = nn.Linear(
        input_features,
        NUM_CLASSES
    )

    return model
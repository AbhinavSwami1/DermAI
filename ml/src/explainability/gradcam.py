import torch
import torch.nn.functional as F


class GradCAM:
    """
    Grad-CAM implementation for CNN-based image classification.

    Generates a class-discriminative activation heatmap.
    This is an attention visualization, not a verified lesion boundary.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        self.forward_handle = target_layer.register_forward_hook(
            self._save_activation
        )

    def _save_activation(self, module, inputs, output):
        self.activations = output
        output.retain_grad()

    def generate(self, input_tensor, target_class=None):
        self.model.zero_grad(set_to_none=True)

        output = self.model(input_tensor)

        if target_class is None:
            target_class = int(output.argmax(dim=1).item())

        score = output[:, target_class].sum()
        score.backward()

        gradients = self.activations.grad
        activations = self.activations

        weights = gradients.mean(dim=(2, 3), keepdim=True)

        cam = (weights * activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)

        cam = F.interpolate(
            cam,
            size=input_tensor.shape[2:],
            mode="bilinear",
            align_corners=False
        )

        cam = cam[0, 0]

        cam_min = cam.min()
        cam_max = cam.max()

        cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)

        return cam.detach().cpu().numpy(), output.detach()

    def close(self):
        self.forward_handle.remove()

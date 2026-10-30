import sys
from pathlib import Path

import pandas as pd
import torch
import matplotlib.pyplot as plt
import numpy as np

from PIL import Image
from torchvision import transforms

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "ml" / "src"))

from models.mobilenet import create_mobilenet_model
from explainability.gradcam import GradCAM


DEVICE = torch.device(
    "mps" if torch.backends.mps.is_available() else "cpu"
)

CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]

TEST_CSV = PROJECT_ROOT / "ml/datasets/splits/fold_1_test.csv"
IMAGE_DIR = PROJECT_ROOT / "ml/datasets/processed/pad_ufes_20"
CHECKPOINT = PROJECT_ROOT / "ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth"

OUTPUT_DIR = PROJECT_ROOT / "ml/outputs/gradcam"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Load test metadata
df = pd.read_csv(TEST_CSV)

# Select one test image per class
selected_rows = []

for class_name in CLASS_NAMES:
    class_rows = df[df["diagnostic"] == class_name]

    if not class_rows.empty:
        selected_rows.append(class_rows.iloc[0])

# Load trained model
model = create_mobilenet_model(pretrained=False)

checkpoint = torch.load(
    CHECKPOINT,
    map_location="cpu",
    weights_only=False
)

model.load_state_dict(checkpoint["model_state_dict"])
model = model.to(DEVICE)
model.eval()

# Grad-CAM target layer
gradcam = GradCAM(
    model=model,
    target_layer=model.features[-1]
)

results = []

print("Device:", DEVICE)
print("Selected samples:", len(selected_rows))

for index, row in enumerate(selected_rows, start=1):

    filename = str(row["img_id"])
    actual_label = str(row["diagnostic"])

    image_path = IMAGE_DIR / filename

    if not image_path.exists():
        print("Missing image:", image_path)
        continue

    original_image = Image.open(image_path).convert("RGB")
    input_tensor = transform(original_image).unsqueeze(0).to(DEVICE)

    # Generate Grad-CAM
    heatmap, logits = gradcam.generate(input_tensor)

    probabilities = torch.softmax(logits, dim=1)[0]
    predicted_index = int(probabilities.argmax().item())

    predicted_label = CLASS_NAMES[predicted_index]
    confidence = float(probabilities[predicted_index].item())

    # Resize heatmap to original image dimensions
    heatmap_image = Image.fromarray(
        np.uint8(heatmap * 255)
    ).resize(original_image.size)

    heatmap_array = np.asarray(heatmap_image) / 255.0

    # Generate original + overlay comparison
    plt.figure(figsize=(10, 4))

    plt.subplot(1, 2, 1)
    plt.imshow(original_image)
    plt.title(f"Original Image\nActual: {actual_label}")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(original_image)
    plt.imshow(heatmap_array, cmap="jet", alpha=0.45)
    plt.title(
        f"Grad-CAM Overlay\nPredicted: {predicted_label}"
        f"\nConfidence: {confidence:.2%}"
    )
    plt.axis("off")

    plt.tight_layout()

    output_path = OUTPUT_DIR / f"gradcam_{index}_{actual_label}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    results.append({
        "image": filename,
        "actual_label": actual_label,
        "predicted_label": predicted_label,
        "confidence": confidence,
        "visualization": str(output_path.relative_to(PROJECT_ROOT))
    })

    print(
        f"{index}. {filename} | Actual: {actual_label} | "
        f"Predicted: {predicted_label} | Confidence: {confidence:.4f}"
    )

gradcam.close()

# Save results
results_df = pd.DataFrame(results)
results_df.to_csv(
    OUTPUT_DIR / "gradcam_results.csv",
    index=False
)

print("\nGrad-CAM generation completed.")
print("Visualizations:", OUTPUT_DIR)
print("Results CSV:", OUTPUT_DIR / "gradcam_results.csv")
print("Generated images:", len(results))

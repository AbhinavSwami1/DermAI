"""Grad-CAM validation on test images (exploratory, not clinical validation).

Needs the trained checkpoint. Run from repo root:
  PYTHONPATH="$PWD:$PWD/backend" python ml/scripts/gradcam_observations.py [--per-class 1]
Writes docs/figures/gradcam/*.png and docs/GRADCAM_OBSERVATIONS.md. Automated numbers
only flag images worth inspecting; the 'Reviewer observation' column must be filled by a person.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from matplotlib import colormaps
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "backend"))
from app.services.inference_service import CLASS_NAMES, MODEL_EXECUTION_LOCK, MODEL_VERSION, load_model, preprocess_image  # noqa: E402
from ml.src.explainability.gradcam import GradCAM  # noqa: E402

ML = ROOT / "ml"


def heat_metrics(h):
    h = np.asarray(h, dtype=np.float64)
    size = h.shape[0]
    yy, xx = np.mgrid[0:size, 0:size]
    edge = np.minimum.reduce([yy, xx, size - 1 - yy, size - 1 - xx]) / size
    border = edge < 0.2
    total = h.sum() + 1e-12
    border_ratio = (h[border].sum() / total) / border.mean()  # >1: more heat on the border than a uniform map
    peak = np.unravel_index(h.argmax(), h.shape)
    return {"border_ratio": float(border_ratio), "coverage_gt_0.5": float((h > 0.5).mean()),
            "max": float(h.max()), "std": float(h.std()), "peak_xy": (float(round(peak[1] / size, 2)), float(round(peak[0] / size, 2))),
            "blank": bool(h.max() < 0.05 or h.std() < 0.01), "saturated": bool((h > 0.5).mean() > 0.8)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=1)
    ap.add_argument("--images-dir", default=str(ML / "datasets" / "processed" / "pad_ufes_20"))
    args = ap.parse_args()

    test = pd.read_csv(ML / "datasets" / "splits" / "fold_1_train_val_test" / "test.csv")
    picks = test.groupby("diagnostic").head(args.per_class).sort_values("diagnostic")
    fig_dir = ROOT / "docs" / "figures" / "gradcam"; fig_dir.mkdir(parents=True, exist_ok=True)
    model, device = load_model()

    lines = ["# Grad-CAM Observations (exploratory)", "",
             f"- Model: `{MODEL_VERSION}`", "- Target layer: `model.features[-1]` (last convolutional block of MobileNetV3-Large)",
             "- Images: test split only. Grad-CAM is not lesion segmentation and does not show a prediction is correct.", "",
             "Automated columns: `border ratio` > 1 means more heat on the outer 20% frame than a uniform map (possible background/artifact focus); "
             "blank/saturated flag suspicious maps. They only flag images to inspect.", "",
             "| Image | True class | Predicted (score) | Border ratio | Coverage >0.5 | Peak (x,y) | Blank | Saturated | Reviewer observation |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, row in picks.iterrows():
        data = (Path(args.images_dir) / str(row["img_id"])).read_bytes()
        x = preprocess_image(data).to(device)
        with MODEL_EXECUTION_LOCK:
            with torch.no_grad():  # before the hook exists
                probs = torch.softmax(model(x), 1)[0].cpu().numpy()
            cam = GradCAM(model=model, target_layer=model.features[-1])
            try:
                model.zero_grad(set_to_none=True)
                with torch.enable_grad():
                    heat, _ = cam.generate(x)
            finally:
                cam.close(); model.zero_grad(set_to_none=True)
        pred = int(probs.argmax())
        orig = Image.open(Path(args.images_dir) / str(row["img_id"])).convert("RGB").resize((224, 224))
        heat224 = np.asarray(Image.fromarray(np.uint8(np.clip(heat, 0, 1) * 255)).resize((224, 224), Image.Resampling.BILINEAR)) / 255.0
        overlay = Image.blend(orig, Image.fromarray(np.uint8(colormaps["jet"](heat224)[..., :3] * 255)), 0.45)
        fig, ax = plt.subplots(1, 3, figsize=(9, 3.3))
        for a, im, t in zip(ax, [orig, heat224, overlay], ["Original", "Heatmap", "Overlay"]):
            a.imshow(im, cmap="jet" if t == "Heatmap" else None, vmin=0, vmax=1); a.set_title(t); a.axis("off")
        fig.suptitle(f"{row['img_id']}  true={row['diagnostic']}  pred={CLASS_NAMES[pred]} ({probs[pred]*100:.1f}%)", fontsize=9)
        fig.tight_layout(); fig.savefig(fig_dir / f"{Path(str(row['img_id'])).stem}.png", dpi=120); plt.close(fig)
        hm = heat_metrics(heat224)
        lines.append(f"| {row['img_id']} | {row['diagnostic']} | {CLASS_NAMES[pred]} ({probs[pred]*100:.1f}%) | {hm['border_ratio']:.2f} | "
                     f"{hm['coverage_gt_0.5']:.2f} | {hm['peak_xy']} | {hm['blank']} | {hm['saturated']} | _to be completed after viewing_ |")
    lines += ["", "## Questions to answer per image after viewing `docs/figures/gradcam/`",
              "1. Does the heatmap change between images?", "2. Does it highlight the lesion region or background/artifacts (hair, ruler, skin edge)?",
              "3. Does the overlay stay aligned with the original?", "4. Are any heatmaps blank, saturated or suspicious?", "",
              "## Limitations", "- Single target layer; low spatial resolution (7x7 upsampled).", "- Explanation of the predicted class, including incorrect predictions.",
              "- No lesion masks exist, so overlap with the lesion cannot be measured quantitatively."]
    (ROOT / "docs" / "GRADCAM_OBSERVATIONS.md").write_text("\n".join(lines) + "\n")
    print("Wrote docs/GRADCAM_OBSERVATIONS.md and figures in", fig_dir)


if __name__ == "__main__":
    main()

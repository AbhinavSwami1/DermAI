"""Calibration analysis for the selected DermAI checkpoint.

- Temperature is fitted on VALIDATION data only.
- TEST data is used once, for final evaluation.
- Outputs: ml/outputs/calibration/{calibration_results.json, reliability_diagram.png,
  high_confidence_errors_test.csv}

Run from repo root:  python ml/scripts/calibration_analysis.py
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT / "src"))

from data.augmentations import eval_transform
from data.dataset import DermAIDataset
from evaluation.calibration import (brier, ece, fit_temperature, nll,
                                    reliability_bins, softmax)
from models.mobilenet_large import create_mobilenet_v3_large

SPLIT_DIR = ML_ROOT / "datasets" / "splits" / "fold_1_train_val_test"
IMAGE_DIR = ML_ROOT / "datasets" / "processed" / "pad_ufes_20"
CHECKPOINT = ML_ROOT / "checkpoints" / "mobilenet" / "best_mobilenet_v3_large_finetuned.pth"
OUT = ML_ROOT / "outputs" / "calibration"
CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
HIGH_CONF = 0.8
AMBIGUOUS_MARGIN = 0.10  # top-1 minus top-2 score; reporting threshold only


def get_logits(model, split, device):
    df = pd.read_csv(SPLIT_DIR / f"{split}.csv")
    df["image_path"] = df["img_id"].apply(lambda i: str(IMAGE_DIR / str(i)))
    df["label"] = df["diagnostic"].map({n: i for i, n in enumerate(CLASS_NAMES)}).astype(int)
    loader = DataLoader(DermAIDataset(df, eval_transform), batch_size=32, shuffle=False)
    out = []
    with torch.no_grad():
        for x, _ in loader:
            out.append(model(x.to(device)).cpu().numpy())
    return np.concatenate(out), df["label"].to_numpy(), df


def summary(logits, labels, T):
    p = softmax(logits, T)
    return {"temperature": T, "accuracy": float((p.argmax(1) == labels).mean()),
            "ece_10bins": ece(p, labels), "nll": nll(p, labels), "brier": brier(p, labels),
            "mean_confidence": float(p.max(1).mean())}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    ckpt = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    model = create_mobilenet_v3_large(pretrained=False)
    model.load_state_dict(ckpt["model_state_dict"], strict=True)
    model.to(device).eval()

    vl, vy, _ = get_logits(model, "validation", device)
    tl, ty, tdf = get_logits(model, "test", device)

    T = fit_temperature(vl, vy)  # validation only
    res = {
        "checkpoint": str(CHECKPOINT.name), "n_val": int(len(vy)), "n_test": int(len(ty)),
        "fit_on": "validation only",
        "validation_before": summary(vl, vy, 1.0), "validation_after": summary(vl, vy, T),
        "test_before": summary(tl, ty, 1.0), "test_after": summary(tl, ty, T),
        "test_reliability_bins_before": reliability_bins(softmax(tl), ty),
        "test_reliability_bins_after": reliability_bins(softmax(tl, T), ty),
    }

    p = softmax(tl)
    pred, conf = p.argmax(1), p.max(1)
    srt = np.sort(p, axis=1)
    margin = srt[:, -1] - srt[:, -2]
    wrong_hi = (pred != ty) & (conf >= HIGH_CONF)
    res["test_error_analysis"] = {
        "high_confidence_threshold": HIGH_CONF,
        "high_confidence_predictions": int((conf >= HIGH_CONF).sum()),
        "high_confidence_incorrect": int(wrong_hi.sum()),
        "ambiguous_margin": AMBIGUOUS_MARGIN,
        "ambiguous_predictions": int((margin < AMBIGUOUS_MARGIN).sum()),
        "accuracy_when_conf_ge_0.8": float((pred == ty)[conf >= HIGH_CONF].mean()) if (conf >= HIGH_CONF).any() else None,
        "accuracy_when_conf_lt_0.5": float((pred == ty)[conf < 0.5].mean()) if (conf < 0.5).any() else None,
    }
    err = tdf.loc[wrong_hi, ["img_id", "diagnostic"]].copy()
    err["predicted"] = [CLASS_NAMES[i] for i in pred[wrong_hi]]
    err["confidence"] = conf[wrong_hi]
    err.to_csv(OUT / "high_confidence_errors_test.csv", index=False)
    (OUT / "calibration_results.json").write_text(json.dumps(res, indent=2))

    fig, ax = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
    for a, key, title in ((ax[0], "test_reliability_bins_before", "Test, uncalibrated"),
                          (ax[1], "test_reliability_bins_after", f"Test, temperature T={T:.2f} (fit on val)")):
        rows = [r for r in res[key] if r["count"]]
        a.plot([0, 1], [0, 1], "k--", lw=1)
        a.plot([r["mean_confidence"] for r in rows], [r["accuracy"] for r in rows], "o-", color="#0e7490")
        a.set_xlabel("Mean model score"); a.set_title(title); a.set_xlim(0, 1); a.set_ylim(0, 1)
    ax[0].set_ylabel("Observed accuracy")
    fig.tight_layout(); fig.savefig(OUT / "reliability_diagram.png", dpi=150)
    print(json.dumps({k: res[k] for k in ("test_before", "test_after", "test_error_analysis")}, indent=2))


if __name__ == "__main__":
    main()

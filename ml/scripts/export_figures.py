"""Collect training-history plots and confusion matrices into docs/figures/training/.

Run from the repo root:  python ml/scripts/export_figures.py
1. Copies existing PNGs written by the training/evaluation scripts (ml/outputs/<model>/*.png).
2. Plots train vs validation loss and validation macro F1 for every experiments/<run>/history.csv.
3. Draws confusion matrices from experiments/<run>/{val,test}_metrics.json.
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ML = Path(__file__).resolve().parents[1]
OUT = ML.parent / "docs" / "figures" / "training"
SKIP = {"calibration", "experiments", "quality_validation"}
CLASSES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]


def confusion_png(matrix, title, path):
    m = np.array(matrix)
    fig, ax = plt.subplots(figsize=(5, 4.4))
    ax.imshow(m, cmap="Blues")
    ax.set_xticks(range(len(CLASSES)), CLASSES); ax.set_yticks(range(len(CLASSES)), CLASSES)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title(title, fontsize=10)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, int(m[i, j]), ha="center", va="center", color="white" if m[i, j] > m.max() / 2 else "black", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for d in sorted((ML / "outputs").glob("*/")):
        if d.name in SKIP:
            continue
        for png in sorted(d.glob("*.png")):
            dest = OUT / f"{d.name}__{png.name}"
            shutil.copy(png, dest); made.append(dest.name)
    for run in sorted((ML / "outputs" / "experiments").glob("*/")):
        h = run / "history.csv"
        if h.exists():
            df = pd.read_csv(h)
            fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
            ax[0].plot(df["epoch"], df["train_loss"], label="train"); ax[0].plot(df["epoch"], df["val_loss"], label="validation")
            ax[0].set_title(f"{run.name}: loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
            ax[1].plot(df["epoch"], df["val_acc"], label="val accuracy"); ax[1].plot(df["epoch"], df["val_macro_f1"], label="val macro F1")
            ax[1].set_title("validation metrics"); ax[1].set_xlabel("epoch"); ax[1].legend()
            fig.tight_layout(); p = OUT / f"experiment_{run.name}__history.png"; fig.savefig(p, dpi=150); plt.close(fig); made.append(p.name)
        for split in ("val", "test"):
            f = run / f"{split}_metrics.json"
            if f.exists():
                p = OUT / f"experiment_{run.name}__{split}_confusion_matrix.png"
                confusion_png(json.loads(f.read_text())["confusion_matrix"], f"{run.name} ({split})", p); made.append(p.name)
    (OUT / "INDEX.md").write_text("# Training figures\n\n" + "\n".join(f"- {m}" for m in made) + "\n")
    print(f"{len(made)} figures in {OUT}")


if __name__ == "__main__":
    main()

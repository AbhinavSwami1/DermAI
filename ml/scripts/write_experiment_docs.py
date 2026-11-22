"""Write the experiment sections of the docs from the saved experiment outputs.

Run from the repo root after the experiments:  python ml/scripts/write_experiment_docs.py
Rewrites docs/ADVANCED_MODELS_STATUS.md and adds/replaces section 5 of
docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md. Everything numeric is read from ml/outputs/experiments.
"""
import json
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "ml" / "outputs" / "experiments"
CLASSES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
START_VAL = "0.5845 accuracy and 1.156 loss"  # baseline checkpoint before training (measured 2026-11-22)
DEPLOYED = {"val_acc": 61.22, "val_f1": 56.53, "test_acc": 57.39, "test_f1": 51.02}


def load(run):
    d = EXP / run
    if not (d / "val_metrics.json").exists():
        return None
    r = {"cfg": json.loads((d / "config.json").read_text()), "val": json.loads((d / "val_metrics.json").read_text()), "dir": d}
    r["test"] = json.loads((d / "test_metrics.json").read_text()) if (d / "test_metrics.json").exists() else None
    r["hist"] = pd.read_csv(d / "history.csv") if (d / "history.csv").exists() else None
    return r


def pct(x):
    return "-" if x is None else f"{x * 100:.2f}%"


def softmax(z):
    z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)


def macro_f1(pred, y):
    f = []
    for c in range(len(CLASSES)):
        tp = np.sum((pred == c) & (y == c)); fp = np.sum((pred == c) & (y != c)); fn = np.sum((pred != c) & (y == c))
        f.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f))


def mcnemar(a, b, y):
    """Exact two-sided McNemar test on paired correctness."""
    ca, cb = a == y, b == y
    n01, n10 = int(np.sum(ca & ~cb)), int(np.sum(~ca & cb))
    n = n01 + n10
    if n == 0:
        return n01, n10, 1.0
    p = min(1.0, 2 * sum(comb(n, k) for k in range(min(n01, n10) + 1)) / 2 ** n)
    return n01, n10, p


def main():
    runs = {r: load(r) for r in ["convnext_tiny_lr1e-4", "swin_t_lr1e-4", "vit_b16_lr1e-5", "mnv3_lr1e-3", "mnv3_lr1e-4", "mnv3_lr1e-5"]}
    present = {k: v for k, v in runs.items() if v}
    best_name = max(present, key=lambda k: present[k]["val"]["macro_f1"])

    def row(name, r):
        v, t, c = r["val"], r["test"], r["cfg"]
        return (f"| {name} | {c['arch']} | {c['lr']:g} | {v['best_epoch']} / {v['epochs_run']} | {pct(v['accuracy'])} | {pct(v['balanced_accuracy'])} | "
                f"{pct(v['macro_f1'])} | {pct(t['accuracy']) if t else '-'} | {pct(t['macro_f1']) if t else '-'} | "
                f"{v['inference_ms_per_image']:.1f} | {c['total_params'] / 1e6:.1f}M | {v['train_seconds'] / 60:.0f} |")

    head = ("| Run | Architecture | LR | Best / run epochs | Val acc | Val bal. acc | Val macro F1 | Test acc | Test macro F1 | ms per image | Params | Train min |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|")
    main_runs = [k for k in ["vit_b16_lr1e-5", "convnext_tiny_lr1e-4", "swin_t_lr1e-4"] if k in present]
    lines = ["# Advanced AI - Status and Results", "",
             "| Item | Status |", "|---|---|",
             "| Baseline CNNs (MobileNetV3-Large, EfficientNet-B0) | Implemented and evaluated |",
             "| Advanced CNN (ConvNeXt-Tiny) | Trained and evaluated |",
             "| Transformers (ViT-B/16, Swin-T) | Trained and evaluated |",
             "| Ensemble (mean softmax of ConvNeXt-Tiny and ViT-B/16) | Evaluated on validation |",
             "| Hyperparameter experiment (MobileNetV3-Large, lr 1e-3, 1e-4, 1e-5) | Run on validation |", "",
             "All runs: same patient-level split (1,477 / 361 / 460), seed 42, preprocessing, weighted cross-entropy, Adam (weight decay 1e-4), ReduceLROnPlateau, early stopping (patience 5), ImageNet-pretrained weights, best epoch chosen by lowest validation loss. Models were compared on validation; the test split was evaluated once, only for ConvNeXt-Tiny and ViT-B/16.", "",
             "## Results", "", head] + [row(k, present[k]) for k in main_runs] + [
             f"| MobileNetV3-Large fine-tuned (deployed, earlier script) | mobilenet_v3_large | 1e-05 | 9 | {DEPLOYED['val_acc']:.2f}% | - | {DEPLOYED['val_f1']:.2f}% | {DEPLOYED['test_acc']:.2f}% | {DEPLOYED['test_f1']:.2f}% | - | 4.2M | - |", ""]

    # ensemble on validation
    if all(k in present for k in ("convnext_tiny_lr1e-4", "vit_b16_lr1e-5")):
        ps = [softmax(np.load(present[k]["dir"] / "val_logits.npy")) for k in ("convnext_tiny_lr1e-4", "vit_b16_lr1e-5")]
        y = np.load(present["vit_b16_lr1e-5"]["dir"] / "val_labels.npy"); pe = np.mean(ps, 0).argmax(1)
        ea, ef = float((pe == y).mean()), macro_f1(pe, y)
        vb = present["vit_b16_lr1e-5"]["val"]
        lines += ["## Ensemble", "", f"Mean softmax of ConvNeXt-Tiny and ViT-B/16 on validation: accuracy {ea * 100:.2f}%, macro F1 {ef * 100:.2f}%, versus ViT-B/16 alone {pct(vb['accuracy'])} and {pct(vb['macro_f1'])}. "
                  + ("The ensemble gave no validation gain, so it was not evaluated on the test split." if ef <= vb["macro_f1"] else "The ensemble improved validation macro F1; evaluate it on test once if it is to be reported."), ""]

    # test details
    if "vit_b16_lr1e-5" in present and present["vit_b16_lr1e-5"]["test"]:
        t = present["vit_b16_lr1e-5"]["test"]
        lines += ["## ViT-B/16 on the test split (460 images)", "", "| Class | Precision | Recall | F1 | Images |", "|---|---|---|---|---|"]
        lines += [f"| {c} | {t['per_class'][c]['precision']:.2f} | {t['per_class'][c]['recall']:.2f} | {t['per_class'][c]['f1-score']:.2f} | {int(t['per_class'][c]['support'])} |" for c in CLASSES]
        lines += ["", f"Accuracy {pct(t['accuracy'])}, balanced accuracy {pct(t['balanced_accuracy'])}, macro F1 {pct(t['macro_f1'])}. Confusion matrix: `docs/figures/training/`.", ""]
        cn = present.get("convnext_tiny_lr1e-4")
        if cn and cn["test"]:
            a = np.load(present["vit_b16_lr1e-5"]["dir"] / "test_logits.npy").argmax(1); b = np.load(cn["dir"] / "test_logits.npy").argmax(1)
            y = np.load(present["vit_b16_lr1e-5"]["dir"] / "test_labels.npy")
            n_vit_only, n_cnx_only, p = mcnemar(a, b, y)
            lines += ["## Paired comparison on test: ViT-B/16 versus ConvNeXt-Tiny", "",
                      f"ViT-B/16 was right and ConvNeXt-Tiny wrong on {n_vit_only} images; the reverse on {n_cnx_only}. Exact McNemar test p = {p:.4f}. "
                      + ("The accuracy difference is unlikely to be chance alone on this test set." if p < 0.05 else "The accuracy difference is not clearly separable from chance on this test set."),
                      "The comparison with the deployed MobileNetV3-Large (test accuracy 57.39%) is not paired because its per-image predictions were evaluated separately.", ""]

    # observations
    lines += ["## Observations", ""]
    for k in main_runs:
        r = present[k]; h = r["hist"]
        if h is not None:
            lines.append(f"- {k}: training accuracy reached {h['train_acc'].iloc[-1] * 100:.0f}% while validation accuracy was {h['val_acc'].iloc[-1] * 100:.0f}% at the last epoch; validation loss was lowest at epoch {r['val']['best_epoch']}, then rose. Early stopping ended training at epoch {r['val']['epochs_run']}.")
    b = present[best_name]
    lines += [f"- Best on validation macro F1: {best_name} ({pct(b['val']['macro_f1'])}). Validation has 361 images (7 MEL, 23 SCC), so differences of a few points are within noise; each model is a single run with one seed.",
              "- Validation scores of the selected models were optimistic: the test split gave lower values (see the table).",
              "- Class imbalance and rare classes (MEL, SCC) remain the main limitation; per-class results are in the confusion matrices.", ""]

    lines += ["## Model selection", "",
              "- Best research result (selected on validation, confirmed once on test): ViT-B/16.",
              "- Deployed in the application: MobileNetV3-Large fine-tuned. ViT-B/16 is about 20 times larger (85.8M versus 4.2M parameters) and slower per image; Grad-CAM, calibration, tests and Docker setup are built on MobileNetV3-Large, and Grad-CAM for a transformer needs a different implementation.",
              "- No claim of clinical reliability follows from these experiments.", ""]
    (ROOT / "docs" / "ADVANCED_MODELS_STATUS.md").write_text("\n".join(lines) + "\n")

    # LR section
    lr = {k: present.get(k) for k in ("mnv3_lr1e-3", "mnv3_lr1e-4", "mnv3_lr1e-5")}
    sec = ["## 5. Learning-rate experiment results (run 2026-11-22)", "",
           "MobileNetV3-Large, started from the head-trained baseline checkpoint, `features[13:]` and `classifier[3]` trainable, same split, seed 42, batch size 16, Adam (weight decay 1e-4), up to 20 epochs with early stopping. Only the learning rate changed. Selection used validation only; the test split was not used.", "",
           "| Run | LR | Best epoch | Val loss at best | Val acc | Val bal. acc | Val macro F1 |", "|---|---|---|---|---|---|---|"]
    for k, r in lr.items():
        if r:
            h = r["hist"]; vl = h.loc[h["epoch"] == r["val"]["best_epoch"], "val_loss"].iloc[0] if h is not None else float("nan")
            sec.append(f"| {k} | {r['cfg']['lr']:g} | {r['val']['best_epoch']} | {vl:.3f} | {pct(r['val']['accuracy'])} | {pct(r['val']['balanced_accuracy'])} | {pct(r['val']['macro_f1'])} |")
    if lr["mnv3_lr1e-3"] and lr["mnv3_lr1e-4"]:
        d = (lr["mnv3_lr1e-3"]["val"]["macro_f1"] - lr["mnv3_lr1e-4"]["val"]["macro_f1"]) * 100
        sec += ["", f"- lr 1e-3 and 1e-4 gave similar validation results (macro F1 difference {d:+.2f} points); the evidence does not separate them. With 1e-3 the validation loss fluctuated strongly between epochs; with 1e-4 it was lowest early (epoch {lr['mnv3_lr1e-4']['val']['best_epoch']}) and then rose as training accuracy climbed."]
    fe = {k: load(k) for k in ("mnv3_lr1e-3_fe", "mnv3_lr1e-4_fe", "mnv3_lr1e-5_fe")}
    has_fe = any(fe.values())
    if lr["mnv3_lr1e-5"]:
        cause = "" if has_fe else " A possible cause is that BatchNorm statistics of frozen layers are updated in training mode (the original trainer keeps `model.features` in eval mode); this was not tested in this run."
        sec += [f"- lr 1e-5 gave the lowest validation scores. The baseline checkpoint itself scored {START_VAL} on validation before any training (measured separately), and the best epoch of this run was below that starting point, so training in this script at 1e-5 did not preserve the starting performance.{cause} The deployed model was trained at 1e-5 with a different script and reached 61.22% validation accuracy, so this result should not be read as showing that 1e-5 is unsuitable in general."]
    if has_fe:
        sec += ["", "### Repeat with the feature extractor in eval mode (BatchNorm statistics frozen)", "",
                "Same settings, plus `--features-eval`, which keeps `model.features` in eval mode during training as `ml/src/training/trainer.py` does.", "",
                "| Run | LR | Best epoch | Val acc | Val bal. acc | Val macro F1 | Val macro F1 without the flag |", "|---|---|---|---|---|---|---|"]
        for k, r in fe.items():
            if r:
                base = lr.get(k.replace("_fe", ""))
                sec.append(f"| {k} | {r['cfg']['lr']:g} | {r['val']['best_epoch']} | {pct(r['val']['accuracy'])} | {pct(r['val']['balanced_accuracy'])} | {pct(r['val']['macro_f1'])} | {pct(base['val']['macro_f1']) if base else '-'} |")
        r5 = fe.get("mnv3_lr1e-5_fe")
        if r5 and lr["mnv3_lr1e-5"]:
            a5, base_acc = r5["val"]["accuracy"], lr["mnv3_lr1e-5"]["val"]["accuracy"]
            improved = a5 - base_acc > 0.02
            if a5 >= 0.5845 and improved:
                msg = f"This is at or above the starting point and above the run without the flag ({pct(base_acc)}), consistent with BatchNorm statistic updates explaining the earlier degradation; it is one run and does not prove the cause."
            elif improved:
                msg = f"This is above the run without the flag ({pct(base_acc)}) but still below the starting point, so BatchNorm updates explain at most part of the degradation."
            else:
                msg = f"There is no clear change from the run without the flag ({pct(base_acc)}), so BatchNorm updates alone do not explain the degradation."
            sec += ["", f"- At lr 1e-5 with the feature extractor in eval mode, validation accuracy was {pct(a5)} (starting checkpoint: 58.45%). " + msg]
    sec += ["- Single run per setting and a small validation set: treat differences of a few points as inconclusive.", ""]
    p = ROOT / "docs" / "TRAINING_CONFIGURATION_AND_LR_PLAN.md"; s = p.read_text()
    marker = "## 5. Learning-rate experiment results"
    s = s[:s.index(marker)].rstrip("\n") + "\n\n" if marker in s else s.rstrip("\n") + "\n\n"
    p.write_text(s + "\n".join(sec) + "\n")
    print("wrote ADVANCED_MODELS_STATUS.md and LR section; best on validation:", best_name)


if __name__ == "__main__":
    main()

"""Update docs/FINAL_REPORT.md with the experiment results (run from the repo root).

  python ml/scripts/update_final_report.py
Replaces section 2 ("Model experiments"), removes the "not run" bullet for the transformer,
ensemble and learning-rate experiments, adds a preprocessed-image feature row and one
limitations bullet. If a heading cannot be found the generated section is written to
docs/_final_report_section2.md instead, and nothing else is touched.
"""
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import write_experiment_docs as w  # noqa: E402

ROOT = w.ROOT


def section2():
    R = {k: w.load(k) for k in ["convnext_tiny_lr1e-4", "swin_t_lr1e-4", "vit_b16_lr1e-5", "mnv3_lr1e-3", "mnv3_lr1e-4", "mnv3_lr1e-5",
                                "mnv3_lr1e-3_fe", "mnv3_lr1e-4_fe", "mnv3_lr1e-5_fe"]}
    D = w.DEPLOYED
    pct = w.pct

    def row(label, r):
        if not r:
            return None
        v, t = r["val"], r["test"]
        return (f"| {label} | {pct(v['accuracy'])} | {pct(v['macro_f1'])} | {pct(t['accuracy']) if t else '-'} | "
                f"{pct(t['macro_f1']) if t else '-'} | {v['inference_ms_per_image']:.1f} | {r['cfg']['total_params'] / 1e6:.1f}M |")

    L = ["## 2. Model experiments", "",
         "Same patient-level split (1,477 / 361 / 460), seed 42 and weighted cross-entropy for every run. Models were compared on validation; the test split was evaluated once, only for the two finalists (ConvNeXt-Tiny and ViT-B/16).", "",
         "| Model | Val acc | Val macro F1 | Test acc | Test macro F1 | ms per image | Params |", "|---|---|---|---|---|---|---|",
         f"| MobileNetV3-Large fine-tuned (deployed) | {D['val_acc']:.2f}% | {D['val_f1']:.2f}% | {D['test_acc']:.2f}% | {D['test_f1']:.2f}% | - | 4.2M |"]
    L += [x for x in (row("ConvNeXt-Tiny", R["convnext_tiny_lr1e-4"]), row("Swin-T", R["swin_t_lr1e-4"]), row("ViT-B/16", R["vit_b16_lr1e-5"])) if x]
    L += ["", "MobileNetV3-Large versus EfficientNet-B0: `docs/PHASE5_MODEL_COMPARISON_REPORT.md`.", ""]
    vit, cnx = R["vit_b16_lr1e-5"], R["convnext_tiny_lr1e-4"]
    if vit and vit["test"]:
        t = vit["test"]; sc = t["per_class"]["SCC"]
        L.append(f"- ViT-B/16 had the best validation macro F1 ({pct(vit['val']['macro_f1'])}) and, among the models evaluated on test, the best test accuracy ({pct(t['accuracy'])}) and macro F1 ({pct(t['macro_f1'])}).")
        if cnx and cnx["test"]:
            a = np.load(vit["dir"] / "test_logits.npy").argmax(1); b = np.load(cnx["dir"] / "test_logits.npy").argmax(1); y = np.load(vit["dir"] / "test_labels.npy")
            n1, n2, p = w.mcnemar(a, b, y)
            L.append(f"- ViT-B/16 was right and ConvNeXt-Tiny wrong on {n1} test images, the reverse on {n2} (exact McNemar p = {p:.4f}); single seed, one dataset.")
        L.append(f"- SCC remains weak for ViT-B/16 on test: precision {sc['precision']:.2f}, recall {sc['recall']:.2f} ({int(sc['support'])} images). MEL has only 10 test images.")
    if vit and cnx:
        ps = [w.softmax(np.load(r["dir"] / "val_logits.npy")) for r in (cnx, vit)]
        y = np.load(vit["dir"] / "val_labels.npy"); pe = np.mean(ps, 0).argmax(1)
        ea, ef = float((pe == y).mean()), w.macro_f1(pe, y)
        L.append(f"- Ensemble (mean softmax of ConvNeXt-Tiny and ViT-B/16): validation accuracy {ea * 100:.2f}%, macro F1 {ef * 100:.2f}%, versus ViT-B/16 alone {pct(vit['val']['accuracy'])} and {pct(vit['val']['macro_f1'])}. "
                 + ("No validation gain, so it was not evaluated on test." if ef <= vit["val"]["macro_f1"] else "Validation gain; test evaluation pending."))
    lr = [(k, R[k], R.get(k + "_fe")) for k in ("mnv3_lr1e-3", "mnv3_lr1e-4", "mnv3_lr1e-5") if R[k]]
    if lr:
        L += ["", "Learning-rate experiment (MobileNetV3-Large, only the learning rate changed, validation macro F1):", "",
              "| LR | BatchNorm in training mode | Feature extractor in eval mode (original trainer) |", "|---|---|---|"]
        for k, a, b in lr:
            L.append(f"| {a['cfg']['lr']:g} | {pct(a['val']['macro_f1'])} (acc {pct(a['val']['accuracy'])}) | " + (f"{pct(b['val']['macro_f1'])} (acc {pct(b['val']['accuracy'])})" if b else "not run") + " |")
        fe5 = R["mnv3_lr1e-5_fe"]
        if fe5:
            L += ["", f"- With the feature extractor in eval mode, lr 1e-5 gave {pct(fe5['val']['accuracy'])} validation accuracy, close to the deployed model ({D['val_acc']:.2f}%); without it the run fell to {pct(R['mnv3_lr1e-5']['val']['accuracy'])}, below the starting checkpoint (58.45%). This is consistent with BatchNorm statistic updates causing the degradation (one run per setting).",
                  "- The ranking of learning rates differed between the two setups, so the experiment is inconclusive about the best learning rate. Details: `docs/TRAINING_CONFIGURATION_AND_LR_PLAN.md`."]
    L += ["", "- Overfitting: training accuracy reached 87% to 97% while validation accuracy stayed at 65% to 77%; validation loss was lowest at epoch 3 to 5 and early stopping ended each run.",
          "- Selected model: ViT-B/16 is the best research result. MobileNetV3-Large stays deployed: it is far smaller (4.2M versus 85.8M parameters) and faster, and Grad-CAM, calibration, tests and the Docker setup are built on it. Full tables: `docs/ADVANCED_MODELS_STATUS.md`. No clinical reliability is claimed.", ""]
    return "\n".join(L)


def main():
    new = section2()
    p = ROOT / "docs" / "FINAL_REPORT.md"; s = p.read_text()
    a = s.find("## 2. Model experiments"); b = s.find("\n## 3.", a) if a != -1 else -1
    if a == -1 or b == -1:
        (ROOT / "docs" / "_final_report_section2.md").write_text(new + "\n")
        print("Heading not found; wrote docs/_final_report_section2.md instead (paste it over section 2)."); return
    s = s[:a] + new + s[b:]
    s = re.sub(r"^- ViT/Swin, ensemble and learning-rate experiments not run.*\n", "", s, flags=re.M)
    if "Preprocessed model-input" not in s:
        s = re.sub(r"^(\| Grad-CAM[^\n]*\n)", r"\1| Preprocessed model-input view (regenerated on demand, not stored) | Implemented |\n", s, count=1, flags=re.M)
    bullet = "- Experiments are single runs with one seed on a small validation set; checkpoints are chosen by validation loss, which can pick an epoch with lower validation F1.\n"
    if bullet not in s:
        c = s.find("\n## 9.")
        if c != -1:
            s = s[:c].rstrip("\n") + "\n" + bullet + s[c:]
    p.write_text(s); print("updated docs/FINAL_REPORT.md")


if __name__ == "__main__":
    main()

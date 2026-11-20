"""Validate the DermAI image-quality thresholds.

1. Synthetic-degradation validation: known ground truth. Each sampled test image is
   blurred / darkened / brightened; we measure detection of the degraded copies and
   false flags on the untouched originals, and sweep the blur threshold.
2. Optional manual reference labels (--reference-csv): agreement between the system and
   a human rater. Create a template with --make-template, then label it good/acceptable/poor.

Run from repo root:  python ml/scripts/evaluate_image_quality.py
These are proxies; synthetic degradation is not a substitute for expert labels.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services import image_quality_service as qs  # noqa: E402

ML = ROOT / "ml"
OUT = ML / "outputs" / "quality_validation"
THRESHOLDS = [20, 30, 40, 50, 60, 75, 100, 125, 150]


def encode(img_bgr):
    return cv2.imencode(".png", img_bgr)[1].tobytes()


def degrade(img):
    f = img.astype(np.float32)
    return {
        "blur_sigma1.5": cv2.GaussianBlur(img, (0, 0), 1.5),
        "blur_sigma3.0": cv2.GaussianBlur(img, (0, 0), 3.0),
        "dark_x0.25": np.clip(f * 0.25, 0, 255).astype(np.uint8),
        "bright": np.clip(255 - (255 - f) * 0.25, 0, 255).astype(np.uint8),
    }


EXPECTED = {"blur_sigma1.5": "POSSIBLY_BLURRY", "blur_sigma3.0": "POSSIBLY_BLURRY",
            "dark_x0.25": "LOW_BRIGHTNESS", "bright": "HIGH_BRIGHTNESS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", default=str(ML / "datasets" / "processed" / "pad_ufes_20"))
    ap.add_argument("--split-csv", default=str(ML / "datasets" / "splits" / "fold_1_train_val_test" / "test.csv"))
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reference-csv", default=None)
    ap.add_argument("--make-template", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    ids = pd.read_csv(args.split_csv)["img_id"].tolist()
    rng = np.random.default_rng(args.seed)
    sample = [ids[i] for i in rng.permutation(len(ids))[: args.n]]

    if args.make_template:
        pd.DataFrame({"img_id": sample[:30], "reference": ""}).to_csv(OUT / "reference_template.csv", index=False)
        print("Wrote", OUT / "reference_template.csv", "- fill 'reference' with good / acceptable / poor after viewing each image")
        return

    rows, orig_scores, deg_scores = [], [], {k: [] for k in EXPECTED}
    for img_id in sample:
        img = cv2.imread(str(Path(args.images_dir) / str(img_id)))
        if img is None:
            continue
        r = qs.assess_image_quality(encode(img))
        orig_scores.append(r["blur_score"])
        rows.append({"img_id": img_id, "condition": "original", "status": r["quality_status"],
                     "flag_list": ";".join(r["quality_flags"]), "blur": r["blur_score"], "brightness": r["brightness_mean"],
                     "w": r["width"], "h": r["height"]})
        for cond, d in degrade(img).items():
            rd = qs.assess_image_quality(encode(d))
            deg_scores[cond].append(rd["blur_score"])
            rows.append({"img_id": img_id, "condition": cond, "status": rd["quality_status"],
                         "flag_list": ";".join(rd["quality_flags"]), "blur": rd["blur_score"], "brightness": rd["brightness_mean"],
                         "w": rd["width"], "h": rd["height"]})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "quality_validation_rows.csv", index=False)

    n_orig = int((df.condition == "original").sum())
    o = df[df.condition == "original"]
    summary = {"images": n_orig, "current_min_blur_score": qs.MIN_BLUR_SCORE,
               "original_flagged_pct": float((o.status != "ACCEPTABLE").mean() * 100),
               "original_blur_flag_pct": float(o["flag_list"].str.contains("POSSIBLY_BLURRY").mean() * 100),
               "original_blur_percentiles": {p: float(np.percentile(orig_scores, p)) for p in (5, 25, 50, 75, 95)},
               "image_size_values": sorted({f"{w}x{h}" for w, h in zip(o.w, o.h)})[:5],
               "detection_pct_expected_flag": {}, "threshold_sweep": []}
    for cond, flag in EXPECTED.items():
        c = df[df.condition == cond]
        summary["detection_pct_expected_flag"][cond] = float(c["flag_list"].str.contains(flag).mean() * 100)
    for t in THRESHOLDS:
        summary["threshold_sweep"].append({
            "min_blur_score": t,
            "original_rejected_pct": float(np.mean(np.array(orig_scores) < t) * 100),
            "blur_sigma1.5_detected_pct": float(np.mean(np.array(deg_scores["blur_sigma1.5"]) < t) * 100),
            "blur_sigma3.0_detected_pct": float(np.mean(np.array(deg_scores["blur_sigma3.0"]) < t) * 100)})

    if args.reference_csv:
        ref = pd.read_csv(args.reference_csv).dropna(subset=["reference"])
        ref = ref[ref.reference.isin(["good", "acceptable", "poor"])]
        sysr = {}
        for img_id in ref.img_id:
            img = cv2.imread(str(Path(args.images_dir) / str(img_id)))
            if img is not None:
                sysr[img_id] = qs.assess_image_quality(encode(img))["quality_status"]
        ref = ref[ref.img_id.isin(sysr)].copy()
        ref["system"] = ref.img_id.map(sysr)
        ref["ref_review"] = ref.reference == "poor"
        ref["sys_review"] = ref.system != "ACCEPTABLE"
        tp = int((ref.ref_review & ref.sys_review).sum()); fn = int((ref.ref_review & ~ref.sys_review).sum())
        fp = int((~ref.ref_review & ref.sys_review).sum()); tn = int((~ref.ref_review & ~ref.sys_review).sum())
        summary["reference_comparison"] = {"n": len(ref), "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "sensitivity_poor": tp / (tp + fn) if tp + fn else None, "specificity": tn / (tn + fp) if tn + fp else None,
            "agreement": (tp + tn) / len(ref) if len(ref) else None}

    (OUT / "quality_validation_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

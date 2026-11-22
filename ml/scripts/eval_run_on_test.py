"""Evaluate one finished experiment on the TEST split, once.

  python ml/scripts/eval_run_on_test.py --run-id swin_t_lr1e-4
Use only after the run has been selected on validation results. Refuses to run twice.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_advanced as ta  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    run_id = ap.parse_args().run_id
    out = ta.ML_ROOT / "outputs" / "experiments" / run_id
    if (out / "test_metrics.json").exists():
        sys.exit("Test metrics already exist for this run; the test split is evaluated once.")
    ck = torch.load(ta.ML_ROOT / "checkpoints" / "experiments" / f"{run_id}.pth", map_location="cpu", weights_only=True)
    ns = argparse.Namespace(arch=ck["arch"], no_pretrained=True, init_checkpoint=None, trainable="all",
                            unfreeze_from=ck["config"].get("unfreeze_from", 13))
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    model = ta.build_model(ns)
    model.load_state_dict(ck["model_state_dict"]); model.to(device)
    df = ta.load_split("test")
    logits, labels, _ = ta.run_eval(model, DataLoader(ta.DermAIDataset(df, ta.eval_transform), batch_size=16), device)
    (out / "test_metrics.json").write_text(json.dumps({"run_id": run_id, **ta.metrics(logits, labels)}, indent=2))
    np.save(out / "test_logits.npy", logits); np.save(out / "test_labels.npy", labels)
    m = ta.metrics(logits, labels)
    print(run_id, "test acc", round(m["accuracy"], 4), "macro F1", round(m["macro_f1"], 4))


if __name__ == "__main__":
    main()

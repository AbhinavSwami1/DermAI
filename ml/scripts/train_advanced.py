"""Controlled training experiments for DermAI (advanced CNNs, Transformers, LR runs).

Same split, seed, preprocessing and weighted loss for every run; only the flags change.
Selection uses VALIDATION data. The test split is touched only with --eval-test.

Examples (repo root):
  python ml/scripts/train_advanced.py --arch convnext_tiny --lr 1e-4 --trainable all --run-id convnext_tiny_lr1e-4
  python ml/scripts/train_advanced.py --arch vit_b_16 --lr 1e-5 --trainable all --run-id vit_b16_lr1e-5
  python ml/scripts/train_advanced.py --arch mobilenet_v3_large --lr 1e-3 --trainable unfreeze_from --unfreeze-from 13 \
      --init-checkpoint ml/checkpoints/mobilenet/best_mobilenet_v3_large.pth --run-id mnv3_lr1e-3
  Smoke test: add --no-pretrained --max-batches 2 --epochs 1 --run-id smoke
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torchvision.models as tvm
from sklearn.metrics import (balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from torch.utils.data import DataLoader

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT / "src"))
from data.augmentations import eval_transform, train_transform  # noqa: E402
from data.dataset import DermAIDataset  # noqa: E402

SPLIT_DIR = ML_ROOT / "datasets" / "splits" / "fold_1_train_val_test"
IMAGE_DIR = ML_ROOT / "datasets" / "processed" / "pad_ufes_20"
CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
HEADS = {
    "mobilenet_v3_large": "classifier.3", "efficientnet_b0": "classifier.1",
    "resnet50": "fc", "densenet121": "classifier",
    "convnext_tiny": "classifier.2", "swin_t": "head", "vit_b_16": "heads.head",
}


def load_split(name):
    df = pd.read_csv(SPLIT_DIR / f"{name}.csv")
    df["image_path"] = df["img_id"].apply(lambda i: str(IMAGE_DIR / str(i)))
    df["label"] = df["diagnostic"].map({n: i for i, n in enumerate(CLASS_NAMES)}).astype(int)
    return df


def replace_head(model, path, n):
    *parents, last = path.split(".")
    parent = model
    for p in parents:
        parent = parent[int(p)] if p.isdigit() else getattr(parent, p)
    old = parent[int(last)] if last.isdigit() else getattr(parent, last)
    new = nn.Linear(old.in_features, n)
    if last.isdigit():
        parent[int(last)] = new
    else:
        setattr(parent, last, new)


def build_model(args):
    model = tvm.get_model(args.arch, weights=None if args.no_pretrained else "DEFAULT")
    replace_head(model, HEADS[args.arch], len(CLASS_NAMES))
    if args.init_checkpoint:
        ck = torch.load(args.init_checkpoint, map_location="cpu", weights_only=True)
        model.load_state_dict(ck["model_state_dict"], strict=True)
    head = HEADS[args.arch] + "."
    for name, p in model.named_parameters():
        p.requires_grad = args.trainable == "all" or name.startswith(head)
    if args.trainable == "unfreeze_from":
        assert args.arch == "mobilenet_v3_large", "--unfreeze-from is implemented for mobilenet_v3_large"
        for block in model.features[args.unfreeze_from:]:
            for p in block.parameters():
                p.requires_grad = True
    return model


@torch.no_grad()
def run_eval(model, loader, device, criterion=None, max_batches=None):
    model.eval()
    logits, labels, loss_sum, n = [], [], 0.0, 0
    for i, (x, y) in enumerate(loader):
        if max_batches and i >= max_batches:
            break
        out = model(x.to(device))
        if criterion is not None:
            loss_sum += criterion(out, y.to(device)).item() * len(y)
        n += len(y)
        logits.append(out.cpu().numpy()); labels.append(y.numpy())
    return np.concatenate(logits), np.concatenate(labels), (loss_sum / max(n, 1))


def metrics(logits, labels):
    pred = logits.argmax(1)
    return {
        "n": int(len(labels)),
        "accuracy": float((pred == labels).mean()),
        "balanced_accuracy": float(balanced_accuracy_score(labels, pred)),
        "macro_f1": float(f1_score(labels, pred, average="macro", zero_division=0)),
        "per_class": classification_report(labels, pred, labels=list(range(len(CLASS_NAMES))),
                                           target_names=CLASS_NAMES, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(labels, pred, labels=list(range(len(CLASS_NAMES)))).tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True, choices=list(HEADS))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--lr", type=float, required=True)
    ap.add_argument("--trainable", choices=["head", "all", "unfreeze_from"], default="all")
    ap.add_argument("--unfreeze-from", type=int, default=13)
    ap.add_argument("--init-checkpoint", default=None)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-pretrained", action="store_true")
    ap.add_argument("--max-batches", type=int, default=None, help="smoke tests only")
    ap.add_argument("--eval-test", action="store_true", help="evaluate the selected best checkpoint on test (once)")
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    out_dir = ML_ROOT / "outputs" / "experiments" / args.run_id
    ck_path = ML_ROOT / "checkpoints" / "experiments" / f"{args.run_id}.pth"
    if ck_path.exists():
        sys.exit(f"Refusing to overwrite existing checkpoint: {ck_path}")
    out_dir.mkdir(parents=True, exist_ok=True); ck_path.parent.mkdir(parents=True, exist_ok=True)

    train_df, val_df = load_split("train"), load_split("validation")
    counts = train_df["label"].value_counts().reindex(range(len(CLASS_NAMES))).fillna(1).to_numpy()
    weights = torch.tensor(len(train_df) / (len(CLASS_NAMES) * counts), dtype=torch.float32).to(device)  # train split only
    criterion = nn.CrossEntropyLoss(weight=weights)

    train_loader = DataLoader(DermAIDataset(train_df, train_transform), batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(DermAIDataset(val_df, eval_transform), batch_size=args.batch_size, shuffle=False)

    model = build_model(args).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    n_train = sum(p.numel() for p in params); n_all = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.Adam(params, lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    config = {**vars(args), "device": str(device), "trainable_params": n_train, "total_params": n_all,
              "optimizer": "Adam", "scheduler": "ReduceLROnPlateau(factor=0.5, patience=2)",
              "loss": "weighted CrossEntropy (weights from train split)", "split": str(SPLIT_DIR.name),
              "selection_criterion": "lowest validation loss", "class_names": CLASS_NAMES}
    (out_dir / "config.json").write_text(json.dumps(config, indent=2))

    best, best_epoch, bad, history, t0 = float("inf"), 0, 0, [], time.time()
    for epoch in range(1, args.epochs + 1):
        model.train(); tl, tn, tc = 0.0, 0, 0
        for i, (x, y) in enumerate(train_loader):
            if args.max_batches and i >= args.max_batches:
                break
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x); loss = criterion(out, y); loss.backward(); optimizer.step()
            tl += loss.item() * len(y); tn += len(y); tc += (out.argmax(1) == y).sum().item()
        vl, vy, vloss = run_eval(model, val_loader, device, criterion, args.max_batches)
        vm = metrics(vl, vy)
        scheduler.step(vloss)
        row = {"epoch": epoch, "train_loss": tl / max(tn, 1), "train_acc": tc / max(tn, 1), "val_loss": vloss,
               "val_acc": vm["accuracy"], "val_macro_f1": vm["macro_f1"], "lr": optimizer.param_groups[0]["lr"]}
        history.append(row); pd.DataFrame(history).to_csv(out_dir / "history.csv", index=False)
        print(row)
        if vloss < best:
            best, best_epoch, bad = vloss, epoch, 0
            torch.save({"model_state_dict": model.state_dict(), "arch": args.arch, "class_names": CLASS_NAMES,
                        "epoch": epoch, "config": config}, ck_path)
        else:
            bad += 1
            if bad >= args.patience:
                print("Early stopping"); break

    # final evaluation of the BEST checkpoint
    ck = torch.load(ck_path, map_location="cpu", weights_only=True)
    model.load_state_dict(ck["model_state_dict"]); model.to(device)
    vl, vy, _ = run_eval(model, val_loader, device, None, args.max_batches)
    res = {"run_id": args.run_id, "best_epoch": best_epoch, "epochs_run": len(history),
           "train_seconds": time.time() - t0, **metrics(vl, vy)}
    sample, _ = next(iter(DataLoader(DermAIDataset(val_df, eval_transform), batch_size=1)))
    with torch.no_grad():
        model(sample.to(device)); t1 = time.time()
        for _ in range(20):
            model(sample.to(device))
    res["inference_ms_per_image"] = (time.time() - t1) / 20 * 1000
    (out_dir / "val_metrics.json").write_text(json.dumps(res, indent=2))
    np.save(out_dir / "val_logits.npy", vl); np.save(out_dir / "val_labels.npy", vy)

    if args.eval_test:
        test_df = load_split("test")
        tl_, ty, _ = run_eval(model, DataLoader(DermAIDataset(test_df, eval_transform), batch_size=args.batch_size), device, None, args.max_batches)
        (out_dir / "test_metrics.json").write_text(json.dumps({"run_id": args.run_id, **metrics(tl_, ty)}, indent=2))
        np.save(out_dir / "test_logits.npy", tl_); np.save(out_dir / "test_labels.npy", ty)
    print("Done. Best epoch:", best_epoch, "val macro F1:", round(res["macro_f1"], 4))


if __name__ == "__main__":
    main()

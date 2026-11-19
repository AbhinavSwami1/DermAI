"""Confidence calibration utilities (numpy only, unit-testable)."""
import numpy as np


def softmax(logits, T=1.0):
    z = np.asarray(logits, dtype=np.float64) / T
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def nll(probs, labels):
    p = np.clip(probs[np.arange(len(labels)), labels], 1e-12, 1.0)
    return float(-np.log(p).mean())


def brier(probs, labels):
    onehot = np.eye(probs.shape[1])[labels]
    return float(((probs - onehot) ** 2).sum(axis=1).mean())


def reliability_bins(probs, labels, n_bins=10):
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == labels).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        n = int(m.sum())
        rows.append({
            "bin_low": float(lo), "bin_high": float(hi), "count": n,
            "mean_confidence": float(conf[m].mean()) if n else None,
            "accuracy": float(correct[m].mean()) if n else None,
        })
    return rows


def ece(probs, labels, n_bins=10):
    total = len(labels)
    return float(sum(
        r["count"] / total * abs(r["accuracy"] - r["mean_confidence"])
        for r in reliability_bins(probs, labels, n_bins) if r["count"]
    ))


def fit_temperature(val_logits, val_labels, lo=0.05, hi=10.0, iters=60):
    """Golden-section search for T minimising validation NLL (validation data only)."""
    g = (5 ** 0.5 - 1) / 2
    a, b = lo, hi
    f = lambda T: nll(softmax(val_logits, T), val_labels)
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a); fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a); fd = f(d)
    return float((a + b) / 2)

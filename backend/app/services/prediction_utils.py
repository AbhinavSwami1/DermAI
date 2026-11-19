"""Helpers derived strictly from stored model scores."""


def top_n_predictions(class_scores: dict | None, n: int = 3) -> list[dict]:
    """Return the top-n classes by model score (descending).

    Values are raw model softmax scores, not clinically validated
    probabilities.
    """
    if not class_scores:
        return []
    ranked = sorted(class_scores.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {"rank": i + 1, "class_name": name, "score": round(float(score), 4)}
        for i, (name, score) in enumerate(ranked[: max(1, n)])
    ]

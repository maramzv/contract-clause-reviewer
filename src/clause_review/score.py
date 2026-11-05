"""CUAD-style scoring. A prediction matches a gold span when char-level overlap / union >= threshold (document it!)."""


def overlap(a, b):
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def score(gold, pred, threshold=0.5):
    """gold/pred: {category: [(start, end), ...]} for one or more docs (keys may be (doc, category))."""
    out = {}
    for cat in set(gold) | set(pred):
        g, p = list(gold.get(cat, [])), list(pred.get(cat, []))
        matched, tp = set(), 0
        for ps in p:
            hit = next((i for i, gs in enumerate(g) if i not in matched and overlap(ps, gs) >= threshold), None)
            if hit is not None:
                matched.add(hit)
                tp += 1
        prec = tp / len(p) if p else 0.0
        rec = tp / len(g) if g else 0.0
        out[cat] = {"precision": prec, "recall": rec, "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
                    "tp": tp, "n_pred": len(p), "n_gold": len(g)}
    return out

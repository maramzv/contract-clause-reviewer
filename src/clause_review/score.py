"""CUAD-style scoring on character spans.

Two ways to decide that a predicted span matches a gold span; each gold span matches at most one prediction.
  jaccard   overlap / union >= threshold. The headline: CUAD's own measure. Strict when one span is much longer.
  coverage  overlap / the shorter span >= threshold. Secondary and more lenient: it counts a prediction that sits
            inside a long labeled span, or a long prediction that contains a short labeled span.
"""


def overlap(a, b):
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def coverage(a, b):
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    shorter = min(a[1] - a[0], b[1] - b[0])
    return inter / shorter if shorter > 0 else 0.0


MEASURES = {"jaccard": overlap, "coverage": coverage}


def score(gold, pred, threshold=0.5, measure="jaccard"):
    """gold/pred: {category: [(start, end), ...]} for one or more docs (keys may be (doc, category))."""
    match = MEASURES[measure]
    out = {}
    for cat in set(gold) | set(pred):
        g, p = list(gold.get(cat, [])), list(pred.get(cat, []))
        matched, tp = set(), 0
        for ps in p:
            hit = next((i for i, gs in enumerate(g) if i not in matched and match(ps, gs) >= threshold), None)
            if hit is not None:
                matched.add(hit)
                tp += 1
        prec = tp / len(p) if p else 0.0
        rec = tp / len(g) if g else 0.0
        out[cat] = {"precision": prec, "recall": rec, "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
                    "tp": tp, "n_pred": len(p), "n_gold": len(g)}
    return out

"""Verify: a quote counts only if it appears in the source after whitespace normalization."""


def _normalize(text):
    """Collapse whitespace runs; return (normalized, map from normalized index -> original index)."""
    out, idx, prev_space = [], [], True
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                idx.append(i)
            prev_space = True
        else:
            out.append(ch)
            idx.append(i)
            prev_space = False
    return "".join(out).rstrip(), idx


def locate(quote, source_norm, idx):
    q = " ".join(quote.split())
    if len(q) < 15:  # too short to be evidence
        return None
    s = source_norm.find(q)
    if s == -1:
        return None
    return idx[s], idx[s + len(q) - 1] + 1  # original-text char span


def verify(candidates, text):
    norm, idx = _normalize(text)
    kept, dropped = [], []
    for c in candidates:
        span = locate(c["quote"], norm, idx)
        if span is None:
            dropped.append(c)  # logged by caller; never shown to the user
        else:
            kept.append({**c, "start": span[0], "end": span[1], "quote": text[span[0]:span[1]]})
    # Collapse overlapping spans within a category (regex and the model often hit the same clause). The model's quote
    # wins over a regex quote; among quotes from the same source the tightest wins.
    kept.sort(key=lambda f: (f.get("source") != "llm", f["end"] - f["start"]))
    final = []
    for f in kept:
        if not any(g["category"] == f["category"] and f["start"] < g["end"] and g["start"] < f["end"] for g in final):
            final.append(f)
    return sorted(final, key=lambda f: (f["category"], f["start"])), dropped

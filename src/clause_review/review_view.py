"""Helpers for the review workspace and the overview: tidy contract titles, the list of (contract, clause) pairs to step
through, what is left to do in each, and the excerpt of a contract around a quotation with the quotation marked."""
import html
import re

from .store import FOUND, NOT_FOUND


def split_title(name):
    """A file name such as 'contract_01 - Endorsement Agreement (MusclePharm).txt' -> (title, party, code):
    ('Endorsement Agreement', 'MusclePharm', 'contract_01'). Anything that does not fit the pattern is kept whole."""
    stem = re.sub(r"\.(txt|pdf)$", "", name, flags=re.I)
    m = re.match(r"^(contract_\d+|sample)\s*-\s*(.*)$", stem, re.I)
    code, rest = (m.group(1), m.group(2)) if m else ("", stem)
    p = None if code.lower() == "sample" else re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", rest)
    title, party = (p.group(1), p.group(2)) if p else (rest, "")
    return title.strip() or stem, party.strip(), code


def display_name(name, dev=False):
    """A contract as a person names it: 'Cooperation Agreement (HPIL Energytech and Ginares)'. The test-file number
    ('contract_02') is only added in dev mode. A name that does not fit the pattern is returned as it is, without '.txt'."""
    title, party, code = split_title(name)
    label = f"{title} ({party})" if party else title
    return f"{code} · {label}" if dev and code else label


def build_slots(docs):
    """Every (contract id, clause) pair of a review in a fixed order: contracts as uploaded, clauses as listed. The review
    screen steps through these and the overview opens one."""
    return [(d["id"], c) for d in docs for c in d["categories"]]


def live_findings(doc, category):
    return [f for f in doc["findings"] if f["category"] == category and f["review"] != "removed"]


def needs_work(doc, category):
    """True while a quote the tool found here is still waiting for a decision (not yet accepted or removed). A clause with
    nothing found is never a task: it stays visible as a gap (see is_gap) but does not hold up the queue or the count."""
    return any(f["review"] == "pending" for f in live_findings(doc, category))


def is_gap(doc, category):
    """A clause with nothing confirmed in it: nothing found, every finding removed, or the file failed. The reviewer is
    told, but it is not a to-do item. A person marking it 'checked' only records that they looked."""
    return clause_state(doc, category) in ("check", "failed")


def clause_state(doc, category):
    """One word for a cell of the overview: 'failed', 'check' (nothing found), 'accepted' (every finding accepted),
    or 'found' (findings, some not yet reviewed)."""
    if doc["status"] == "failed" or doc["categories"].get(category) not in (FOUND, NOT_FOUND):
        return "failed"
    live = live_findings(doc, category)
    if not live:
        return "check"
    return "accepted" if all(f["review"] == "accepted" for f in live) else "found"


def _snap(text, i, forward):
    """Move an offset to a line boundary so an excerpt does not start or stop in the middle of a line."""
    if i <= 0:
        return 0
    if i >= len(text):
        return len(text)
    if forward:
        j = text.find("\n", i, i + 600)
        if j == -1:
            j = text.find(" ", i, i + 200)  # no line break nearby (one long line): end on a word
        return i if j == -1 else j
    j = text.rfind("\n", max(0, i - 600), i)
    if j != -1:
        return j + 1
    j = text.find(" ", i, i + 200)  # begin on a word, not in the middle of one
    return i if j == -1 else j + 1


def _merge(spans):
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def _marked(text, lo, hi, spans):
    """text[lo:hi] as HTML-safe text with <mark> around each span and <br> for line breaks. Overlaps are merged."""
    out, pos = [], lo
    for a, b in _merge(sorted((max(a, lo), min(b, hi)) for a, b in spans if b > lo and a < hi)):
        out.append(html.escape(text[pos:a]))
        out.append("<mark>" + html.escape(text[a:b]) + "</mark>")
        pos = b
    out.append(html.escape(text[pos:hi]))
    shown = "".join(out).replace("\n", "<br>")
    return re.sub(r"(?:<br>\s*){3,}", "<br><br>", shown)  # long runs of blank lines (page breaks, tables) become one gap


def passage_html(text, spans, before=1400, after=2600):
    """The part of a contract around some quotations, with the quotations marked. With no spans it shows the start of
    the contract. Returns (html, lo, hi): the excerpt's bounds in the text, so a caller can tell whether more lies above
    or below."""
    if spans:
        lo = _snap(text, max(0, min(a for a, _ in spans) - before), forward=False)
        hi = _snap(text, min(len(text), max(b for _, b in spans) + after), forward=True)
    else:
        lo, hi = 0, _snap(text, min(len(text), before + after), forward=True)
    return _marked(text, lo, hi, spans), lo, hi


def search_snippets(text, query, limit=8, context=170):
    """Where a word or phrase occurs in a contract: (list of HTML snippets with the match marked, total matches).
    The match is literal and ignores case. Fewer than two characters finds nothing."""
    query = (query or "").strip()
    if len(query) < 2:
        return [], 0
    hits = [m.span() for m in re.finditer(re.escape(query), text, flags=re.I)]
    snippets = []
    for a, b in hits[:limit]:
        lo, hi = max(0, a - context), min(len(text), b + context)
        snippets.append(("… " if lo else "") + _marked(text, lo, hi, [(a, b)]) + (" …" if hi < len(text) else ""))
    return snippets, len(hits)


def overview_stats(docs, cats):
    """Everything the Overview shows, counted once: how much is decided, what waits on the Senior Lawyer, what is ready for
    the Junior Associate to resolve, how many clauses have nothing found or failed, per-contract work left and, for each
    clause, in how many contracts something was found. `docs` come from load_results."""
    f_all = [f for d in docs for f in d["findings"] if f["category"] in cats]
    pending = sum(1 for f in f_all if f["review"] == "pending")
    removed = sum(1 for f in f_all if f["review"] == "removed")
    accepted = sum(1 for f in f_all if f["review"] == "accepted")
    live = [f for f in f_all if f["review"] != "removed"]
    waiting = [f for f in live if f["question"] and f["qstate"] in (None, "open")]
    answered = [f for f in live if f["question"] and f["qstate"] == "answered"]
    states = {(d["id"], c): clause_state(d, c) for d in docs for c in cats}
    return {
        "total": len(f_all), "pending": pending, "accepted": accepted, "removed": removed, "decided": accepted + removed,
        "waiting": len(waiting), "answered": len(answered),
        "waiting_ids": [f["id"] for f in waiting], "answered_ids": [f["id"] for f in answered],
        "nothing": sum(1 for v in states.values() if v == "check"), "failed": sum(1 for v in states.values() if v == "failed"),
        "left": {d["id"]: sum(1 for f in d["findings"] if f["category"] in cats and f["review"] == "pending") for d in docs},
        "found_in": {c: sum(1 for d in docs if states[(d["id"], c)] in ("found", "accepted")) for c in cats},
    }

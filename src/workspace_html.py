"""The review workspace drawn as one HTML component (ui/workspace.html/css/js) instead of Streamlit widgets, so the page
can match the design exactly. Everything that decides or stores anything stays in Python: this module builds the data
the page shows (`build_view`, no Streamlit needed) and applies what the page reports (`apply_action`).

Page -> Python: one trigger, `act`, with a dict such as {"type": "accept", "id": 7}. Python -> page: the `view` dict."""
import re
from pathlib import Path

from clause_review.review_view import build_slots, clause_state, is_gap, live_findings, passage_html, search_snippets, split_title
from clause_review.store import ANSWERED, OPEN, RESOLVED
from workspace import short

UI = Path(__file__).parent / "ui"
STATE_LABEL = {"found": "Found", "accepted": "Accepted", "check": "To check", "failed": "Failed"}


def build_items(slots, by_id):
    """What the review steps through, in reading order: (slot index, finding id) for every quote the tool found, and
    (slot index, None) for a clause with nothing found. One item is one screen."""
    items = []
    for i, (doc_id, cat) in enumerate(slots):
        live = live_findings(by_id[doc_id], cat)
        items += [(i, f["id"]) for f in live] if live else [(i, None)]
    return items


def selection(state, slots, by_id):
    """Which passage is on screen and which items Previous/Next walk through. `state` is st.session_state (or any dict);
    it is updated in place, including navigation requested by the page.
    Returns (position, finding id or None, members, items, pending ids)."""
    items = build_items(slots, by_id)
    index = {it: k for k, it in enumerate(items)}
    pending = {f["id"] for d in by_id.values() for f in d["findings"] if f["review"] == "pending"}
    state.setdefault("ws_mode", "To do")
    members = [it for it in items if state["ws_mode"] == "All clauses" or it[1] in pending]

    pos = min(state.get("ws_pos", 0), len(slots) - 1)
    live = live_findings(by_id[slots[pos][0]], slots[pos][1])
    ids = [f["id"] for f in live]
    fid = state.get("ws_fid")
    if fid not in ids:  # a new clause: start at its first passage still to decide, else its first
        fid = next((f["id"] for f in live if f["id"] in pending), ids[0] if ids else None)
    cur = (pos, fid)

    step = state.pop("ws_step", 0)
    if step and members:
        ahead = [m for m in members if (index[m] > index[cur] if step > 0 else index[m] < index[cur])]
        cur = (ahead[0] if step > 0 else ahead[-1]) if ahead else (members[0] if step > 0 else members[-1])  # wraps around
    pstep = state.pop("ws_pstep", 0)
    if pstep:  # through this contract's passages only, whatever their clause
        doc_id = slots[cur[0]][0]
        mine = [it for it in items if it[1] and slots[it[0]][0] == doc_id]
        ahead = [it for it in mine if (index[it] > index[cur] if pstep > 0 else index[it] < index[cur])]
        if ahead:
            cur = ahead[0] if pstep > 0 else ahead[-1]
            state["ws_mode"] = "All clauses"  # the passage may already be decided
            members = list(items)
    pinned = state.pop("ws_pin", False)
    if members and cur not in members and cur[1] is not None and not pinned:
        # the passage just decided left the list: go to the next one that remains. A clause with nothing found is not in
        # the list either, but someone who opened it on purpose stays on it.
        cur = next((m for m in members if index[m] > index[cur]), members[0])
    state["ws_pos"], state["ws_fid"] = cur
    return cur[0], cur[1], members, items, pending


def build_view(store, docs, state, categories=None):
    """Everything the page draws, as plain JSON-able data."""
    slots = build_slots(docs)
    if not slots:
        return {"empty": True}
    by_id = {d["id"]: d for d in docs}
    pos, fid, members, items, pending = selection(state, slots, by_id)
    doc_id, cat = slots[pos]
    doc = by_id[doc_id]
    title, party, code = split_title(doc["name"])
    live = live_findings(doc, cat)
    current = next((f for f in live if f["id"] == fid), None)
    cur = (pos, fid)
    where = members.index(cur) + 1 if cur in members else 0
    later = [m for m in members if items.index(m) > items.index(cur)][:2]
    total = sum(1 for it in items if it[1])

    def upnext(m):
        d, c = slots[m[0]]
        ids = [f["id"] for f in live_findings(by_id[d], c)]
        return {"name": split_title(by_id[d]["name"])[0],
                "clause": short(c) + (f" · passage {ids.index(m[1]) + 1}" if len(ids) > 1 and m[1] else ""),
                "state": clause_state(by_id[d], c), "label": STATE_LABEL[clause_state(by_id[d], c)]}

    view = {
        "empty": False, "docId": doc_id, "category": cat, "nothingLeft": not members, "mode": state["ws_mode"],
        "position": {"at": where, "of": len(members)},
        "progress": 1.0 if not total else (total - len(pending)) / total,
        "gaps": [{"doc": d, "name": c, "title": split_title(by_id[d]["name"])[0], "clause": short(c), "state": clause_state(by_id[d], c),
                  "checked": bool(by_id[d]["reviewed"].get(c))} for d, c in slots if is_gap(by_id[d], c)],
        "title": title, "party": party, "contractNo": docs.index(doc) + 1, "contracts": len(docs),
        "foundCount": sum(1 for c in doc["categories"] if clause_state(doc, c) in ("found", "accepted")),
        "clauseCount": len(doc["categories"]),
        "clauses": [{"name": c, "label": short(c), "state": clause_state(doc, c), "active": c == cat} for c in doc["categories"]],
        "current": {"name": short(cat), "state": clause_state(doc, cat), "status": doc["categories"][cat] or "Failed",
                    "reviewed": bool(doc["reviewed"].get(cat)), "failed": doc["error"] if doc["status"] == "failed" else None},
        "findings": [_finding(current, [f["id"] for f in live].index(fid) + 1, len(live), doc["name"])] if current else [],
        "removed": [{"id": f["id"], "quote": " ".join(f["quote"].split())}
                    for f in doc["findings"] if f["category"] == cat and f["review"] == "removed"],
        "upNext": [upnext(m) for m in later],
        "file": " · ".join(x for x in ((code if state.get("dev_mode") else ""), party) if x) or (title if code else doc["name"]),
        "fileFull": doc["name"],  # (the test-file number shows in dev mode only)
    }
    view["document"] = _document(store, doc, cat, current, state)
    return view


def _finding(f, i, n, name=""):
    """One passage for the page. The page number is only passed on for a PDF: a text file has no pages, so "page 1" would mislead."""
    return {"id": f["id"], "index": i, "of": n, "page": f["page"] if name.lower().endswith(".pdf") and f["page"] else None, "review": f["review"], "quote": " ".join(f["quote"].split()),
            "question": f["question"] or "", "answer": f["answer"] or "", "qstate": f["qstate"] or (OPEN if f["question"] else None)}


_HEAD = re.compile(r"(?:\d+(?:\.\d+)*\.?\s+)?[A-Z][A-Z0-9 ,&'/()\-]+")
_BREAKS = [  # places where a new paragraph starts inside running text (X = a marked passage, treated as a capital)
    re.compile(r"(?<=[.;:\"”\d])\s{3,}(?=\(?[A-Za-z0-9X]{1,4}[.)]\s|\d{1,2}\.\d)"),        # runs of spaces left by line breaks, before "(b)", "12." or "9.1"
    re.compile(r"(?<=[.;:\"”\d])\s+(?=\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\s+[A-ZX(])"),             # "... void. 9.2 Any transfer"
    re.compile(r"(?<=[.;:\"”\d])\s+(?=\d{1,2}\.\s+[A-Z][A-Z ,&'\-]{3,60}(?:\s|\x00|$))"),           # "... 8. ASSIGNMENT ..."
]


def readable(body):
    """Contract text as paragraphs, the way the design shows it: blank lines and the numbering of sections ("9.1", "(b)",
    "10. TERMINATION") start new paragraphs, a single line break is only a wrapped line, a short line in capitals (or a
    numbered one) is a bold heading, and when a passage is marked, the section around it is dark while the rest is dimmed.
    `body` is the output of passage_html: escaped text with <mark> and <br> only. Contract text is never turned into
    anything but text, <p>, <mark>."""
    marks = []

    def hold(m):
        marks.append(re.sub(r"(?:<br>\s*)+", " ", m.group(0)))  # a marked passage stays inside one paragraph
        return f"X{len(marks) - 1}\x01"
    body = re.sub(r"<mark>.*?</mark>", hold, body, flags=re.S)
    body = re.sub(r"(?:<br>\s*){2,}", "\x00", body)
    for rx in _BREAKS:
        body = rx.sub("\x00", body)
    paras = []
    for p in body.split("\x00"):
        p = re.sub(r"\s*<br>\s*", " ", p)
        p = re.sub(r"(?:\s?\.){4,}\s*", " … ", p)  # a table of contents' dot leaders ("Term.........") become one ellipsis
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            paras.append(p)
    restore = lambda p: re.sub(r"X(\d+)\x01", lambda m: marks[int(m.group(1))], p)
    flags = []  # (is heading, has a marked passage)
    for p in paras:
        plain = re.sub(r"X\d+\x01", "", p)
        flags.append((len(plain) <= 70 and bool(_HEAD.fullmatch(plain)), "\x01" in p))
    hit = [i for i, (_, m) in enumerate(flags) if m]
    active = set(range(len(paras)))
    if hit:
        lo = next((i for i in range(hit[0], -1, -1) if flags[i][0]), hit[0])
        hi = next((i for i in range(hit[-1] + 1, len(paras)) if flags[i][0]), hit[-1] + 1)
        active = set(range(lo, min(hi, hit[-1] + 5)))
    out = []
    for i, p in enumerate(paras):
        cls = " ".join(c for c in ("h" if flags[i][0] else "", "" if i in active else "dim") if c)
        out.append(f'<p class="{cls}">{restore(p)}</p>' if cls else f"<p>{restore(p)}</p>")
    return "".join(out)


def _document(store, doc, cat, current, state):
    text = store.document_text(doc["id"])
    query = state.get(f"find{doc['id']}", "").strip()
    if query:
        snippets, total = search_snippets(text, query)
        return {"mode": "search", "query": query, "total": total, "snippets": snippets, "short": len(query) < 2}
    spans = [(current["start"], current["end"])] if current else []  # only the passage on screen is marked
    body, _, _ = passage_html(text, spans, len(text), len(text))  # the whole contract, scrolled to the marked passage
    ticks = [{"top": round(min(96, max(2, 100 * f["start"] / max(1, len(text)))), 1), "now": bool(current) and f["id"] == current["id"],
              "label": short(f["category"])} for f in doc["findings"] if f["review"] != "removed"]
    return {"mode": "passage", "html": readable(body), "ticks": ticks,
            "hasSpans": bool(spans), "scrollKey": f"{doc['id']}|{cat}|{current['id'] if current else ''}"}


def apply_action(store, state, act, docs):
    """Do what the page asked. Returns "overview" when the page wants the Overview, else None. Unknown or stale actions
    are ignored (the page can lag a click behind the data)."""
    kind = (act or {}).get("type")
    fid = act.get("id") if act else None
    if kind == "prev":
        state["ws_step"] = -1
    elif kind == "next":
        state["ws_step"] = 1
    elif kind == "pprev":
        state["ws_pstep"] = -1
    elif kind == "pnext":
        state["ws_pstep"] = 1
    elif kind == "mode" and act.get("mode") in ("To do", "All clauses"):
        state["ws_mode"] = act["mode"]
    elif kind in ("clause", "jump"):
        slots = build_slots(docs)
        doc_id = act.get("doc") or slots[min(state.get("ws_pos", 0), len(slots) - 1)][0]
        if (doc_id, act.get("name")) in slots:
            state["ws_pos"] = slots.index((doc_id, act["name"]))
            state.pop("ws_fid", None)  # start at that clause's first passage still to decide
            state["ws_pin"] = True  # chosen on purpose, so it is not skipped even if it is already decided
    elif kind in ("accept", "remove", "restore") and fid:
        store.set_review(fid, {"accept": "accepted", "remove": "removed", "restore": "pending"}[kind])
    elif kind == "undo" and fid:  # take the last Accept or Remove back and show that passage again
        store.set_review(fid, "pending")
        slots = build_slots(docs)
        if (act.get("doc"), act.get("name")) in slots:
            state["ws_pos"], state["ws_fid"], state["ws_pin"] = slots.index((act["doc"], act["name"])), fid, True
    elif kind == "ask" and fid:
        store.set_question(fid, act.get("text", ""))
    elif kind == "resolve" and fid:
        store.set_resolved(fid, bool(act.get("on", True)))
    elif kind == "reviewed":
        store.set_category_reviewed(act["doc"], act["name"], bool(act.get("on")))
    elif kind == "find":
        state[f"find{act['doc']}"] = act.get("q", "")
    elif kind == "overview":
        return "overview"
    return None


FULL_BLEED = ('<style>[data-testid="stMain"] .block-container{max-width:none!important;padding:0!important}[data-testid="stHeader"]{background:transparent!important;height:0!important}[data-testid="stToolbar"]{z-index:1000}'
              '[data-testid="stMain"] [data-testid="stVerticalBlock"]{gap:0!important}</style>')  # the page runs edge to edge beside the sidebar
_component = None


def _mount():
    global _component
    if _component is None:
        import streamlit as st
        _component = st.components.v2.component(
            "clautra_workspace", html=(UI / "workspace.html").read_text(encoding="utf-8"),
            css=(UI / "workspace.css").read_text(encoding="utf-8"), js=(UI / "workspace.js").read_text(encoding="utf-8"))
    return _component


def render(st, store, res, docs):
    """Draw the workspace. Clicks arrive through the component's `act` trigger; the callback applies them before the next
    draw, and a request for the Overview is carried out after it."""
    view = build_view(store, docs, st.session_state)
    if view.get("empty"):
        st.info("This review has no contracts.")
        return

    def on_act():
        act = (st.session_state.get("ws_html") or {}).get("act")
        if apply_action(store, st.session_state, act, docs) == "overview":
            st.session_state["ws_goto_overview"] = True

    if view["nothingLeft"] and view["mode"] == "To do":
        _completion(st, store, res, docs, view)
        return
    st.markdown(FULL_BLEED, unsafe_allow_html=True)
    _mount()(key="ws_html", data=view, on_act_change=on_act, height="content")
    if st.session_state.pop("ws_goto_overview", False):
        st.switch_page("pages/2_Overview.py")


def _look_back(st):
    st.session_state["ws_mode"] = "All clauses"
    st.session_state["ws_pos"] = 0  # from the first passage
    st.session_state.pop("ws_fid", None)
    st.session_state["ws_pin"] = True


def _completion(st, store, res, docs, view):
    """The finish line: every passage the tool found has been decided. A summary, the CSV, and the way back."""
    from clause_review.export import csv_text
    from theme import kpi_row
    findings = [f for d in docs for f in d["findings"]]
    accepted = sum(1 for f in findings if f["review"] == "accepted")
    removed = sum(1 for f in findings if f["review"] == "removed")
    waiting = sum(1 for f in findings if f["review"] != "removed" and f["question"] and f["qstate"] == OPEN)
    nothing = sum(1 for g in view["gaps"] if not g["checked"])
    st.markdown('<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Junior associate</div><h1>All decided</h1>'
                '<p class="tag">Every passage the tool found has been accepted or removed.</p><hr class="rule"></div>',
                unsafe_allow_html=True)
    kpi_row(st, [(accepted, "Accepted", None, False), (removed, "Removed", None, False),
                 (waiting, "Question waiting for the senior lawyer" if waiting == 1 else "Questions waiting for the senior lawyer",
                  "export again once they answer" if waiting else None, waiting > 0),
                 (nothing, "Clause with nothing found" if nothing == 1 else "Clauses with nothing found",
                  "listed in the CSV as Not found, for you to check by hand" if nothing else None, nothing > 0)])
    a, b, c = st.columns([1.2, 1.2, 2])
    a.download_button("Download CSV", csv_text(store, res["pid"]), file_name="clause_review.csv", mime="text/csv",
                      type="primary", use_container_width=True, key="done_csv",
                      help="Every finding with its review state, plus a row for every clause with nothing found.")
    b.page_link("pages/2_Overview.py", label="See the overview", icon=":material/grid_view:")
    c.button("Look back at the passages", on_click=_look_back, args=(st,))

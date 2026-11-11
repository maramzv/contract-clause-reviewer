"""The review workspace: one contract and one clause at a time on the left, the contract text beside it with the quoted
passage marked. It steps through what is still to do, so a reviewer always knows what comes next.

Drawing and clicks only; what counts as "still to do" lives in clause_review.review_view."""
import html

from clause_review.review_view import build_slots, clause_state, live_findings, needs_work, passage_html, search_snippets, split_title
from clause_review.store import ANSWERED, OPEN, RESOLVED
from clause_review.view import md_escape
from theme import category_heading

QSTATE_CHIP = {OPEN: ("chip-miss", "Question open: waiting for the senior lawyer"),
               ANSWERED: ("chip-found", "Answered by the senior lawyer"), RESOLVED: ("chip-found", "Question resolved")}
DOT = {"found": "●", "accepted": "●", "check": "○", "failed": "■"}
SHORT = {"Termination for Convenience": "Termination"}  # short names for the clause strip
MORE = 2500  # characters added each time "Earlier text" or "Later text" is pressed


def short(category):
    s = SHORT.get(category, category)
    return s[:1] + s[1:].lower()  # sentence case: "Change of control", "Governing law"


def render(st, store, res, docs):
    """Draw the workspace for the review `res` (the dict kept in st.session_state['result']) whose results are `docs`."""
    slots = build_slots(docs)
    by_id = {d["id"]: d for d in docs}
    if not slots:
        st.info("This review has no contracts.")
        return
    todo = {s for s in slots if needs_work(by_id[s[0]], s[1])}
    st.session_state.setdefault("ws_mode", "To do")
    mode = st.session_state["ws_mode"]
    members = [s for s in slots if mode == "All clauses" or s in todo]

    _apply_navigation(st, slots, members, by_id)
    pos = min(st.session_state.get("ws_pos", 0), len(slots) - 1)
    if members and slots[pos] not in members:  # the clause just finished left the list: go to the next one that remains
        pos = slots.index(next((s for s in members if slots.index(s) > pos), members[0]))
    st.session_state["ws_pos"] = pos
    doc_id, cat = slots[pos]
    doc = by_id[doc_id]

    left, right = st.columns([8, 12], gap="large")
    with left:
        _left(st, store, docs, slots, members, todo, pos, doc, cat)
    with right:
        _document(st, store, doc, cat, slots)


def _apply_navigation(st, slots, members, by_id):
    """Previous / Next (through what is left to do) and Previous / Next passage (through this contract's findings),
    applied before anything is drawn."""
    pos = st.session_state.get("ws_pos", 0)
    step = st.session_state.pop("ws_step", 0)
    if step and members:
        ahead = [s for s in members if (slots.index(s) > pos if step > 0 else slots.index(s) < pos)]
        pick = (ahead[0] if step > 0 else ahead[-1]) if ahead else (members[0] if step > 0 else members[-1])  # wraps around
        st.session_state["ws_pos"] = slots.index(pick)
    pstep = st.session_state.pop("ws_pstep", 0)
    if pstep:
        pos = st.session_state.get("ws_pos", 0)
        doc_id = slots[min(pos, len(slots) - 1)][0]
        mine = [i for i, s in enumerate(slots) if s[0] == doc_id and live_findings(by_id[doc_id], s[1])]
        ahead = [i for i in mine if (i > pos if pstep > 0 else i < pos)]
        if ahead:
            st.session_state["ws_pos"] = ahead[0] if pstep > 0 else ahead[-1]
            st.session_state["ws_mode"] = "All clauses"  # the passage may belong to a clause that is already done


def _set(st, key, value):
    st.session_state[key] = value


def _pick_clause(st, slots, doc_id):
    chosen = st.session_state.get("ws_clause")
    if chosen:
        st.session_state["ws_pos"] = slots.index((doc_id, chosen))


def _left(st, store, docs, slots, members, todo, pos, doc, cat):
    title, party, code = split_title(doc["name"])
    cur = slots[pos]
    where = members.index(cur) + 1 if cur in members else 0
    top, b_prev, b_next = st.columns([5, 2, 2])
    top.markdown(f"**{where} of {len(members)}** still to do" if st.session_state["ws_mode"] == "To do" and members
                 else (f"**{where} of {len(members)}** clauses" if members else "Nothing left to do"))
    b_prev.button("Previous", key="ws_prev", on_click=_set, args=(st, "ws_step", -1), use_container_width=True, disabled=not members)
    b_next.button("Next", key="ws_next", on_click=_set, args=(st, "ws_step", 1), use_container_width=True, disabled=not members)
    st.progress((len(slots) - len(todo)) / len(slots))
    st.page_link("app.py", label="See every contract and clause in the overview", icon=":material/grid_view:")

    if not members:
        st.success("Everything is decided or marked as checked. Download the CSV from the sidebar, or switch to "
                   "All clauses below to look back.")
        st.radio("Show", ["To do", "All clauses"], key="ws_mode", horizontal=True)
        return

    found = sum(1 for c in doc["categories"] if clause_state(doc, c) in ("found", "accepted"))
    st.markdown(f'<div class="ws-title">{html.escape(title)}</div>'
                f'<div class="ws-sub">{html.escape(party + " · " if party else "")}contract {docs.index(doc) + 1} of {len(docs)} · '
                f'{found} of {len(doc["categories"])} clauses found</div>', unsafe_allow_html=True)

    cats = list(doc["categories"])
    labels = {c: f"{DOT[clause_state(doc, c)]} {short(c)}" for c in cats}
    st.session_state["ws_clause"] = cat  # keep the strip on the clause being shown
    st.pills("Clause", cats, key="ws_clause", format_func=labels.get, label_visibility="collapsed",
             on_change=_pick_clause, args=(st, slots, doc["id"]))

    status = doc["categories"][cat] or "Failed to process"
    live = live_findings(doc, cat)
    st.markdown(category_heading(short(cat), status, doc["reviewed"][cat]), unsafe_allow_html=True)
    if doc["status"] == "failed":
        st.error(f"Failed to process: {doc['error']}")
    for i, f in enumerate(live, 1):
        _finding(st, store, f, i, len(live))
    if not live:
        st.markdown("Nothing confirmed here. An empty result is not proof the clause is absent: search the contract "
                    "yourself with **Find in contract**, then mark the clause as checked.")
    for f in (x for x in doc["findings"] if x["category"] == cat and x["review"] == "removed"):
        st.markdown(f'<div class="quote removed">{html.escape(" ".join(f["quote"].split()))}</div>', unsafe_allow_html=True)
        st.button("Restore", key=f"restore{f['id']}", on_click=_review, args=(st, store, f["id"], "pending"))
    key = f"reviewed{doc['id']}-{cat}"
    st.checkbox("Mark this clause as checked" if not live else "Mark this clause as reviewed", value=doc["reviewed"][cat],
                key=key, on_change=_mark, args=(st, store, doc["id"], cat, key),
                help="Only a progress mark: it does not change the status above. For a clause with no finding it means "
                     "you searched the contract yourself.")

    st.divider()
    st.caption("UP NEXT")
    later = [s for s in members if slots.index(s) > pos][:2]
    for did, c in later:
        d2 = next(d for d in docs if d["id"] == did)
        st.markdown(f"{DOT[clause_state(d2, c)]} {md_escape(split_title(d2['name'])[0])} · {short(c)}")
    if not later:
        st.caption("That is the last one.")
    st.radio("Show", ["To do", "All clauses"], key="ws_mode", horizontal=True)


def _finding(st, store, f, i, n):
    st.markdown(f'<div class="passage-no">Passage {i} of {n} · '
                f'{"Not yet reviewed" if f["review"] == "pending" else f["review"].capitalize()}</div>'
                f'<div class="quote">{html.escape(" ".join(f["quote"].split()))}</div>', unsafe_allow_html=True)
    st.caption("Check the marked passage in the contract says the same, word for word.")
    b1, b2, b3 = st.columns([1, 1, 1.25])
    b1.button("Accept", key=f"accept{f['id']}", on_click=_review, args=(st, store, f["id"], "accepted"),
              type="secondary" if f["review"] == "accepted" else "primary", disabled=f["review"] == "accepted",
              use_container_width=True)
    b2.button("Remove", key=f"remove{f['id']}", on_click=_review, args=(st, store, f["id"], "removed"),
              use_container_width=True)
    qkey = f"q{f['id']}"
    with b3.popover("Edit question" if f["question"] else "Ask senior", use_container_width=True):
        st.text_area("Question for the senior lawyer", value=f["question"] or "", key=qkey, height=100,
                     placeholder="e.g. Does a transfer to an affiliate count as assignment here?",
                     help="One question per finding. Saving new text reopens it; saving empty text removes it.")
        st.button("Save question", key=f"saveq{f['id']}", on_click=_question, args=(st, store, f["id"], qkey))
    if f["question"]:
        with st.container(key=f"qa{f['id']}"):
            cls, text = QSTATE_CHIP[f["qstate"] or OPEN]
            st.markdown(f'<span class="chip {cls}">{text}</span>', unsafe_allow_html=True)
            st.markdown("**You asked:** " + md_escape(f["question"]))
            if f["answer"]:
                st.markdown("**Senior lawyer:** " + md_escape(f["answer"]))
                if f["qstate"] == RESOLVED:
                    st.button("Reopen", key=f"reopen{f['id']}", on_click=_resolve, args=(st, store, f["id"], False))
                else:
                    st.button("Mark resolved", key=f"resolve{f['id']}", on_click=_resolve, args=(st, store, f["id"], True))


def _document(st, store, doc, cat, slots):
    """The contract beside the findings: the passage around the quotation, or the search results for a typed phrase."""
    text = store.document_text(doc["id"])
    st.markdown('<div class="ws-doc-title">Contract text</div>'
                f'<div class="ws-doc-file" title="{html.escape(doc["name"])}">{html.escape(doc["name"])}</div>', unsafe_allow_html=True)
    h2, h3, h4 = st.columns(3)
    h2.button("Previous passage", key="ws_pprev", on_click=_set, args=(st, "ws_pstep", -1), use_container_width=True)
    h3.button("Next passage", key="ws_pnext", on_click=_set, args=(st, "ws_pstep", 1), use_container_width=True)
    with h4.popover("Find in contract", use_container_width=True):
        query = st.text_input("Find in contract", key=f"find{doc['id']}", placeholder="A word or phrase",
                              label_visibility="collapsed")
        st.caption("Searches the whole contract and shows the first matches here.")
    if query.strip():
        snippets, total = search_snippets(text, query)
        if len(query.strip()) < 2:
            st.caption("Type at least two characters.")
        elif not total:
            st.markdown('<div class="docwrap"><div class="doc">No match in this contract.</div></div>', unsafe_allow_html=True)
        else:
            st.caption(f"{total} match{'es' if total != 1 else ''} for “{query.strip()}”"
                       + (f", showing the first {len(snippets)}" if total > len(snippets) else ""))
            body = "<hr>".join(f"<p>{s}</p>" for s in snippets)
            st.markdown(f'<div class="docwrap"><div class="doc">{body}</div></div>', unsafe_allow_html=True)
        return
    live = live_findings(doc, cat)
    spans = [(f["start"], f["end"]) for f in live]
    ctx = st.session_state.setdefault("ws_ctx", {})
    extra_before, extra_after = ctx.get((doc["id"], cat), (0, 0))
    body, lo, hi = passage_html(text, spans, 300 + extra_before, 2400 + extra_after)
    if not spans:
        st.caption("Nothing was found for this clause, so this is the start of the contract. Use Find in contract.")
    gap = '<p class="doc-gap">…</p>'
    ticks = "".join(
        f'<span class="tick{" now" if f["category"] == cat else ""}" title="{html.escape(short(f["category"]))}" '
        f'style="top:{min(96, max(2, 100 * f["start"] / max(1, len(text)))):.1f}%"></span>'
        for f in doc["findings"] if f["review"] != "removed")
    st.markdown(f'<div class="docwrap"><div class="doc">{gap if lo > 0 else ""}{body}{gap if hi < len(text) else ""}</div>'
                f'<div class="strip" aria-label="Where the findings in this contract sit">{ticks}</div></div>', unsafe_allow_html=True)
    if spans:  # bring the marked passage to the top of the pane (it can sit below the fold when the text above is long)
        st.html(f"<script>/* {doc['id']}-{cat}-{extra_before}-{extra_after} */"
                "(function(){var n=0;function go(){var d=document.querySelector('.doc'),m=d&&d.querySelector('mark');"
                "if(m){d.scrollTop=Math.max(0,m.offsetTop-d.offsetTop-70);}if(++n<8)setTimeout(go,150);}go();})();</script>",
                unsafe_allow_javascript=True)
    e1, e2, _ = st.columns([1, 1, 3])
    e1.button("Earlier text", key="ws_earlier", disabled=lo == 0, on_click=_widen, args=(st, doc["id"], cat, MORE, 0),
              use_container_width=True)
    e2.button("Later text", key="ws_later", disabled=hi >= len(text), on_click=_widen, args=(st, doc["id"], cat, 0, MORE),
              use_container_width=True)


def _widen(st, doc_id, cat, before, after):
    ctx = st.session_state.setdefault("ws_ctx", {})
    b, a = ctx.get((doc_id, cat), (0, 0))
    ctx[(doc_id, cat)] = (b + before, a + after)


def _review(st, store, finding_id, state):
    store.set_review(finding_id, state)


def _question(st, store, finding_id, key):
    store.set_question(finding_id, st.session_state[key])


def _resolve(st, store, finding_id, resolved):
    store.set_resolved(finding_id, resolved)


def _mark(st, store, document_id, category, key):
    store.set_category_reviewed(document_id, category, st.session_state[key])

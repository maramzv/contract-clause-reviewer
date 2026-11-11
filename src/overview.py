"""The junior associate's home screen: every contract against every clause in one grid, so the reviewer sees at a glance
where the work is. A cell opens that clause in the Review page. Drawing and clicks only; what each cell means comes from
clause_review.review_view."""
from clause_review.categories import CATEGORIES
from clause_review.review_view import build_slots, clause_state, live_findings, split_title
from clause_review.store import ANSWERED
from clause_review.view import load_results
from theme import kpi_row
from workspace import short

REVIEW_PAGE = "pages/2_Review.py"
LABEL = {"found": "{n} found", "accepted": "Accepted", "check": "To check", "failed": "Failed"}


def render(st, store, res):
    """Draw the overview of the review `res` (the dict kept in st.session_state['result'])."""
    docs = load_results(store, res["pid"], res["categories"])
    cats = [c for c in CATEGORIES if c in res["categories"]]
    slots = build_slots(docs)
    all_f = [f for d in docs for f in d["findings"]]
    tally = {k: sum(1 for f in all_f if f["review"] == k) for k in ("pending", "accepted", "removed")}
    n_check = sum(1 for d in docs for c in cats if clause_state(d, c) in ("check", "failed"))
    answered = sum(1 for f in all_f if f["review"] != "removed" and f["qstate"] == ANSWERED)
    kpi_row(st, [(len(docs), "Contract" if len(docs) == 1 else "Contracts", None, False),
                 (tally["pending"], "Finding to verify" if tally["pending"] == 1 else "Findings to verify",
                  f"{tally['accepted']} accepted · {tally['removed']} removed", tally["pending"] > 0),
                 (n_check, "Clause to check by hand" if n_check == 1 else "Clauses to check by hand", "nothing found or file failed", n_check > 0),
                 (answered, "Question answered" if answered == 1 else "Questions answered", "waiting for you to resolve", answered > 0)])

    fcol, scol = st.columns([3, 2])
    view = fcol.radio("Show", ["All contracts", "To check by hand", "Has a question"], horizontal=True, label_visibility="collapsed")
    order = scol.radio("Sort", ["Most to do first", "As uploaded"], horizontal=True, label_visibility="collapsed")

    def n_open(d):
        return sum(1 for c in cats if clause_state(d, c) in ("check", "failed", "found"))

    def has_question(d):
        return any(f["question"] and f["review"] != "removed" for f in d["findings"])

    rows = docs
    if view == "To check by hand":
        rows = [d for d in rows if any(clause_state(d, c) in ("check", "failed") for c in cats)]
    elif view == "Has a question":
        rows = [d for d in rows if has_question(d)]
    if order == "Most to do first":
        rows = sorted(rows, key=lambda d: -n_open(d))  # stable: ties stay in upload order

    def jump(doc_id, cat):
        st.session_state["ws_pos"] = slots.index((doc_id, cat))
        st.session_state.pop("ws_fid", None)
        st.session_state["ws_mode"] = "All clauses"  # so a clause already done can still be opened
        st.switch_page(REVIEW_PAGE)

    st.markdown(
        '<div class="ov-key" role="list" aria-label="What each cell means">'
        '<span class="ov-key-i"><span class="ov-sw found">N found</span>quotes found, not reviewed yet</span>'
        '<span class="ov-key-i"><span class="ov-sw accepted">Accepted</span>you confirmed the quote</span>'
        '<span class="ov-key-i"><span class="ov-sw check">To check</span>nothing found: search the contract yourself</span>'
        '<span class="ov-key-i"><span class="ov-sw failed">Failed</span>the file could not be read</span>'
        '<span class="ov-key-i"><span class="ov-sw q">?</span>a question for the senior lawyer</span></div>', unsafe_allow_html=True)
    widths = [3.4] + [1.25] * len(cats)
    head = st.columns(widths)
    head[0].markdown('<div class="ov-head">Contract</div>', unsafe_allow_html=True)
    for col, c in zip(head[1:], cats):
        col.markdown(f'<div class="ov-head">{short(c)}</div>', unsafe_allow_html=True)
    if not rows:
        st.caption("No contracts match this filter.")
    for d in rows:
        title, party, code = split_title(d["name"])
        cols = st.columns(widths, vertical_alignment="center")
        sub = " · ".join(x for x in (party, code if st.session_state.get("dev_mode") else "") if x)  # the test-file number is for dev mode
        cols[0].markdown(f'<div class="ov-title">{title}</div><div class="ov-party">{sub}</div>', unsafe_allow_html=True)
        for col, c in zip(cols[1:], cats):
            state = clause_state(d, c)
            n = len(live_findings(d, c))
            asked = any(f["question"] and f["category"] == c and f["review"] != "removed" for f in d["findings"])
            label = LABEL[state].format(n=n) + (" ?" if asked else "")
            col.button(label, key=f"cell{state}_{d['id']}_{c}", on_click=jump, args=(d["id"], c), use_container_width=True,
                       help="Open this clause in the review.")

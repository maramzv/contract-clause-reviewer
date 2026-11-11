"""The Junior Associate's home screen. It answers three things: how far along am I, what is waiting on someone else, and where
is the work. Progress and what is waiting sit at the top, with a button to carry on; below is every contract against every clause,
where a cell shows what is left to decide there and opens that clause. Drawing and clicks only; every count comes from
clause_review.review_view.overview_stats."""
import html

from clause_review.categories import CATEGORIES
from clause_review.review_view import build_slots, clause_state, found_by_you, live_findings, overview_stats, question_flag, senior_decided, split_title
from clause_review.view import load_results
from theme import kpi_row
from workspace import short

REVIEW_PAGE = "pages/2_Review.py"
FILTERS = ["All contracts", "Needs review", "Has a question", "Gaps"]


def _noun(n, one, many):
    return f"{n} {one if n == 1 else many}"


def render(st, store, res):
    """Draw the whole page for the review `res` (the dict kept in st.session_state['result'])."""
    docs = load_results(store, res["pid"], res["categories"])
    cats = [c for c in CATEGORIES if c in res["categories"]]
    slots = build_slots(docs)
    by_id = {d["id"]: d for d in docs}
    s = overview_stats(docs, cats)

    def go(slot=None, fid=None, mode="All clauses"):
        """Open the Review page: on a given clause (and passage), or on the next passage still to decide."""
        if slot is not None:
            st.session_state["ws_pos"] = slots.index(slot)
            st.session_state["ws_pin"] = True  # opened on purpose, so not skipped even if already decided
            st.session_state["ws_fid"] = fid
            if fid is None:
                st.session_state.pop("ws_fid", None)
        st.session_state["ws_mode"] = mode
        st.switch_page(REVIEW_PAGE)

    def first_pending(doc):
        for f in doc["findings"]:
            if f["category"] in cats and f["review"] == "pending":
                return (doc["id"], f["category"]), f["id"]
        return None, None

    def open_contract(doc):
        slot, fid = first_pending(doc)
        if slot is None:  # nothing left to decide there: its first clause
            slot = next((x for x in slots if x[0] == doc["id"]), None)
        go(slot, fid, "To do" if fid else "All clauses")

    # ---- the title ----
    saved = store.run_for_project(res["pid"])
    crumb = f' &nbsp;/&nbsp; {html.escape(saved["name"][:40])}' if saved else ""  # the review's own name, given when it was started
    st.markdown(f'<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Junior Associate{crumb}</div><h1>Overview</h1>'
                '<p class="tag">Where every clause stands.</p><hr class="rule"></div>', unsafe_allow_html=True)

    # ---- how far along (the same numbers and bar as at the top of the Review), with the way to carry on beside it ----
    pct = round(100 * s["decided"] / s["total"]) if s["total"] else 100
    prog_col, go_col = st.columns([4, 1.3], vertical_alignment="bottom", gap="large")
    prog_col.markdown(f'<div class="ov-prog"><div class="ov-prog-t"><b>{s["decided"]} of {s["total"]}</b> passages reviewed · {s["pending"]} left</div>'
                      f'<div class="ov-bar"><span style="width:{max(2, pct) if s["total"] else 100}%"></span></div></div>', unsafe_allow_html=True)
    if s["pending"]:
        label = "Continue reviewing"
    else:
        label = "Finish and export" if s["total"] else "Open the review"
    if go_col.button(label, type="primary", icon=":material/arrow_forward:", use_container_width=True, key="ov_go"):
        if not s["pending"] and s["total"]:
            st.switch_page("pages/3_Export.py")  # everything reviewed: check the table and download it
        go(None, None, "To do")

    # ---- the four numbers ----
    kpi_row(st, [
        (len(docs), "Contract" if len(docs) == 1 else "Contracts", None, False),
        (s["pending"], "Passage to review" if s["pending"] == 1 else "Passages to review",
         f'{s["accepted"]} accepted · {s["removed"]} removed', s["pending"] > 0),
        (s["waiting"], "Pending question" if s["waiting"] == 1 else "Pending questions", "asked to the Senior Lawyer" if s["waiting"] else None, s["waiting"] > 0),
        (s["answered"], "Reply" if s["answered"] == 1 else "Replies", "ready for you to act on" if s["answered"] else None, s["answered"] > 0),
        (s["nothing"] + s["failed"], "Gap" if s["nothing"] + s["failed"] == 1 else "Gaps",
         "not found, review required" if s["nothing"] + s["failed"] else None, False)])

    # ---- the filter row (and a search once the list is long) ----
    many = len(docs) > 8
    f_col, q_col = st.columns([3, 1.4]) if many else (st.container(), None)
    view = f_col.pills("Show", FILTERS, selection_mode="single", default="All contracts", key="ov_filter", label_visibility="collapsed") or "All contracts"
    query = q_col.text_input("Find a contract", placeholder="Find a contract", label_visibility="collapsed", key="ov_find").strip().lower() if many else ""

    def has_question(d):
        return (any(f["question"] and f["review"] != "removed" for f in d["findings"])
                or any(q["question"] for c, q in d["gap_questions"].items() if c in cats))

    def has_gap(d):
        return any(clause_state(d, c) in ("check", "failed") for c in cats)

    rows = docs
    if view == "Needs review":
        rows = [d for d in rows if s["left"][d["id"]]]
    elif view == "Has a question":
        rows = [d for d in rows if has_question(d)]
    elif view == "Gaps":
        rows = [d for d in rows if has_gap(d)]
    if query:
        rows = [d for d in rows if query in split_title(d["name"])[0].lower() or query in split_title(d["name"])[1].lower()]

    # ---- the grid ----
    widths = [3.4] + [1.25] * len(cats)
    grid = st.container(key="ov_grid")  # the table's own card: legend, header and rows share one tall container, so the header can stay in view
    with grid:
        st.markdown('<div class="ov-legend"><span class="ov-sw accepted">Accepted</span> <span class="ov-sw found">To review</span> '
                    '<span class="ov-sw mine">Found by you</span> '
                    '<span class="ov-sw gap">Gap</span> not found, review required &nbsp;&nbsp;·&nbsp;&nbsp; '
                    '<span class="ov-sw q">?</span> waiting on Senior &nbsp;&nbsp;·&nbsp;&nbsp; '
                    '<span class="ov-sw q">!</span> answered &nbsp;&nbsp;·&nbsp;&nbsp; '
                    '<span class="ov-sw q">S</span> decided by Senior</div>', unsafe_allow_html=True)
        with st.container(key="ov_head"):
            head = st.columns(widths)
            head[0].markdown('<div class="ov-head">Contract</div>', unsafe_allow_html=True)
            for col, c in zip(head[1:], cats):
                col.markdown(f'<div class="ov-head">{short(c)}<span class="ov-found">found in {s["found_in"][c]} of {len(docs)}</span></div>',
                             unsafe_allow_html=True)
        if not rows:
            st.caption("No contracts match this filter.")
        for d in rows:
            title, party, code = split_title(d["name"])
            cols = st.columns(widths, vertical_alignment="center")
            left_n = s["left"][d["id"]]
            sub = " · ".join(x for x in (party, code if st.session_state.get("dev_mode") else "") if x)
            with cols[0].container(key=f"ovt_{d['id']}"):
                st.button(title, key=f"ovtb_{d['id']}", on_click=open_contract, args=(d,))  # no tooltip: it adds a hidden copy that takes space
                st.markdown(f'<div class="ov-party">{html.escape(sub)}{" · " if sub else ""}'
                            f'{"<b>" + str(left_n) + " left</b>" if left_n else "all reviewed"}</div>', unsafe_allow_html=True)
            for col, c in zip(cols[1:], cats):
                state = clause_state(d, c)
                live = live_findings(d, c)
                pend = [f for f in live if f["review"] == "pending"]
                kind = state
                if state == "found":
                    label = f"{len(pend)} to review"
                elif state == "accepted" and found_by_you(d, c):
                    kind, label = "mine", "Found by you"  # the tool found nothing; the reviewer highlighted the passage herself
                elif state == "check" and d["reviewed"].get(c):
                    kind, label = "checked", "Gap · checked"  # still a gap (never proof of absence), but the reviewer has looked
                else:
                    label = {"accepted": "Accepted", "check": "Gap", "failed": "Failed"}[state]
                flag = question_flag(d, c) or ("s" if senior_decided(d, c) else "")  # a question on a passage or the gap itself; else S when the Senior Lawyer decided one
                col.button(label, key=f"cell{kind}_{d['id']}_{c}" + (f"_flag{flag}" if flag else ""), on_click=go, args=((d["id"], c), pend[0]["id"] if pend else None),
                           use_container_width=True, help="Open this clause in the review.")

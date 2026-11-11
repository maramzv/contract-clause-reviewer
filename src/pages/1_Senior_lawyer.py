"""Senior Lawyer dashboard: read the questions Maya flagged next to the passage, answer them, see which contracts have a
clause and which categories are still unconfirmed. It reads the same saved review the Junior Associate's screen writes to, and
never changes the Junior Associate's accept / remove decisions.

Run with the Junior Associate's screen:  streamlit run app.py   (this page appears in the sidebar menu)"""
import html

import streamlit as st

from clause_review.categories import CATEGORIES
from clause_review.review_view import build_slots, display_name, run_label, run_when
from clause_review.store import ANSWERED, FOUND, OPEN, RESOLVED
from clause_review.view import load_results, md_escape
from common import get_store, new_review_button, refresh_corner
from theme import apply_theme, brand, category_heading, export_link, kpi_row, marquee, nav_gap, views

st.set_page_config(page_title="Clautra · Senior Lawyer", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
st.markdown('<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Senior Lawyer</div><h1>Overview</h1>'
            "<p class=\"tag\">Answer the Junior Associate's questions and see where the review stands.</p><hr class=\"rule\">"
            "<p class=\"lede\">The Junior Associate checks each clause the tool found and flags anything they are unsure about. "
            "<strong>Questions</strong> lists those flags beside the passage they are about: answer them here and the answer "
            "appears on their screen. <strong>By clause</strong> shows every contract's passages for one clause. "
            "<strong>Nothing found</strong> lists clauses where no passage was found or the file failed. They still need a check by "
            "hand. Their accept and remove decisions are shown here but cannot be changed.</p></div>",
            unsafe_allow_html=True)

STATE_LABEL = {OPEN: "Open", ANSWERED: "Answered", RESOLVED: "Resolved"}
STATE_CHIP = {OPEN: "chip-miss", ANSWERED: "chip-found", RESOLVED: "chip-found"}
store = get_store()


def shown(d):
    return display_name(d["name"], st.session_state.get("dev_mode", False))  # the test-file number is for dev mode



def answer(finding_id, key):
    store.set_answer(finding_id, st.session_state[key])


runs = store.list_runs()
with st.sidebar:
    brand(st)
    views(st)
    nav_gap(st)
    new_review_button(st)
    export_link(st)
    if not runs:
        st.caption("No saved reviews yet. The Junior Associate runs one first; it is saved automatically.")
    else:
        ids = [r["id"] for r in runs]
        current = (st.session_state.get("result") or {}).get("pid")  # the review open on the Junior Associate's screen, same session
        default = next((i for i, r in enumerate(runs) if r["project_id"] == current), 0)
        if st.query_params.get("open", "").isdigit() and int(st.query_params["open"]) in ids:
            default = ids.index(int(st.query_params["open"]))
        if len(ids) == 1:
            run_id = ids[0]  # nothing to choose: the title is on the page itself
        else:  # several reviews (for example one per deal): pick the one to look at
            st.header("Which review?")
            run_id = st.selectbox("Which review?", ids, index=default, label_visibility="collapsed",
                                  format_func=lambda i: run_label(next(r for r in runs if r["id"] == i)))
        refresh_corner(st)  # the refresh icon sits in the page corner, not in the left nav

if not runs:
    st.info("There is nothing to review yet. Ask the Junior Associate to run a review, then open this page again.")
    st.stop()

run = next(r for r in runs if r["id"] == run_id)
pid, cats = run["project_id"], run["categories"]
docs = load_results(store, pid, cats)
# which review this page is about: the name the Junior Associate gave it, how many contracts, and when it was run


def read_in_contract(doc_id, category, finding_id):
    """Open the contract beside this passage (or clause) on the Review page as the Senior Lawyer: the same screen the Junior Associate
    uses, with a box to answer the question and Accept / Remove, each recorded as the Senior Lawyer's decision."""
    st.session_state["review_role"] = "senior"
    st.session_state["result"] = {"pid": pid, "categories": cats, "provider": f"{run['provider']} (saved run)", "usage": run["usage"] or ""}
    st.session_state.update(ws_pos=build_slots(docs).index((doc_id, category)), ws_pin=True, ws_mode="All clauses")
    if finding_id is None:
        st.session_state.pop("ws_fid", None)
    else:
        st.session_state["ws_fid"] = finding_id
    st.switch_page("pages/2_Review.py")


st.markdown(f'<div class="rv-context"><span class="rv-eyebrow">Reviewing</span><span class="rv-name">{html.escape(run["name"])}</span>'
            f'<span class="rv-meta">{run["docs"]} contract{"s" if run["docs"] != 1 else ""} · run by the Junior Associate on '
            f'{html.escape(run_when(run["created"], with_time=True))}</span></div>', unsafe_allow_html=True)
asked = [(d, f) for d in docs for f in d["findings"] if f["question"] and f["review"] != "removed"]
# a question about a clause where nothing was found has no passage: it is shown with a note instead of a quotation
asked += [(d, {**q, "category": c, "quote": "", "page": None, "review": "accepted", "gap": True})
          for d in docs for c, q in d["gap_questions"].items() if q["question"] and c in cats]
count = {k: sum(1 for _, f in asked if f["qstate"] == k) for k in (OPEN, ANSWERED, RESOLVED)}
gaps = [(d, c) for d in docs for c in cats if d["categories"][c] != FOUND]
kpi_row(st, [(count[OPEN], "Open question" if count[OPEN] == 1 else "Open questions", "waiting for your answer", count[OPEN] > 0),
             (count[ANSWERED] + count[RESOLVED], "Answered", None, False),
             (len(gaps), "Clause with nothing found" if len(gaps) == 1 else "Clauses with nothing found", "no passage found, or the file failed", len(gaps) > 0)])

tab_q, tab_c, tab_g = st.tabs([f"Questions ({len(asked)})", "By clause", f"Nothing found ({len(gaps)})"])

with tab_q:
    if not asked:
        st.info("No questions yet. When the Junior Associate flags a passage, it appears here with the passage.")
    show = st.radio("Show", ["Needs my answer", "Answered", "All"], horizontal=True, label_visibility="collapsed")
    wanted = {"Needs my answer": (OPEN,), "Answered": (ANSWERED, RESOLVED), "All": (OPEN, ANSWERED, RESOLVED)}[show]
    for d, f in sorted((x for x in asked if x[1]["qstate"] in wanted), key=lambda x: (x[1]["qstate"] != OPEN, x[0]["id"], x[1]["id"])):
        with st.container(border=True):
            if f.get("gap"):
                st.caption(f"{shown(d)} · {f['category']} · Nothing found")
                st.markdown("> *The tool found no passage for this clause. The Junior Associate is asking whether it is really absent.*")
            else:
                added = " · found by the Junior Associate" if f["source"] == "manual" else ""
                who = "Senior Lawyer" if f.get("decided_by") == "senior" else "Junior Associate"
                st.caption(f"{shown(d)} · {f['category']} · Page {f['page']}{added} · {who} marked it "
                           f"{'not yet reviewed' if f['review'] == 'pending' else f['review']}")
                st.markdown("> " + md_escape(f["quote"]))
            st.markdown(f'<span class="chip {STATE_CHIP[f["qstate"]]}">{STATE_LABEL[f["qstate"]]}</span>', unsafe_allow_html=True)
            st.markdown("**Question:** " + md_escape(f["question"]))
            key = f"ans{f['id']}"
            st.text_area("Your answer", value=f["answer"] or "", key=key, height=90, label_visibility="collapsed",
                         placeholder="Your answer for the Junior Associate. Saving empty text takes an answer back.")
            b1, b2, _ = st.columns([1, 1.5, 3])
            b1.button("Save answer", key=f"save{f['id']}", type="primary" if f["qstate"] == OPEN else "secondary",
                      on_click=answer, args=(f["id"], key), use_container_width=True)
            b2.button("Read in contract", key=f"read{f['id']}", icon=":material/menu_book:", use_container_width=True,
                      on_click=read_in_contract, args=(d["id"], f["category"], None if f.get("gap") else f["id"]),
                      help="Open the contract beside this passage. You can answer, accept or remove from there.")
    if asked and not any(x[1]["qstate"] in wanted for x in asked):
        st.caption("Nothing here.")

with tab_c:
    pick = st.selectbox("Clause", [c for c in CATEGORIES if c in cats])
    st.caption("Every contract in this review, with what the tool found for this clause. Removed passages are left out.")
    for d in docs:
        status = d["categories"][pick] or "Failed to process"
        with st.container(border=True):
            st.markdown(category_heading(shown(d), status, d["reviewed"][pick]), unsafe_allow_html=True)
            for f in (x for x in d["findings"] if x["category"] == pick and x["review"] != "removed"):
                st.caption(f"Page {f['page']} · {'Not yet reviewed' if f['review'] == 'pending' else f['review'].capitalize()}"
                           + (" · has a question" if f["question"] else ""))
                st.markdown("> " + md_escape(f["quote"]))
            if status != FOUND:
                st.caption("Nothing confirmed. An empty result is not proof the clause is absent: ask for a manual check.")

with tab_g:
    if not gaps:
        st.success("Every clause in every contract has at least one passage.")
    else:
        st.caption("Clauses with nothing found. These are the ones to ask the Junior Associate to check by hand.")
    for d, c in gaps:
        st.markdown(category_heading(f"{shown(d)} · {c}", d["categories"][c] or "Failed to process", d["reviewed"][c]),
                    unsafe_allow_html=True)

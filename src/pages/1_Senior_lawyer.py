"""Senior lawyer dashboard: read the questions Maya flagged next to the passage, answer them, see which contracts have a
clause and which categories are still unconfirmed. It reads the same saved review the reviewer screen writes to, and
never changes her accept / remove decisions.

Run with the reviewer screen:  streamlit run app.py   (this page appears in the sidebar menu)"""
import streamlit as st

from clause_review.categories import CATEGORIES
from clause_review.export import csv_text, questions_csv_text
from clause_review.store import ANSWERED, FOUND, OPEN, RESOLVED
from clause_review.view import load_results, md_escape
from common import get_store
from theme import apply_theme, brand, category_heading, kpi_row, marquee, views

st.set_page_config(page_title="Clautra · Senior lawyer", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
st.markdown('<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Senior lawyer</div><h1>Senior review</h1>'
            '<p class="tag">What did she ask, and what is still unconfirmed?</p><hr class="rule">'
            '<p class="lede">Questions flagged by the reviewer sit beside the passage they are about. Answer them here; the '
            "reviewer sees your answer on her screen. Her accept and remove decisions are shown but not changed here.</p></div>",
            unsafe_allow_html=True)

STATE_LABEL = {OPEN: "Open", ANSWERED: "Answered", RESOLVED: "Resolved"}
STATE_CHIP = {OPEN: "chip-miss", ANSWERED: "chip-found", RESOLVED: "chip-found"}
store = get_store()


def answer(finding_id, key):
    store.set_answer(finding_id, st.session_state[key])


runs = store.list_runs()
with st.sidebar:
    brand(st)
    views(st)
    st.header("Review")
    if not runs:
        st.caption("No saved reviews yet. The reviewer runs one first; it is saved automatically.")
    else:
        ids = [r["id"] for r in runs]
        current = (st.session_state.get("result") or {}).get("pid")  # the review open on the reviewer screen, same session
        default = next((i for i, r in enumerate(runs) if r["project_id"] == current), 0)
        if st.query_params.get("open", "").isdigit() and int(st.query_params["open"]) in ids:
            default = ids.index(int(st.query_params["open"]))
        run_id = st.selectbox("Saved review", ids, index=default, format_func=lambda i: next(
            f"{r['name']} · {r['docs']} contract(s)" for r in runs if r["id"] == i))
        st.button("Refresh", help="Reloads the review, to pick up questions the reviewer has just saved.", use_container_width=True)

if not runs:
    st.info("There is nothing to review yet. Ask the reviewer to run a review, then open this page again.")
    st.stop()

run = next(r for r in runs if r["id"] == run_id)
pid, cats = run["project_id"], run["categories"]
docs = load_results(store, pid, cats)
asked = [(d, f) for d in docs for f in d["findings"] if f["question"] and f["review"] != "removed"]
count = {k: sum(1 for _, f in asked if f["qstate"] == k) for k in (OPEN, ANSWERED, RESOLVED)}
gaps = [(d, c) for d in docs for c in cats if d["categories"][c] != FOUND]
kpi_row(st, [(count[OPEN], "Open question" if count[OPEN] == 1 else "Open questions", "waiting for your answer", count[OPEN] > 0),
             (count[ANSWERED] + count[RESOLVED], "Answered", None, False),
             (len(gaps), "Unconfirmed categor" + ("y" if len(gaps) == 1 else "ies"), "not found or failed", len(gaps) > 0)])
st.sidebar.download_button("Download questions CSV", questions_csv_text(store, pid), file_name="questions_for_senior_lawyer.csv",
                           mime="text/csv", help="Only the findings the reviewer asked about, with the answers so far.")
st.sidebar.download_button("Download full table CSV", csv_text(store, pid), file_name="clause_review.csv", mime="text/csv",
                           help="The reviewer's whole table, with her review marks, questions and your answers.")

tab_q, tab_c, tab_g = st.tabs([f"Questions ({len(asked)})", "By clause", f"Unconfirmed ({len(gaps)})"])

with tab_q:
    if not asked:
        st.info("No questions yet. When the reviewer flags a finding, it appears here with the passage.")
    show = st.radio("Show", ["Needs my answer", "Answered", "All"], horizontal=True, label_visibility="collapsed")
    wanted = {"Needs my answer": (OPEN,), "Answered": (ANSWERED, RESOLVED), "All": (OPEN, ANSWERED, RESOLVED)}[show]
    for d, f in sorted((x for x in asked if x[1]["qstate"] in wanted), key=lambda x: (x[1]["qstate"] != OPEN, x[0]["id"], x[1]["id"])):
        with st.container(border=True):
            st.caption(f"{d['name']} · {f['category']} · Page {f['page']} · reviewer marked it "
                       f"{'not yet reviewed' if f['review'] == 'pending' else f['review']}")
            st.markdown("> " + md_escape(f["quote"]))
            st.markdown(f'<span class="chip {STATE_CHIP[f["qstate"]]}">{STATE_LABEL[f["qstate"]]}</span>', unsafe_allow_html=True)
            st.markdown("**Question:** " + md_escape(f["question"]))
            key = f"ans{f['id']}"
            st.text_area("Your answer", value=f["answer"] or "", key=key, height=90, label_visibility="collapsed",
                         placeholder="Your answer for the reviewer. Saving empty text takes an answer back.")
            st.button("Save answer", key=f"save{f['id']}", type="primary" if f["qstate"] == OPEN else "secondary",
                      on_click=answer, args=(f["id"], key))
    if asked and not any(x[1]["qstate"] in wanted for x in asked):
        st.caption("Nothing here.")

with tab_c:
    pick = st.selectbox("Clause category", [c for c in CATEGORIES if c in cats])
    st.caption("Every contract in this review, with what the reviewer's tool found for this category. Removed findings are left out.")
    for d in docs:
        status = d["categories"][pick] or "Failed to process"
        with st.container(border=True):
            st.markdown(category_heading(d["name"], status, d["reviewed"][pick]), unsafe_allow_html=True)
            for f in (x for x in d["findings"] if x["category"] == pick and x["review"] != "removed"):
                st.caption(f"Page {f['page']} · {'Not yet reviewed' if f['review'] == 'pending' else f['review'].capitalize()}"
                           + (" · has a question" if f["question"] else ""))
                st.markdown("> " + md_escape(f["quote"]))
            if status != FOUND:
                st.caption("Nothing confirmed. An empty result is not proof the clause is absent: ask for a manual check.")

with tab_g:
    if not gaps:
        st.success("Every category in every contract has at least one finding.")
    else:
        st.caption("Categories nobody has confirmed. These are the ones to ask the reviewer to check by hand.")
    for d, c in gaps:
        st.markdown(category_heading(f"{d['name']} · {c}", d["categories"][c] or "Failed to process", d["reviewed"][c]),
                    unsafe_allow_html=True)

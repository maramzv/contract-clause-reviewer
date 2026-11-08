"""Streamlit review screen: upload contracts, choose categories, see each finding with its quotation, page and status.

Run:  streamlit run app.py
Environment: CLAUSE_PROVIDER (mock by default), CLAUSE_DB (SQLite file, default review.db), plus the provider and
spend-limit variables described in the README.
"""
import os
import tempfile
import time
from pathlib import Path

import streamlit as st

from clause_review.categories import CATEGORIES
from clause_review.envfile import load_env
from clause_review.export import csv_text
from clause_review.pipeline import run_review
from clause_review.providers import BudgetExceeded, get_provider
from clause_review.store import FAILED, FOUND, NOT_FOUND, Store
from clause_review.view import load_results, md_escape

load_env()  # use the key and spend limit from .env, if there is one
ICON = {FOUND: "✅", NOT_FOUND: "⚠️", FAILED: "❌"}
DB_PATH = os.environ.get("CLAUSE_DB", "review.db")

st.set_page_config(page_title="Contract clause review", layout="wide")
st.title("Contract clause review")
st.caption("Every finding is a quotation found word for word in the contract. "
           "A category with no verified finding is flagged for you to check, never left blank.")


@st.cache_resource
def get_store():
    return Store(DB_PATH)


def act(finding_id, state):
    get_store().set_review(finding_id, state)


def run(files, categories):
    """Write the uploads to a temp folder (one subfolder each, so equal file names do not collide) and review them."""
    store, provider = get_store(), get_provider()
    project = time.strftime("Review %Y-%m-%d %H:%M:%S")
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, f in enumerate(files):
            d = Path(tmp) / str(i)
            d.mkdir()
            p = d / Path(f.name).name
            p.write_bytes(f.getvalue())
            paths.append(p)
        pid = run_review(store, project, paths, provider, categories=categories,
                         workers=int(os.environ.get("CLAUSE_WORKERS", "1")))
    return pid, provider


provider_name = os.environ.get("CLAUSE_PROVIDER", "mock")
if provider_name == "mock":
    st.warning("Mock provider: this is an offline demo that finds clauses with keyword rules, not a real model.")

with st.sidebar:
    st.header("New review")
    chosen = st.multiselect("Clause categories", list(CATEGORIES), default=list(CATEGORIES))
    files = st.file_uploader("Contracts (PDF or text)", type=["pdf", "txt"], accept_multiple_files=True)
    go = st.button("Run review", type="primary", disabled=not files or not chosen)

if go:
    try:
        with st.spinner("Reading contracts and checking quotations..."):
            pid, provider = run(files, chosen)
        st.session_state["result"] = {"pid": pid, "categories": chosen, "usage": provider.meter.summary()}
    except BudgetExceeded as e:
        st.session_state.pop("result", None)
        st.error(f"Stopped at the spending limit: {e}. Responses already paid for are saved and are reused on a rerun.")
    except Exception as e:  # never show a half-finished table as if it were complete
        st.session_state.pop("result", None)
        st.error(f"The review could not be completed: {e}")

res = st.session_state.get("result")
if not res:
    st.info("Choose categories, upload one or more contracts and select Run review.")
    st.stop()

docs = load_results(get_store(), res["pid"], res["categories"])
all_f = [f for d in docs for f in d["findings"]]
n_check = sum(1 for d in docs for c in res["categories"] if d["categories"][c] != FOUND)
tally = {k: sum(1 for f in all_f if f["review"] == k) for k in ("pending", "accepted", "removed")}
st.subheader(f"{len(docs)} contract(s), {len(all_f) - tally['removed']} finding(s), {n_check} category check(s) for you")
st.caption(f"Reviewed: {tally['accepted']} accepted, {tally['removed']} removed, {tally['pending']} not yet reviewed. "
           f"Model usage: {res['usage']}")
st.sidebar.download_button("Download CSV", csv_text(get_store(), res["pid"]), file_name="clause_review.csv",
                           mime="text/csv", help="Accepted and not-yet-reviewed findings, plus every category still to check.")

for d in docs:
    found = sum(1 for c in res["categories"] if d["categories"][c] == FOUND)
    label = f"{d['name']}  ·  {found} of {len(res['categories'])} categories found"
    if d["status"] == "failed":
        label = f"{d['name']}  ·  Failed to process"
    with st.expander(label, expanded=len(docs) <= 3):
        if d["status"] == "failed":
            st.error(f"Failed to process: {d['error']}")
        for c in res["categories"]:
            status = d["categories"][c] or FAILED
            st.markdown(f"**{ICON.get(status, '❌')} {c}** — {status}")
            for f in (x for x in d["findings"] if x["category"] == c):
                removed = f["review"] == "removed"
                with st.container(border=True):
                    st.caption(f"Page {f['page']} · {f['review'].capitalize() if f['review'] != 'pending' else 'Not yet reviewed'}")
                    quote = md_escape(f["quote"])
                    st.markdown("> " + (f"~~{quote}~~" if removed else quote))
                    b1, b2, _ = st.columns([1, 1, 6])
                    if removed:
                        b1.button("Restore", key=f"restore{f['id']}", on_click=act, args=(f["id"], "pending"))
                    else:
                        b1.button("Accept", key=f"accept{f['id']}", on_click=act, args=(f["id"], "accepted"),
                                  type="secondary" if f["review"] == "accepted" else "primary",
                                  disabled=f["review"] == "accepted")
                        b2.button("Remove", key=f"remove{f['id']}", on_click=act, args=(f["id"], "removed"))

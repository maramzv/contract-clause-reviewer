"""Shared by the reviewer screen (app.py) and the senior lawyer dashboard (pages/): one SQLite store, so a question
Maya saves is the one the senior lawyer sees and his answer is the one she sees."""
import os

import streamlit as st

from clause_review.envfile import load_env
from clause_review.store import Store

load_env()
DB_PATH = os.environ.get("CLAUSE_DB", "review.db")


@st.cache_resource
def get_store():
    return Store(DB_PATH)


def result_actions(st, store, res):
    """Refresh and Download CSV at the bottom of the sidebar, the same on every junior associate screen."""
    from clause_review.export import csv_text
    st.sidebar.button("Refresh", help="Reloads the results, to pick up answers the senior lawyer has just saved.",
                      use_container_width=True)
    st.sidebar.download_button("Download CSV", csv_text(store, res["pid"]), file_name="clause_review.csv",
                               mime="text/csv", help="Accepted and not-yet-reviewed findings, plus every category still to check.")


def resume_latest(st, store):
    """Coming back to the app: open the latest saved review, unless one is already open or the person chose to start a new
    one. Returns the open review's session entry, or None when there is none yet."""
    if "result" in st.session_state or st.session_state.get("new_review"):
        return st.session_state.get("result")
    runs = store.list_runs()
    if not runs:
        return None
    r = runs[0]
    st.session_state["result"] = {"pid": r["project_id"], "categories": r["categories"],
                                  "provider": f"{r['provider']} (saved run)", "usage": r["usage"] or ""}
    return st.session_state["result"]


def _start_new_review():
    st.session_state["new_review"] = True
    st.session_state.pop("result", None)
    st.switch_page("app.py")


def new_review_button(container):
    """One button that goes to the start screen, from any junior associate screen. `container` is where to draw it
    (st.sidebar, or a container reserved in the sidebar so it can be filled in later)."""
    container.button("New review", icon=":material/add:", on_click=_start_new_review, use_container_width=True,
                      help="Pick clauses and contracts and run another review. The current one stays in Saved runs.")

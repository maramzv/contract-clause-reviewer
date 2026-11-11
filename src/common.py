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
    """Download CSV in the sidebar, the same on every junior associate screen, and the refresh icon in the page corner."""
    from clause_review.export import csv_text
    refresh_corner(st)
    st.sidebar.download_button("Download CSV", csv_text(store, res["pid"]), file_name="clause_review.csv",
                               mime="text/csv")  # no hover text


def resume_latest(st, store):
    """Coming back to the app: open the latest saved review, once per visit. After that the person is in charge: if they
    closed or lost the open review, it does not reopen by itself. Returns the open review's session entry, or None."""
    if st.session_state.get("_resumed") or "result" in st.session_state:
        st.session_state["_resumed"] = True
        return st.session_state.get("result")
    st.session_state["_resumed"] = True
    runs = store.list_runs()
    if not runs:
        return None
    r = runs[0]
    st.session_state["result"] = {"pid": r["project_id"], "categories": r["categories"],
                                  "provider": f"{r['provider']} (saved run)", "usage": r["usage"] or ""}
    return st.session_state["result"]


def _start_new_review():
    st.session_state["new_review"] = True  # app.py opens the New review section in the sidebar
    st.switch_page("app.py")


def new_review_button(container):
    """A button on the other junior associate screens that goes to the Review page with the New review section open."""
    container.button("New review", icon=":material/add:", on_click=_start_new_review, use_container_width=True,
                      help="Pick clauses and contracts and run another review. The current one stays in Saved runs.")


def refresh_corner(st):
    """A refresh icon fixed in the top-right corner of a dashboard (not in the left nav). Pressing it reruns the page, which
    reloads the results from the saved review, so answers the other person just saved show up."""
    with st.container(key="refresh_corner"):
        st.button("", icon=":material/refresh:", key="refresh_btn", help="Refresh: reload the latest answers and decisions.")

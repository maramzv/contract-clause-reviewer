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

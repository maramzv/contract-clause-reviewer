"""Review: one passage at a time with the contract beside it. The Junior Associate gets here from the Overview (the home
screen): a cell opens that clause, Continue reviewing opens the first passage still to decide."""
import os

import streamlit as st

from clause_review.view import load_results
from common import get_store, new_review_button, resume_latest, result_actions
from theme import apply_theme, brand, marquee, views
import workspace
import workspace_html

st.set_page_config(page_title="Clautra · Review", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
store = get_store()

with st.sidebar:
    brand(st)
    views(st, on_review=True)  # the Review belongs to the Junior Associate

res = resume_latest(st, store)  # opened directly: the latest saved review
if not res:
    st.info("There is nothing to review yet. Start a review from the Overview first.")
    st.page_link("app.py", label="Go to the Overview", icon=":material/grid_view:")
    st.stop()

new_review_button(st.sidebar)
result_actions(st, store, res)
docs = load_results(store, res["pid"], res["categories"])
if st.session_state.get("dev_mode"):
    st.caption(f"Model: {res.get('provider', '?')}. Usage: {res['usage']}")
(workspace if os.environ.get("CLAUSE_WORKSPACE") == "classic" else workspace_html).render(st, store, res, docs)

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

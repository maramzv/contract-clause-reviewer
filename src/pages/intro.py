"""/intro: the slides as plain images, one under the other, with no app chrome. The images are in static/slides/deck (01.png, 02.png,
...) and are sent through st.image, so this works on any host with no static-file setting. To change the deck, replace those files."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Clautra · Slides", page_icon="static/brand/clautra-mark-transparent.png", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.block-container { max-width: 1280px !important; padding-top: 1rem !important; }
[data-testid="stImage"] img { border-radius: 6px; box-shadow: 0 2px 14px rgba(20,39,55,.25); }
[data-testid="stElementToolbar"] { display: none !important; }
</style>""", unsafe_allow_html=True)

for p in sorted((Path(__file__).resolve().parent.parent / "static" / "slides" / "deck").glob("*.png")):
    st.image(str(p), use_container_width=True)

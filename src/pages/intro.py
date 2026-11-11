"""/intro: the slide deck as plain images, one under the other, full width with no app chrome. The images are in static/slides/deck
(01.png, 02.png, ...). To change the deck, replace those files."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Clautra · Slides", page_icon="static/brand/clautra-mark-transparent.png", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.block-container { max-width: 1280px !important; padding-top: 1rem !important; }
.slide { width: 100%; display: block; margin: 0 0 18px; border-radius: 6px; box-shadow: 0 2px 14px rgba(20,39,55,.25); }
</style>""", unsafe_allow_html=True)

slides = sorted((Path(__file__).resolve().parent.parent / "static" / "slides" / "deck").glob("*.png"))
st.markdown("".join(f'<img class="slide" src="/app/static/slides/deck/{p.name}" alt="Slide {i}" loading="{"eager" if i < 3 else "lazy"}">'
                    for i, p in enumerate(slides, 1)), unsafe_allow_html=True)
st.markdown("[Download the slides as a PDF](/app/static/slides/deck.pdf)")

"""/intro: the slide deck, opened full width with no app chrome. The deck is a plain PDF in static/slides (served by Streamlit's
static folder) and shown in a frame, so a new deck is just a new file copied over deck.pdf."""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clautra · Slides", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.block-container { padding: .8rem 1.2rem 0 !important; max-width: 100% !important; }
</style>""", unsafe_allow_html=True)

components.html('<style>html,body{margin:0;height:100%}</style><iframe src="/app/static/slides/deck.pdf" style="width:100%;height:100%;border:0;border-radius:8px"></iframe>', height=850)
st.markdown("[Open the slides as a PDF](/app/static/slides/deck.pdf)")

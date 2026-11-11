"""/intro: the slides, opened full width with no app chrome. Two decks: the short plain-language intro, and the results deck.
Both are plain files in static/slides (served by Streamlit's static folder), shown in a frame, so a slide can be replaced by
copying a new file over the old one."""
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clautra · Intro", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.block-container { padding: 1rem 1.2rem 0 !important; max-width: 100% !important; }
</style>""", unsafe_allow_html=True)

def _frame(src):
    return (f'<style>html,body{{margin:0;height:100%}}</style><iframe src="{src}" style="width:100%;height:100%;border:0;border-radius:8px"></iframe>')


intro, deck = st.tabs(["Intro slides", "Results deck"])
with intro:
    components.html(_frame("/app/static/slides/intro.html"), height=780)
    st.markdown("[Open the intro full screen](/app/static/slides/intro.html)")
with deck:
    components.html(_frame("/app/static/slides/results-deck.pdf"), height=780)
    st.markdown("[Open the results deck as a PDF](/app/static/slides/results-deck.pdf)")

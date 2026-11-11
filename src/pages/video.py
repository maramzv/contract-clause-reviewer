"""/video: the demo video, full width. Drop the chosen file in static/video as clautra_demo.mp4 (and clautra_demo.vtt for captions)
and push: this page shows it. Until then it says the video is coming."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Clautra · Video", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #0d1b27 !important; }
h1 { color: #F3EFE6 !important; font-family: Georgia, 'Times New Roman', serif !important; font-weight: 400 !important; text-align: center; }
.block-container { max-width: 1180px !important; }
video { width: 100%; border-radius: 8px; background: #0d1b27; box-shadow: 0 10px 40px rgba(0,0,0,.5); }
</style>""", unsafe_allow_html=True)

st.title("Clautra")
here = Path(__file__).resolve().parent.parent / "static" / "video"
if (here / "clautra_demo.mp4").is_file():
    # st.video sends the file through Streamlit itself, so it works on any host with no static-file setting
    st.video(str(here / "clautra_demo.mp4"), subtitles=str(here / "clautra_demo.vtt") if (here / "clautra_demo.vtt").is_file() else None)
else:
    st.info("The demo video is on its way. Check back soon.")

"""/video: the demo video, full width. Drop the chosen file in static/video as clautra_demo.mp4 (and clautra_demo.vtt for captions)
and push: this page shows it. Until then it says the video is coming."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clautra · Video", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #0d1b27 !important; }
.block-container { max-width: min(1500px, calc((100vh - 2rem) * 1.6)) !important; padding: 1rem 1rem 0 !important; }  /* the biggest 16:10 picture that fits the window, no scrolling */
video { width: 100%; border-radius: 8px; background: #0d1b27; box-shadow: 0 10px 40px rgba(0,0,0,.5); }
/* the video has no sound, so no volume button */
video::-webkit-media-controls-mute-button, video::-webkit-media-controls-volume-slider, video::-webkit-media-controls-volume-control-container { display: none !important; }
</style>""", unsafe_allow_html=True)

here = Path(__file__).resolve().parent.parent / "static" / "video"
if (here / "clautra_demo.mp4").is_file():
    # st.video sends the file through Streamlit itself, so it works on any host with no static-file setting
    st.video(str(here / "clautra_demo.mp4"), subtitles=str(here / "clautra_demo.vtt") if (here / "clautra_demo.vtt").is_file() else None)
    # Play and the timeline stay; the browser's extras (download, picture-in-picture, casting, speed, right-click menu; fullscreen stays) go.
    # Streamlit draws the <video> itself, so this small script sets those attributes on it (it also catches a re-draw).
    components.html("""<script>
    const d = window.parent.document;
    function lock() {
      d.querySelectorAll('video').forEach(v => {
        v.setAttribute('controlsList', 'nodownload noplaybackrate');
        v.setAttribute('disablepictureinpicture', ''); v.disablePictureInPicture = true;
        v.setAttribute('disableremoteplayback', ''); v.disableRemotePlayback = true;
        if (!v.__locked) { v.__locked = true; v.addEventListener('contextmenu', e => e.preventDefault()); }
      });
    }
    lock();
    new MutationObserver(lock).observe(d.body, {childList: true, subtree: true});
    </script>""", height=0)
else:
    st.info("The demo video is on its way. Check back soon.")

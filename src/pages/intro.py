"""/intro: the slides as a slideshow. One slide at a time; arrow keys, space, a clicker or a click move through it (no on-screen arrows), and
the corner icon (or F) fills the screen. The slide images are in static/slides/deck (01.png, 02.png, ...); replace those files to change the deck.
The images are embedded in the page itself, so no static-file setting is needed."""
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clautra · Slides", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #0d1b27 !important; }
.block-container { max-width: 100% !important; padding: .6rem 1rem 0 !important; }
</style>""", unsafe_allow_html=True)

_DIR = Path(__file__).resolve().parent.parent / "static" / "slides" / "deck"
_SHOW = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#0d1b27;font-family:system-ui,-apple-system,Segoe UI,sans-serif;overflow:hidden}
#show{position:relative;width:100%;height:100%;background:#0d1b27;display:flex;flex-direction:column;user-select:none}
#stage{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:10px 0;position:relative;cursor:pointer}
#stage img{max-width:100%;max-height:100%;aspect-ratio:16/9;object-fit:contain;border-radius:6px;box-shadow:0 6px 30px rgba(0,0,0,.5);opacity:1;transition:opacity .35s ease}
#stage img.out{opacity:0}
#bar{flex:none;display:flex;align-items:center;gap:14px;padding:6px 14px 10px;color:rgba(217,210,192,.6);font-size:12px}
#dots{display:flex;gap:7px;flex:1;justify-content:center}
#dots i{width:9px;height:9px;border-radius:50%;background:rgba(243,239,230,.3);cursor:pointer;transition:background .2s,transform .2s}
#dots i.on{background:#C4A972;transform:scale(1.25)}
#count{min-width:56px;font-variant-numeric:tabular-nums}
#present{border:0;background:transparent;color:rgba(243,239,230,.45);padding:2px;width:22px;height:22px;cursor:pointer;display:grid;place-items:center}
#present:hover{color:#C4A972}#present svg{width:16px;height:16px}
#show:fullscreen #bar{display:none}
#show:fullscreen #stage{padding:0}
#show:fullscreen #stage img{box-shadow:none;border-radius:0}
#show:fullscreen{cursor:none}#show:fullscreen:hover{cursor:default}
</style></head><body>
<div id="show"><div id="stage" title="Click for the next slide"><img id="img" alt=""></div>
<div id="bar"><span id="count"></span><div id="dots"></div><button id="present" aria-label="Full screen" title="Full screen (F)"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="square"><path d="M1 5V1h4M11 1h4v4M15 11v4h-4M5 15H1v-4"/></svg></button></div></div>
<script>
const S = __SLIDES__; let i = 0; const $ = id => document.getElementById(id), img = $('img'), show = $('show');
$('dots').innerHTML = S.map((_, k) => `<i data-k="${k}" title="Slide ${k + 1}"></i>`).join('');
S.forEach(s => { const p = new Image(); p.src = s; });   // load them all up front so a change of slide never waits
function go(n, instant) {
  n = Math.max(0, Math.min(S.length - 1, n)); if (n === i && img.src) return;
  const swap = () => { i = n; img.src = S[i]; img.alt = 'Slide ' + (i + 1); img.classList.remove('out');
    $('count').textContent = (i + 1) + ' / ' + S.length;
    document.querySelectorAll('#dots i').forEach((d, k) => d.classList.toggle('on', k === i)); };
  if (instant) return swap(); img.classList.add('out'); setTimeout(swap, 230);
}
function present() { if (document.fullscreenElement) document.exitFullscreen(); else if (show.requestFullscreen) show.requestFullscreen().catch(() => {}); }
const keys = e => {
  if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(e.key)) { go(i + 1); e.preventDefault(); }
  else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(e.key)) { go(i - 1); e.preventDefault(); }
  else if (e.key === 'Home') go(0); else if (e.key === 'End') go(S.length - 1);
  else if (e.key === 'f' || e.key === 'F' || e.key === 'p' || e.key === 'P') present();
};
addEventListener('keydown', keys);
try { if (parent.__clautraKeys) parent.removeEventListener('keydown', parent.__clautraKeys); parent.__clautraKeys = keys; parent.addEventListener('keydown', keys); } catch (_) {}
$('present').onclick = present;
$('stage').onclick = e => { const r = $('stage').getBoundingClientRect(); go(e.clientX - r.left > r.width / 2 ? i + 1 : i - 1); };
$('dots').onclick = e => { if (e.target.dataset.k) go(+e.target.dataset.k); };
go(0, true); window.focus();
</script></body></html>"""

slides = ["data:image/png;base64," + base64.b64encode(p.read_bytes()).decode() for p in sorted(_DIR.glob("*.png"))]
components.html(_SHOW.replace("__SLIDES__", json.dumps(slides)), height=820)

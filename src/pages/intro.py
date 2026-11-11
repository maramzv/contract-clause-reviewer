"""/intro: the slides as a slideshow. One slide at a time; arrow keys, space, the on-screen arrows or a click move through it, and
Present (or F) fills the screen. The slide images are in static/slides/deck (01.png, 02.png, ...); replace those files to change the deck.
The images are embedded in the page itself, so no static-file setting is needed."""
import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Clautra · Slides", page_icon="static/brand/clautra-mark-transparent.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], header { display: none !important; }
.block-container { max-width: 100% !important; padding: .6rem 1rem 0 !important; }
</style>""", unsafe_allow_html=True)

_DIR = Path(__file__).resolve().parent.parent / "static" / "slides" / "deck"
_SHOW = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#0d1b27;font-family:system-ui,-apple-system,Segoe UI,sans-serif;overflow:hidden}
#show{position:relative;width:100%;height:100%;background:#0d1b27;display:flex;flex-direction:column;user-select:none}
#stage{flex:1;min-height:0;display:flex;align-items:center;justify-content:center;padding:10px 70px;position:relative;cursor:pointer}
#stage img{max-width:100%;max-height:100%;aspect-ratio:16/9;object-fit:contain;border-radius:6px;box-shadow:0 6px 30px rgba(0,0,0,.5);opacity:1;transition:opacity .35s ease}
#stage img.out{opacity:0}
.nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;border-radius:50%;border:1px solid rgba(243,239,230,.35);background:rgba(20,39,55,.75);color:#F3EFE6;font-size:24px;cursor:pointer;display:grid;place-items:center;transition:background .2s,opacity .2s}
.nav:hover{background:#A58A58}.nav:disabled{opacity:.25;cursor:default;background:rgba(20,39,55,.75)}
#prev{left:10px}#next{right:10px}
#bar{flex:none;display:flex;align-items:center;gap:14px;padding:8px 16px 12px;color:#d9d2c0;font-size:14px}
#dots{display:flex;gap:7px;flex:1;justify-content:center}
#dots i{width:9px;height:9px;border-radius:50%;background:rgba(243,239,230,.3);cursor:pointer;transition:background .2s,transform .2s}
#dots i.on{background:#C4A972;transform:scale(1.25)}
#count{min-width:56px;font-variant-numeric:tabular-nums}
#present{border:1px solid rgba(243,239,230,.4);background:transparent;color:#F3EFE6;border-radius:6px;padding:7px 16px;font:600 14px inherit;font-family:inherit;cursor:pointer}
#present:hover{background:#A58A58;border-color:#A58A58}
#show:fullscreen #bar{opacity:0;transition:opacity .4s;position:absolute;left:0;right:0;bottom:0}
#show:fullscreen:hover #bar{opacity:1}
#show:fullscreen #stage{padding:0 70px}
#show:fullscreen #stage img{box-shadow:none;border-radius:0}
#show:fullscreen{cursor:none}#show:fullscreen:hover{cursor:default}
</style></head><body>
<div id="show"><div id="stage" title="Click for the next slide"><img id="img" alt=""></div>
<button class="nav" id="prev" aria-label="Previous slide">&#8592;</button><button class="nav" id="next" aria-label="Next slide">&#8594;</button>
<div id="bar"><span id="count"></span><div id="dots"></div><button id="present">Present &#x26F6;</button></div></div>
<script>
const S = __SLIDES__; let i = 0; const $ = id => document.getElementById(id), img = $('img'), show = $('show');
$('dots').innerHTML = S.map((_, k) => `<i data-k="${k}" title="Slide ${k + 1}"></i>`).join('');
S.forEach(s => { const p = new Image(); p.src = s; });   // load them all up front so a change of slide never waits
function go(n, instant) {
  n = Math.max(0, Math.min(S.length - 1, n)); if (n === i && img.src) return;
  const swap = () => { i = n; img.src = S[i]; img.alt = 'Slide ' + (i + 1); img.classList.remove('out');
    $('count').textContent = (i + 1) + ' / ' + S.length; $('prev').disabled = i === 0; $('next').disabled = i === S.length - 1;
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
$('next').onclick = () => go(i + 1); $('prev').onclick = () => go(i - 1); $('present').onclick = present;
$('stage').onclick = e => { const r = $('stage').getBoundingClientRect(); go(e.clientX - r.left > r.width / 2 ? i + 1 : i - 1); };
$('dots').onclick = e => { if (e.target.dataset.k) go(+e.target.dataset.k); };
go(0, true); window.focus();
</script></body></html>"""

slides = ["data:image/png;base64," + base64.b64encode(p.read_bytes()).decode() for p in sorted(_DIR.glob("*.png"))]
components.html(_SHOW.replace("__SLIDES__", json.dumps(slides)), height=820)
st.caption("Arrow keys or space to move, F to fill the screen, Esc to leave.")

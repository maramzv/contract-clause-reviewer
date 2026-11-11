"""Clautra "Ink & Ivory" look for the review screen.

Colours, the heading font and the sidebar colours come from .streamlit/config.toml. This file adds what the config cannot:
paper and woven-navy textures, brushed-brass buttons, serif quotations, status chips and the page header. It draws only;
no pipeline logic lives here. Files it uses are in ./static (served at /app/static)."""
import html

INK, MIST, IVORY, BRASS, BRASS_DEEP, LINE = "#142737", "#B9C8D4", "#F3EFE6", "#A58A58", "#7A6334", "#D3CAB4"
SERIF = "'Latin Modern Roman', 'Cormorant Garamond', Georgia, 'Times New Roman', serif"
STATIC = "app/static"
LOCKUP = "static/brand/clautra-lockup-transparent.png"
MARK = "static/brand/clautra-mark-transparent.png"

CHIP_CLASS = {"Found": "chip-found", "Not found, review required": "chip-miss", "Failed to process": "chip-fail"}

_CSS = """
<style>
:root { --ink:%(INK)s; --mist:%(MIST)s; --ivory:%(IVORY)s; --brass:%(BRASS)s; --brass-deep:%(BRASS_DEEP)s; --line:%(LINE)s; }

/* surfaces: warm paper for reading, woven navy for navigation */
.stApp { background-color:var(--ivory); background-image:url(%(STATIC)s/brand/texture-ivory.jpg); background-size:372px auto; }
[data-testid="stHeader"] { background:transparent; }
section[data-testid="stSidebar"] > div:first-child { background-color:var(--ink); background-image:url(%(STATIC)s/brand/texture-navy.jpg);
  background-size:372px auto; border-right:1px solid #0c1823; }
[data-testid="stSidebarContent"] { padding-top:.4rem; }
.block-container { padding-top:1.6rem; max-width:1600px; }


/* corner logo: the lockup is used as a mask over brushed brass with a soft sheen, so it gleams like the metal version */
[data-testid="stSidebarHeader"] { height:1.6rem; min-height:0; padding:0 .5rem; margin:0; }
.brand { display:flex; justify-content:center; padding:1.8rem 0 1.6rem; margin:-.2rem -1.9rem 1.1rem -1.9rem;
  background:radial-gradient(ellipse 80%% 70%% at 50%% 38%%, rgba(46,80,108,.55), rgba(10,24,36,.0) 72%%), rgba(8,20,31,.55);
  border-bottom:1px solid rgba(196,169,114,.45); filter:drop-shadow(0 1px 1px rgba(0,0,0,.65)); }
.st-key-brandlink { position:relative; z-index:5; height:0; margin-bottom:-1rem; }
.st-key-brandlink a { position:absolute; left:-1.9rem; right:-3rem; top:-13.6rem; height:12.6rem; opacity:0; cursor:pointer; }
.brand-stack { display:flex; flex-direction:column; align-items:center; gap:30px; }
.gold { background-image:linear-gradient(112deg, rgba(255,244,214,0) 18%%, rgba(255,244,214,.7) 40%%, rgba(255,244,214,0) 62%%), url(%(STATIC)s/brand/texture-brass.jpg);
  background-size:100%% 100%%, cover; background-position:center; filter:brightness(1.35) saturate(1.05); }
.brand-mark { width:92px; aspect-ratio:977 / 1078;
  -webkit-mask:url(%(STATIC)s/brand/clautra-mark-trim.png) center / contain no-repeat; mask:url(%(STATIC)s/brand/clautra-mark-trim.png) center / contain no-repeat; }
.brand-word { width:172px; aspect-ratio:1662 / 201;
  -webkit-mask:url(%(STATIC)s/brand/clautra-wordmark-trim.png) center / contain no-repeat; mask:url(%(STATIC)s/brand/clautra-wordmark-trim.png) center / contain no-repeat; }

/* dropdown options: let long contract names wrap instead of being cut off */
/* long names (dropdown options, selected chips, contract headings): clipped with an ellipsis, and on hover they slide
   sideways so the whole name can be read. The script that sets --shift is in marquee() below. */
[role="option"] div, span[data-baseweb="tag"] > span:first-child { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
[role="option"] { padding-top:.5rem; padding-bottom:.5rem; }
span[data-baseweb="tag"] { max-width:100%%; }
.clautra-marquee { text-overflow:clip !important; animation:clautra-slide var(--dur, 6s) ease-in-out infinite alternate; }
@keyframes clautra-slide { 0%%, 14%% { text-indent:0; } 86%%, 100%% { text-indent:var(--shift, 0px); } }
@media (prefers-reduced-motion: reduce) { .clautra-marquee { animation:none; text-overflow:ellipsis !important; } }

/* KPI row: the three headline numbers of a review */
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:1rem; margin:.3rem 0 1.1rem; }
.kpi { background:rgba(255,253,248,.78); border:1px solid var(--line); border-top:3px solid var(--brass); border-radius:3px; padding:.75rem 1.1rem .85rem; }
.kpi .num { font-family:%(SERIF)s; font-size:2.9rem; line-height:1; color:var(--ink); }
.kpi .lbl { margin-top:.35rem; font-size:.72rem; letter-spacing:.2em; text-transform:uppercase; font-weight:600; color:var(--brass-deep); }
.kpi .note { margin-top:.15rem; font-size:.8rem; color:#4b5f70; }
.kpi.flag { background:#EFE2BF; border-color:#D9C38C; border-top-color:var(--brass-deep); }
.kpi.flag .lbl { color:#5c4719; }

/* user / dev mode switch, pinned to the top-right corner */
.st-key-dev_mode { position:fixed; top:.55rem; right:3.4rem; z-index:1000002; background:rgba(243,239,230,.94);
  border:1px solid var(--line); border-radius:999px; padding:.15rem .9rem .15rem .6rem; box-shadow:0 1px 3px rgba(20,39,55,.15); }
.st-key-dev_mode label p { font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; font-weight:600; color:var(--ink); }

/* screen switch under the logo: serif labels, brass icons, the current screen marked with a brass rule */
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] { border-radius:3px; border-left:3px solid transparent; padding-left:.55rem; }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p { font-family:%(SERIF)s; font-size:1.12rem; color:var(--ivory); }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"] { color:#C4A972; }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover { background:rgba(196,169,114,.12); }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p { color:#E4D3A6; }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] { background:rgba(196,169,114,.16); border-left-color:#C4A972; }
section[data-testid="stSidebar"] [class*="st-key-nav_junior_on"] [data-testid="stPageLink-NavLink"] { background:rgba(196,169,114,.16); border-left-color:#C4A972; }
section[data-testid="stSidebar"] [class*="st-key-nav_junior_on"] [data-testid="stPageLink-NavLink"] p { color:#E4D3A6; }
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p { color:#E4D3A6; }

/* review workspace: contract title, the contract text beside the findings */
.ws-title { font-family:%(SERIF)s; font-size:1.6rem; line-height:1.1; color:var(--ink); margin:.2rem 0 .05rem 0; }
.ws-sub { font-size:.8rem; color:#4b5f70; margin-bottom:.35rem; }
.ws-doc-title { font-family:%(SERIF)s; font-size:1.3rem; color:var(--ink); line-height:1.2; }
.ws-doc-file { font-size:.8rem; color:#4b5f70; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%%; }
.docwrap { display:flex; gap:.6rem; }
.doc { flex:1; min-width:0; background:rgba(255,253,248,.97); border:1px solid var(--line); border-radius:4px; padding:1.6rem 2.3rem; height:72vh; overflow:auto;
  font-family:%(SERIF)s; font-size:1.04rem; line-height:1.5; color:#5d6c78; }
.doc p { margin:0 0 .8rem 0; }
.doc mark { background:#E4D3A6; color:#14202b; padding:.1rem 0; box-shadow:0 0 0 3px #E4D3A6; border-radius:2px; }
.doc .doc-gap { color:#7a8a97; text-align:center; letter-spacing:.3em; }
.doc hr { border:0; border-top:1px solid var(--line); margin:.9rem 0; }
.strip { position:relative; width:14px; flex:none; background:#EAE4D5; border-radius:7px; }
.strip .tick { position:absolute; left:3px; width:8px; height:8px; border-radius:50%%; background:#2F5F82; }
.strip .tick.now { left:1px; width:12px; height:12px; background:#C4A972; border:2px solid var(--ink); box-sizing:border-box; }

/* the finding on the left: the quotation on a mist band, then the answer panel */
.passage-no { font-size:.78rem; color:#4b5f70; margin:.35rem 0 .2rem 0; }
.quote { background:#DCE4EB; border-radius:3px; padding:.65rem .9rem; font-family:%(SERIF)s; font-size:1.08rem; line-height:1.36; color:#0f1f2c; }
.quote.removed { background:transparent; color:#6b7a87; text-decoration:line-through; padding:.2rem 0; }
[class*="st-key-qa"] { background:#EAF0F4; border-radius:4px; padding:.7rem .9rem; margin-top:.5rem; gap:.35rem !important; }
[data-testid="stMain"] [data-testid="stButtonGroup"], [data-testid="stMain"] [data-testid="stButtonGroup"] > div { flex-wrap:wrap !important; row-gap:.4rem; }
[data-testid="stMain"] [data-testid="stButtonGroup"] button { border:1px solid #A58A58 !important; background:transparent !important; color:var(--ink) !important; border-radius:999px; }
[data-testid="stMain"] [data-testid="stButtonGroup"] button[aria-checked="true"] { border-color:var(--ink) !important; background:var(--ink) !important; color:var(--ivory) !important; }
[data-testid="stMain"] [data-testid="stButtonGroup"] button p { color:inherit !important; font-size:.82rem; }
[data-testid="stMain"] [data-testid="stButtonGroup"] button { min-height:1.9rem; padding:.1rem .7rem; }
/* slimmer buttons in the workspace, as in the mockup */
[data-testid="stMain"] [data-testid="stHorizontalBlock"] button { min-height:2.3rem; padding:.15rem .6rem; }
[data-testid="stMain"] [data-testid="stHorizontalBlock"] button p { font-size:.88rem; }

/* overview matrix: a cell is a button; its key says what it holds (cellfound, cellaccepted, cellcheck, cellfailed) */
[data-testid="stMain"] [class*="st-key-cell"] button { min-height:2rem; padding:.15rem .6rem; font-size:.8rem; font-weight:600; border-radius:5px; border:0 !important; width:100%%; }
[data-testid="stMain"] [class*="st-key-cellfound_"] button { background:var(--mist) !important; color:#10202d !important; }
[data-testid="stMain"] [class*="st-key-cellaccepted_"] button { background:#2F5F82 !important; color:#fff !important; }
[data-testid="stMain"] [class*="st-key-cellcheck_"] button { background:#EBD8B0 !important; color:#57431a !important; }
[data-testid="stMain"] [class*="st-key-cellfailed_"] button { background:#E6C7C1 !important; color:#6a2a22 !important; }
[data-testid="stMain"] [class*="st-key-cell"] button p { color:inherit !important; }
[data-testid="stMain"] [class*="st-key-cell"] button:hover { filter:brightness(.95); outline:2px solid var(--brass-deep); }
.ov-key { display:flex; flex-wrap:wrap; gap:.55rem 1.4rem; align-items:center; margin:.2rem 0 1rem; padding:.7rem .9rem; background:#FFFDF8; border:1px solid var(--line); border-radius:4px; font-size:.88rem; color:var(--ink); }
.ov-key-i { display:inline-flex; align-items:center; gap:.5rem; }
.ov-sw { display:inline-block; min-width:3.4rem; text-align:center; padding:.12rem .6rem; border-radius:4px; font-size:.82rem; font-weight:600; }
.ov-sw.found { background:var(--mist); color:#10202d; } .ov-sw.accepted { background:#2F5F82; color:#fff; }
.ov-sw.check { background:#EBD8B0; color:#57431a; } .ov-sw.failed { background:#E6C7C1; color:#6a2a22; }
.ov-sw.q { min-width:0; background:transparent; border:1px solid var(--ink); border-radius:50%%; padding:0 .5rem; }
.ov-head { font-size:.8rem; font-weight:600; color:var(--ink); padding:.3rem 0; border-bottom:1px solid var(--line); }
.ov-title { font-family:%(SERIF)s; font-size:1.05rem; line-height:1.15; color:var(--ink); }
.ov-party { font-size:.76rem; color:#4b5f70; }

/* page header */
.hero { margin:0 0 1.4rem 0; }
.hero .eyebrow { font-size:.7rem; letter-spacing:.26em; text-transform:uppercase; color:var(--brass-deep); font-weight:600; }
.hero h1 { font-family:%(SERIF)s; font-weight:400; font-size:3rem; line-height:1.05; margin:.35rem 0 .15rem 0; padding:0; color:var(--ink); }
.hero .tag { font-family:%(SERIF)s; font-style:italic; font-size:1.35rem; color:var(--ink); margin:0 0 .9rem 0; }
.hero .rule { height:2px; border:0; margin:0 0 .8rem 0; background:linear-gradient(90deg,var(--brass),rgba(165,138,88,.15) 70%%,transparent); }
.hero .lede { font-size:.98rem; color:#35495a; max-width:46rem; margin:0; }

/* headings and body */
h1,h2,h3,h4 { font-family:%(SERIF)s !important; font-weight:400 !important; color:var(--ink); }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color:var(--ivory); letter-spacing:.01em; }
[data-testid="stSidebar"] h2 { border-bottom:1px solid #34506A; padding-bottom:.35rem; }
[data-testid="stCaptionContainer"], .stCaption { color:#4b5f70; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#a9bccb; }

/* buttons: brushed brass for the main action, quiet outlines for the rest */
button[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] {
  background:url(%(STATIC)s/brand/texture-brass.jpg) center/cover; color:#0f1c28; border:1px solid var(--brass-deep);
  font-weight:600; letter-spacing:.02em; border-radius:3px; box-shadow:inset 0 1px 0 rgba(255,255,255,.35), 0 1px 2px rgba(10,20,30,.3); }
button[data-testid="stBaseButton-primary"]:hover { filter:brightness(1.08); border-color:#5c4a24; color:#0f1c28; }
.st-key-ov_back button, .st-key-ov_back button p, .st-key-ov_back button span { color:#fff !important; text-shadow:0 1px 1px rgba(60,45,15,.5); }
button[data-testid="stBaseButton-primary"]:disabled { filter:saturate(.6); opacity:.5; cursor:not-allowed; }
button[data-testid="stBaseButton-secondary"] { background:transparent; border:1px solid rgba(20,39,55,.38); color:var(--ink); border-radius:3px; }
button[data-testid="stBaseButton-secondary"]:hover { border-color:var(--brass-deep); color:var(--brass-deep); background:rgba(165,138,88,.08); }
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] { border-color:rgba(243,239,230,.35); color:var(--ivory); }
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover { border-color:#C4A972; color:#E4D3A6; background:rgba(196,169,114,.12); }
[data-testid="stDownloadButton"] button { background:url(%(STATIC)s/brand/texture-brass.jpg) center/cover; color:#0f1c28; border:1px solid var(--brass-deep); font-weight:600; border-radius:3px; }

/* quotations: serif, set on a mist-blue band with a brass rule */
[data-testid="stMarkdownContainer"] blockquote { margin:.35rem 0 .75rem 0; padding:.8rem 1.1rem; border-left:3px solid var(--brass);
  background:rgba(185,200,212,.72); border-radius:0 3px 3px 0; font-family:%(SERIF)s; font-size:1.12rem; line-height:1.5; color:#0f1f2c; -webkit-text-stroke:.25px #0f1f2c; }
[data-testid="stMarkdownContainer"] blockquote p { margin:0; }
[data-testid="stMarkdownContainer"] blockquote del { color:#6b7a87; }

/* contract panels and finding cards */
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:4px; background:rgba(255,253,248,.62); box-shadow:0 1px 0 rgba(20,39,55,.04); }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { font-family:%(SERIF)s; font-size:1.15rem; color:var(--ink); }
[data-testid="stExpander"] summary:hover, [data-testid="stExpander"] summary:hover p { color:var(--brass-deep); }
section[data-testid="stSidebar"] [data-testid="stExpander"] { background:rgba(255,255,255,.04); border-color:#34506A; box-shadow:none; }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary, section[data-testid="stSidebar"] [data-testid="stExpander"] summary p { color:var(--ivory); font-size:1.05rem; }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover p { color:#E4D3A6; }
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stCaptionContainer"]) { border-color:var(--line); background:rgba(255,253,248,.85); border-radius:4px; }

/* category lines and status chips */
.cat { display:flex; align-items:center; gap:.6rem; margin:1.05rem 0 .15rem 0; padding-top:.7rem; border-top:1px solid var(--line); }
.cat-name { font-family:%(SERIF)s; font-size:1.2rem; color:var(--ink); }
.chip { display:inline-block; padding:.12rem .62rem; border-radius:5px; font-size:.78rem; font-weight:600; letter-spacing:.01em; line-height:1.5; }
.chip-found { background:var(--mist); color:#10202d; }
.chip-miss { background:#EBD8B0; color:#57431a; }
.chip-fail { background:#E6C7C1; color:#6a2a22; }
.cat-note { font-size:.78rem; color:#4b5f70; }

/* alerts, progress, tags */
[data-testid="stAlert"], [data-testid="stAlertContainer"] { background-color:rgba(185,200,212,.42) !important; color:var(--ink) !important; }
[data-testid="stAlertContainer"] p { color:var(--ink) !important; }
[data-testid="stAlert"] { border-radius:3px; border:1px solid var(--line); border-left:3px solid var(--brass); background:rgba(185,200,212,.35); color:var(--ink); }
section[data-testid="stSidebar"] [data-testid="stAlert"], section[data-testid="stSidebar"] [data-testid="stAlertContainer"] { background-color:rgba(185,200,212,.14) !important; color:var(--ivory) !important; }
section[data-testid="stSidebar"] [data-testid="stAlertContainer"] p { color:var(--ivory) !important; }
section[data-testid="stSidebar"] [data-testid="stAlert"] { color:var(--ivory); border-color:#34506A; border-left-color:#C4A972; }
[data-testid="stProgress"] > div > div { background-color:rgba(20,39,55,.12); }
/* the left nav scrolls up and down only, never sideways */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { overflow-x:hidden !important; overflow-y:auto; }
/* the refresh icon fixed in the corner of a dashboard; its wrapper leaves the page flow so it adds no gap above the title */
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-refresh_corner"]) { position:absolute; width:0; height:0; overflow:visible; }
[class*="st-key-refresh_corner"] { position:fixed; top:.6rem; right:1.1rem; z-index:1000001; width:auto; }
[class*="st-key-refresh_corner"] button { width:2.2rem; height:2.2rem; min-height:0; padding:0; border-radius:50%%;
  background:rgba(243,239,230,.94); border:1px solid var(--line); box-shadow:0 1px 4px rgba(20,39,55,.18); color:var(--ink); }
[class*="st-key-refresh_corner"] button:hover { border-color:var(--brass-deep); background:#fff; }
[class*="st-key-refresh_corner"] [data-testid="stIconMaterial"] { font-size:1.25rem; }
/* the run screen: one row per contract */
.pr-head { font-family:%(SERIF)s; font-size:1.55rem; color:var(--ink); margin:.2rem 0 .4rem; }
.pr { padding:.55rem 0 .7rem; border-bottom:1px solid var(--line); }
.pr-top { display:flex; justify-content:space-between; align-items:baseline; gap:1rem; margin-bottom:.4rem; }
.pr-name { min-width:0; display:flex; flex-wrap:wrap; align-items:baseline; gap:.1rem .7rem; }
.pr-title { font-family:%(SERIF)s; font-size:1.12rem; line-height:1.2; color:var(--ink); }
.pr-party { font-size:.82rem; color:#4b5f70; }
.pr-note { flex:none; display:inline-flex; align-items:center; gap:.35rem; font-size:.85rem; font-weight:600; color:#4b5f70; white-space:nowrap; }
.pr-done .pr-note { color:var(--brass-deep); }
.pr-failed .pr-note { color:#8a2f25; white-space:normal; text-align:right; }
.pr-waiting .pr-title { color:#6b7c8b; }
.pr-bar { height:5px; border-radius:3px; background:rgba(20,39,55,.12); overflow:hidden; }
.pr-bar span { display:block; height:100%%; border-radius:3px; background:var(--brass-deep); transition:width .25s ease; }
.pr-failed .pr-bar span { background:#a8473b; }
.pr-ic { flex:none; }
[class*="st-key-pr_done"] { margin-top:.9rem; padding:.55rem .9rem .55rem 1.1rem; border:1px solid var(--line); border-left:3px solid var(--brass);
  border-radius:3px; background:rgba(185,200,212,.35); }
[class*="st-key-pr_done"] p { margin:0; font-size:1rem; color:var(--ink); }
span[data-baseweb="tag"] { background:#C4A972 !important; color:#142737 !important; border-radius:3px; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background:rgba(255,255,255,.05); border:1px dashed #6f8aa3; }
</style>
"""


def apply_theme(st):
    st.markdown(_CSS % {"INK": INK, "MIST": MIST, "IVORY": IVORY, "BRASS": BRASS, "BRASS_DEEP": BRASS_DEEP, "LINE": LINE,
                        "SERIF": SERIF, "STATIC": STATIC}, unsafe_allow_html=True)


_MARQUEE_JS = """
(function () {
  if (window.__clautraMarquee) return;
  window.__clautraMarquee = true;
  var active = null;
  function clipped(el) {
    var cs = getComputedStyle(el);
    return el.scrollWidth - el.clientWidth > 2 && (cs.overflowX === 'hidden' || cs.overflow === 'hidden');
  }
  function stop() { if (active) { active.classList.remove('clautra-marquee'); active = null; } }
  document.addEventListener('mouseover', function (e) {
    var el = e.target, hops = 0;
    while (el && el !== document.body && hops < 5 && !clipped(el)) { el = el.parentElement; hops++; }
    // only a line of text slides: never a container such as the whole sidebar or a panel with many parts inside
    if (el && (el.matches('section, [data-testid="stSidebarContent"], [data-testid="stSidebar"], [data-testid="stMain"]') || el.getElementsByTagName('*').length > 8)) { stop(); return; }
    if (!el || el === document.body || !clipped(el)) { stop(); return; }
    if (el === active) return;
    stop();
    var extra = el.scrollWidth - el.clientWidth;
    el.title = el.title || el.textContent.trim();
    el.style.setProperty('--shift', '-' + (extra + 6) + 'px');
    el.style.setProperty('--dur', Math.max(3, extra / 28 + 2) + 's');
    el.classList.add('clautra-marquee');
    active = el;
  }, true);
  document.addEventListener('mouseleave', stop, true);
})();
"""


def marquee(st):
    """Switched off: long names are cut off with "..." and show in full as a tooltip, they no longer slide on hover. The calls on
    every page are kept so the slide can come back by restoring the one line below."""
    return None  # st.html(f"<script>{_MARQUEE_JS}</script>", unsafe_allow_javascript=True)


def brand(st):
    """The corner logo (sidebar top)."""
    st.markdown('<div class="brand"><div class="brand-stack" role="img" aria-label="Clautra"><div class="gold brand-mark"></div><div class="gold brand-word"></div></div></div>', unsafe_allow_html=True)
    with st.container(key="brandlink"):  # an invisible link laid over the logo: it goes to the home page without reloading the app
        st.page_link("app.py", label="Clautra home", help="Back to the home page")


def views(st, on_review=False):
    """The switch between the two screens, drawn under the logo (Streamlit's own page menu is off in config.toml).
    The Junior associate link opens the Overview (the home screen). The Review page belongs to the same role, so while it is open
    (`on_review`) that link is drawn as the current one."""
    with st.container(key="nav_junior_on" if on_review else "nav_junior"):
        st.page_link("app.py", label="Junior associate", icon=":material/fact_check:")
    st.page_link("pages/1_Senior_lawyer.py", label="Senior lawyer", icon=":material/gavel:")


def kpi_row(st, items):
    """A row of headline numbers. Each item is (value, label, note); a tile whose note is given and whose value is above 0
    is highlighted (something is waiting for the reader). Text is escaped."""
    tiles = []
    for value, label, note, flag in items:
        tiles.append(f'<div class="kpi{" flag" if flag else ""}"><div class="num">{int(value)}</div>'
                     f'<div class="lbl">{html.escape(label)}</div>' + (f'<div class="note">{html.escape(note)}</div>' if note else "") + "</div>")
    st.markdown('<div class="kpis">' + "".join(tiles) + "</div>", unsafe_allow_html=True)


def hero(st, demo=False):
    """The page header. `demo` adds a small 'Demo mode' tag to the eyebrow line (shown in user mode when the offline
    keyword demo is the model, so the results are never mistaken for a real model's)."""
    tag = '&nbsp;&nbsp;·&nbsp;&nbsp;Demo mode' if demo else ''
    st.markdown(
        f'<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Contract review{tag}</div>'
        '<h1>Contract review</h1><p class="tag">Every clause, accounted for.</p><hr class="rule">'
        '<p class="lede">Every finding is a quotation found word for word in the contract. A category with no verified '
        "finding is flagged for you to check, never left blank.</p></div>", unsafe_allow_html=True)


def category_heading(name, status, reviewed=False):
    """One category line: its name and a coloured status chip. `name` and `status` are escaped."""
    chip = f'<span class="chip {CHIP_CLASS.get(status, "chip-fail")}">{html.escape(status)}</span>'
    note = '<span class="cat-note">✔ reviewed</span>' if reviewed else ""
    return f'<div class="cat"><span class="cat-name">{html.escape(name)}</span>{chip}{note}</div>'

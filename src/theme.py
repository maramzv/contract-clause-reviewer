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
.block-container { padding-top:2.2rem; max-width:1180px; }


/* corner logo: the lockup is used as a mask over brushed brass with a soft sheen, so it gleams like the metal version */
[data-testid="stSidebarHeader"] { height:1.6rem; min-height:0; padding:0 .5rem; margin:0; }
.brand { display:flex; justify-content:center; padding:1.8rem 0 1.6rem; margin:-.2rem -1.9rem 1.1rem -1.9rem;
  background:radial-gradient(ellipse 80%% 70%% at 50%% 38%%, rgba(46,80,108,.55), rgba(10,24,36,.0) 72%%), rgba(8,20,31,.55);
  border-bottom:1px solid rgba(196,169,114,.45); filter:drop-shadow(0 1px 1px rgba(0,0,0,.65)); }
.brand-stack { display:flex; flex-direction:column; align-items:center; gap:30px; }
.gold { background-image:linear-gradient(112deg, rgba(255,244,214,0) 18%%, rgba(255,244,214,.7) 40%%, rgba(255,244,214,0) 62%%), url(%(STATIC)s/brand/texture-brass.jpg);
  background-size:100%% 100%%, cover; background-position:center; filter:brightness(1.35) saturate(1.05); }
.brand-mark { width:92px; aspect-ratio:977 / 1078;
  -webkit-mask:url(%(STATIC)s/brand/clautra-mark-trim.png) center / contain no-repeat; mask:url(%(STATIC)s/brand/clautra-mark-trim.png) center / contain no-repeat; }
.brand-word { width:172px; aspect-ratio:1662 / 201;
  -webkit-mask:url(%(STATIC)s/brand/clautra-wordmark-trim.png) center / contain no-repeat; mask:url(%(STATIC)s/brand/clautra-wordmark-trim.png) center / contain no-repeat; }

/* KPI row: the three headline numbers of a review */
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:1rem; margin:.3rem 0 1.1rem; }
.kpi { background:rgba(255,253,248,.78); border:1px solid var(--line); border-top:3px solid var(--brass); border-radius:3px; padding:.75rem 1.1rem .85rem; }
.kpi .num { font-family:%(SERIF)s; font-size:2.9rem; line-height:1; color:var(--ink); }
.kpi .lbl { margin-top:.35rem; font-size:.72rem; letter-spacing:.2em; text-transform:uppercase; font-weight:600; color:var(--brass-deep); }
.kpi .note { margin-top:.15rem; font-size:.8rem; color:#4b5f70; }
.kpi.flag { background:#EFE2BF; border-color:#D9C38C; border-top-color:var(--brass-deep); }
.kpi.flag .lbl { color:#5c4719; }

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
span[data-baseweb="tag"] { background:#C4A972 !important; color:#142737 !important; border-radius:3px; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] { background:rgba(255,255,255,.05); border:1px dashed #6f8aa3; }
</style>
"""


def apply_theme(st):
    st.markdown(_CSS % {"INK": INK, "MIST": MIST, "IVORY": IVORY, "BRASS": BRASS, "BRASS_DEEP": BRASS_DEEP, "LINE": LINE,
                        "SERIF": SERIF, "STATIC": STATIC}, unsafe_allow_html=True)


def brand(st):
    """The corner logo (sidebar top)."""
    st.markdown('<div class="brand"><div class="brand-stack" role="img" aria-label="Clautra"><div class="gold brand-mark"></div><div class="gold brand-word"></div></div></div>', unsafe_allow_html=True)


def kpi_row(st, items):
    """A row of headline numbers. Each item is (value, label, note); a tile whose note is given and whose value is above 0
    is highlighted (something is waiting for the reader). Text is escaped."""
    tiles = []
    for value, label, note, flag in items:
        tiles.append(f'<div class="kpi{" flag" if flag else ""}"><div class="num">{int(value)}</div>'
                     f'<div class="lbl">{html.escape(label)}</div>' + (f'<div class="note">{html.escape(note)}</div>' if note else "") + "</div>")
    st.markdown('<div class="kpis">' + "".join(tiles) + "</div>", unsafe_allow_html=True)


def hero(st):
    st.markdown(
        '<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Contract review</div>'
        '<h1>Contract review</h1><p class="tag">Every clause, accounted for.</p><hr class="rule">'
        '<p class="lede">Every finding is a quotation found word for word in the contract. A category with no verified '
        "finding is flagged for you to check, never left blank.</p></div>", unsafe_allow_html=True)


def category_heading(name, status, reviewed=False):
    """One category line: its name and a coloured status chip. `name` and `status` are escaped."""
    chip = f'<span class="chip {CHIP_CLASS.get(status, "chip-fail")}">{html.escape(status)}</span>'
    note = '<span class="cat-note">✔ reviewed</span>' if reviewed else ""
    return f'<div class="cat"><span class="cat-name">{html.escape(name)}</span>{chip}{note}</div>'

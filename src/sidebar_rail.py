"""New review in the left sidebar as three steps down a thin rail: add contracts, choose clauses, run.

A finished step shrinks to one line with its own tick and the next one opens. The contracts come from a browse-or-drop box
(in the demo it opens the fake Open window, see demo_picker) and the clause types are slim rows with an icon that fill in brass
when chosen. Drawing and clicks only: the run itself is app.run."""
import html
import urllib.parse

import streamlit as st

import demo_picker
from clause_review.categories import CATEGORIES
from clause_review.provider_choice import CHOICES, default_choice, problem
from clause_review.review_view import display_name
from clause_review.samples import workers_from_env

ICONS = [  # line icons, one per clause type, in the order of CATEGORIES
    '<path d="M4 8h13l-3-3M20 16H7l3 3"/>',
    '<circle cx="8" cy="12" r="3.5"/><path d="M11.5 12H21M17 12v3.5M20 12v2.5"/>',
    '<path d="M6 3h9v18H6zM15 6l4 1.5v13L15 21M10 12h.01"/>',
    '<path d="M20 11a8 8 0 1 0-2.3 5.6M20 4v7h-7"/>',
    '<path d="M12 4v16M6 20h12M5 7h14M5 7l-2.5 6a3 3 0 0 0 5 0zM19 7l-2.5 6a3 3 0 0 0 5 0z"/>',
]
UPLOAD = '<path d="M12 16V5M7.5 9.5 12 5l4.5 4.5M5 19h14"/>'
DOC = '<path d="M6 3h9l4 4v14H6zM15 3v4h4M9 13h6M9 17h6"/>'


def _uri(path, color, width=1.6):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='{color}' stroke-width='{width}' "
           f"stroke-linecap='round' stroke-linejoin='round'>{path}</svg>")
    return "url(\"data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="") + "\")"


def _css():
    rows = "".join(
        f'[class*="st-key-nrc{i}_off"] button::before{{background-image:{_uri(p, "#9fb1c0")};}}'
        f'[class*="st-key-nrc{i}_on"] button::before{{background-image:{_uri(p, "#C4A972")};}}' for i, p in enumerate(ICONS))
    return f"""<style>
section[data-testid="stSidebar"] [class*="st-key-nr_rail"] {{ position:relative; padding-left:26px; gap:.9rem; }}
section[data-testid="stSidebar"] [class*="st-key-nr_rail"]::before {{ content:""; position:absolute; left:8px; top:10px; bottom:16px; width:1px; background:#34506A; }}
section[data-testid="stSidebar"] [class*="st-key-nr_s"] {{ position:relative; gap:.35rem; }}
[class*="st-key-nr_s"]::before {{ content:""; position:absolute; left:-26px; top:2px; width:17px; height:17px; border-radius:50%;
  border:1.5px solid #8aa3b8; background:#142737; box-sizing:border-box; }}
[class*="st-key-nr_s"][class*="_now"]::before {{ border-color:#C4A972; box-shadow:0 0 0 3px rgba(196,169,114,.25); }}
[class*="st-key-nr_s"][class*="_done"]::before {{ background:#F3EFE6; border-color:#F3EFE6; }}
[class*="st-key-nr_s"][class*="_done"]::after {{ content:""; position:absolute; left:-21px; top:6px; width:7px; height:4px; border:2px solid #142737;
  border-top:0; border-right:0; transform:rotate(-48deg); }}
[class*="st-key-nr_s"][class*="_dim"] {{ opacity:.45; }}
[class*="st-key-nr_s"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0 !important; }}  /* streamlit pulls the next element up by 1rem */
[class*="st-key-nr_s"] [data-testid="stMarkdownContainer"] > * {{ margin-bottom:0 !important; }}
.nr-h {{ font-weight:600; font-size:14px; color:#F3EFE6; margin-top:1px; }}
.nr-hint {{ font-size:12.5px; color:#9fb1c0; white-space:nowrap; }}
.nr-files {{ list-style:none; margin:0; padding:0; max-height:112px; overflow:auto; border-block:1px solid #34506A; }}
.nr-files li {{ display:flex; gap:8px; align-items:center; padding:4px 0; border-bottom:1px solid rgba(52,80,106,.5); font-size:12.5px; color:#F3EFE6; }}
.nr-files li:last-child {{ border-bottom:0; }}
.nr-files .n {{ flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.nr-files .s {{ color:#9fb1c0; font-size:11.5px; }}
.nr-files .d {{ width:13px; height:15px; flex:none; background:{_uri(DOC, "#9fb1c0", 1.8)} center/contain no-repeat; }}
/* the browse or drop box */
[class*="st-key-nr_browse"] button {{ height:auto; min-height:0; flex-direction:column; gap:4px; padding:18px 10px; border:1px dashed #6f8aa3 !important;
  background:transparent !important; color:#9fb1c0 !important; box-shadow:none; }}
[class*="st-key-nr_browse"] button::before {{ content:""; width:22px; height:22px; background:{_uri(UPLOAD, "#9fb1c0")} center/contain no-repeat; }}
[class*="st-key-nr_browse"] button::after {{ content:"PDF or text"; font-size:12px; color:#9fb1c0; }}
[class*="st-key-nr_browse"] button p {{ font-size:13px; color:#9fb1c0; }}
[class*="st-key-nr_browse"] button p strong {{ color:#F3EFE6; text-decoration:underline; text-underline-offset:3px; }}
[class*="st-key-nr_browse"] button:hover {{ border-color:#C4A972 !important; }}
/* Change and Next read as small links */
[class*="st-key-nr_link"] button {{ background:transparent !important; border:0 !important; box-shadow:none; min-height:0; height:auto; padding:0; color:#B9C8D4 !important; justify-content:flex-end; }}
[class*="st-key-nr_link"] button p {{ white-space:nowrap; font-size:12.5px; text-decoration:underline; text-underline-offset:3px; color:#B9C8D4; }}
[class*="st-key-nr_link"] button:disabled {{ opacity:.4; }}
/* the clause rows: a dim outline, filled with brass when chosen */
[class*="st-key-nrc"] button {{ height:auto; min-height:0; justify-content:flex-start; gap:10px; padding:6px 9px; background:transparent !important;
  border:1px solid #34506A !important; border-radius:3px; color:#9fb1c0 !important; box-shadow:none; }}
[class*="st-key-nrc"] button::before {{ content:""; width:17px; height:17px; flex:none; background-repeat:no-repeat; background-position:center; background-size:contain; }}
[class*="st-key-nrc"] button > div {{ flex:1; justify-content:flex-start !important; }}
[class*="st-key-nrc"] button p {{ font-size:13px; line-height:1.2; color:inherit; text-align:left; }}
[class*="st-key-nrc"] button:hover {{ border-color:#8aa3b8 !important; color:#F3EFE6 !important; }}
[class*="st-key-nrc"][class*="_on"] button {{ background:rgba(196,169,114,.18) !important; border-color:rgba(196,169,114,.5) !important;
  border-left:3px solid #C4A972 !important; color:#E4D3A6 !important; font-weight:600; }}
[class*="st-key-nrc"][class*="_on"] button p {{ font-weight:600; }}
{rows}
</style>"""


def _flip(i):
    sel = st.session_state["nr_clauses"]
    sel.symmetric_difference_update({i})
    st.session_state["nr_ok"] = False  # the choice changed: confirm it again


def _confirm():
    st.session_state["nr_ok"] = True


def _reopen():
    st.session_state["nr_ok"] = False


def _kb(n):
    return f"{max(1, round(n / 1024))} KB"


def render(dev):
    """Draw the three steps. Returns (go, chosen clause names, files, provider name, workers)."""
    provider_name = default_choice()
    if dev:  # choose how this run is done: Mock, the local Claude agent, or the API (dev mode only)
        options = list(CHOICES) + ([provider_name] if provider_name not in CHOICES else [])  # keep e.g. CLAUSE_PROVIDER=local
        provider_name = st.selectbox("Run with", options, index=options.index(provider_name),
                                     format_func=lambda n: CHOICES.get(n, f"{n} (set by CLAUSE_PROVIDER)"))
    blocked = problem(provider_name)  # for everyone (#24): a missing key shows here, before Run, and disables Run
    if blocked:
        st.error(blocked)
    st.markdown(_css(), unsafe_allow_html=True)
    cats = list(CATEGORIES)
    st.session_state.setdefault("nr_clauses", set(range(len(cats))))
    st.session_state.setdefault("nr_ok", False)
    sel = st.session_state["nr_clauses"]
    demo = demo_picker.enabled()
    go = False

    with st.container(key="nr_rail"):
        # 1. contracts
        files = demo_picker.chosen() if demo else (st.session_state.get("nr_upload") or [])
        with st.container(key="nr_s1_" + ("done" if files else "now")):
            st.markdown('<div class="nr-h">Add contracts</div>', unsafe_allow_html=True)
            if demo:
                if not files:
                    with st.container(key="nr_browse"):
                        if st.button("**Browse** or drop contracts", key="nr_browse_btn", use_container_width=True):
                            demo_picker.open_dialog()
                else:
                    items = "".join(f'<li><span class="d"></span><span class="n" title="{html.escape(f.name)}">'
                                    f'{html.escape(display_name(f.name))}</span><span class="s">{_kb(f.size)}</span></li>' for f in files)
                    st.markdown(f'<ul class="nr-files">{items}</ul>', unsafe_allow_html=True)
                    a, b = st.columns([2.6, 1])
                    a.markdown(f'<div class="nr-hint">{len(files)} contract{"s" if len(files) != 1 else ""} · '
                               f'{_kb(sum(f.size for f in files))}</div>', unsafe_allow_html=True)
                    with b.container(key="nr_link_files"):
                        if st.button("Change", key="nr_change_files"):
                            demo_picker.open_dialog()
            else:
                files = st.file_uploader("Upload contracts (PDF or text)", type=["pdf", "txt"], accept_multiple_files=True,
                                         key="nr_upload", label_visibility="collapsed") or []
        have = bool(files)
        if not have:
            st.session_state["nr_ok"] = False
        chosen = [c for i, c in enumerate(cats) if i in sel]
        ok = have and st.session_state["nr_ok"] and bool(chosen)

        # 2. clauses
        state2 = "done" if ok else ("now" if have else "dim")
        with st.container(key=f"nr_s2_{state2}"):
            st.markdown('<div class="nr-h">Choose clauses</div>', unsafe_allow_html=True)
            if state2 == "dim":
                st.markdown('<div class="nr-hint">Opens once contracts are added</div>', unsafe_allow_html=True)
            elif state2 == "now":
                for i, c in enumerate(cats):
                    with st.container(key=f"nrc{i}_{'on' if i in sel else 'off'}"):
                        st.button(c[:1] + c[1:].lower(), key=f"nrb{i}", on_click=_flip, args=(i,), use_container_width=True)
                a, b = st.columns([2.6, 1])
                with b.container(key="nr_link_next"):
                    st.button("Next", key="nr_next", on_click=_confirm, disabled=not chosen)
            else:
                a, b = st.columns([2.6, 1])
                a.markdown(f'<div class="nr-hint">{len(chosen)} clause{"s" if len(chosen) != 1 else ""}</div>', unsafe_allow_html=True)
                with b.container(key="nr_link_clauses"):
                    st.button("Change", key="nr_change_clauses", on_click=_reopen)

        # 3. run
        with st.container(key=f"nr_s3_{'now' if ok else 'dim'}"):
            st.markdown('<div class="nr-h">Run</div>', unsafe_allow_html=True)
            if ok:
                st.markdown(f'<div class="nr-hint">{len(files)} contract{"s" if len(files) != 1 else ""} · '
                            f'{len(chosen)} clause{"s" if len(chosen) != 1 else ""}</div>', unsafe_allow_html=True)
            label = "Run review"
            go = st.button(label, key="nr_run", type="primary", disabled=not ok or bool(blocked), use_container_width=True)
    return go, chosen, files or [], provider_name, workers_from_env()

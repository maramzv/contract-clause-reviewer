"""A demo prop: when someone clicks Upload, an "Open" window that looks like a computer's file dialog pops up with the ten tested
contracts shown as document files, all selected. Open adds them to the review as if they had been picked from a folder.

It is not an operating-system dialog and it does not read anything from the computer: the files are the ten contracts bundled
with the app. Turn it off with CLAUSE_DEMO_PICKER=0 to get the normal upload box back."""
import os
import urllib.parse
from pathlib import Path

import streamlit as st

from clause_review.samples import list_samples

_PAGE = ("<svg xmlns='http://www.w3.org/2000/svg' width='54' height='68' viewBox='0 0 54 68'>"
         "<path d='M4 2h32l14 14v50H4z' fill='white' stroke='#8f9aa6' stroke-width='2'/>"
         "<path d='M36 2v14h14' fill='#e6ebf0' stroke='#8f9aa6' stroke-width='2'/>"
         "<g stroke='#b4bec9' stroke-width='2'><path d='M12 30h30M12 38h30M12 46h30M12 54h20'/></g></svg>")
_ICON = "url(\"data:image/svg+xml;utf8," + urllib.parse.quote(_PAGE, safe="") + "\")"

_CSS = f"""<style>
[data-testid="stDialog"] div[role="dialog"] {{ background:#f3f5f8; }}
.fd-bar {{ display:flex; gap:12px; align-items:center; background:#fff; border:1px solid #d5dbe2; border-radius:4px; padding:7px 12px;
  font-size:13px; color:#33404d; margin-bottom:10px; }}
.fd-bar .path {{ flex:1; }} .fd-bar .search {{ color:#8a96a3; border-left:1px solid #d5dbe2; padding-left:12px; }}
.fd-places {{ font-size:13px; color:#33404d; line-height:2.0; }} .fd-places b {{ display:block; color:#6a7683; font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; margin-top:4px; }}
.fd-places .on {{ background:#dbe7f6; border-radius:3px; padding:0 8px; font-weight:600; }} .fd-places span {{ display:block; padding:0 8px; }}
.fd-foot {{ display:flex; gap:10px; align-items:center; font-size:13px; color:#33404d; margin-top:6px; }}
.fd-foot .name {{ flex:1; background:#fff; border:1px solid #c5ccd5; border-radius:3px; padding:5px 10px; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }}
[class*="st-key-fdc"] button {{ width:100%; height:auto; min-height:126px; background:transparent; border:2px solid transparent; border-radius:6px;
  display:flex; flex-direction:column; align-items:center; justify-content:flex-start; padding:8px 6px; color:#1f2933; box-shadow:none; }}
[class*="st-key-fdc"] button::before {{ content:""; display:block; width:54px; height:68px; margin-bottom:6px; background:{_ICON} center/contain no-repeat; }}
[class*="st-key-fdc"] button p {{ font-size:12px; line-height:1.25; text-align:center; word-break:break-word; display:-webkit-box;
  -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; color:#1f2933; margin:0; }}
[class*="st-key-fdc"] button:hover {{ background:#e9eff7; }}
[class*="st-key-fdc"][class*="_on"] button {{ background:#cfe1fa; border-color:#7aa7e0; }}
</style>"""


def enabled(environ=None):
    """The fake Open window is on unless CLAUSE_DEMO_PICKER=0."""
    return (environ if environ is not None else os.environ).get("CLAUSE_DEMO_PICKER", "1") != "0"


class DemoFile:
    """Looks like an uploaded file to the rest of the app: a name and the bytes."""
    def __init__(self, name, path):
        self.name, self._path = name, path

    @property
    def size(self):
        return Path(self._path).stat().st_size

    def getvalue(self):
        return Path(self._path).read_bytes()


def demo_files():
    """The ten tested contracts, under their full titled names (the short made-up sample is not one of them)."""
    return [DemoFile(f"{s['label']}.txt", s["path"]) for s in list_samples() if s["id"] != "sample"]


def _toggle(i):
    sel = st.session_state.setdefault("fd_sel", set())
    sel.symmetric_difference_update({i})


def _all(n, on):
    st.session_state["fd_sel"] = set(range(n)) if on else set()


@st.dialog("Open", width="large")
def _dialog(files):
    st.markdown(_CSS, unsafe_allow_html=True)
    sel = st.session_state.setdefault("fd_sel", set(range(len(files))))
    per_row = 5
    for r in range(0, len(files), per_row):
        cols = st.columns(per_row)
        for c, i in zip(cols, range(r, min(r + per_row, len(files)))):
            with c.container(key=f"fdc{i}_{'on' if i in sel else 'off'}"):
                st.button(files[i].name, key=f"fdb{i}", on_click=_toggle, args=(i,), use_container_width=True)
    a, b, _, c, d = st.columns([1.2, 1.1, 1.6, 1.1, 1.1])
    a.button("Select all", on_click=_all, args=(len(files), True), use_container_width=True)
    b.button("Clear", on_click=_all, args=(len(files), False), use_container_width=True)
    if c.button("Cancel", use_container_width=True, key="fd_cancel"):
        st.rerun()  # closes the window without adding anything
    if d.button("Open", type="primary", disabled=not sel, use_container_width=True, key="fd_open"):
        st.session_state["fd_files"] = [files[i] for i in sorted(sel)]
        st.session_state["nr_ok"] = False  # new contracts: the clause step is shown again
        st.rerun()


def chosen():
    """The files that were opened in the window (empty until Open is pressed)."""
    return st.session_state.get("fd_files", [])


def open_dialog():
    """Pop up the fake Open window with all ten contracts selected."""
    files = demo_files()
    st.session_state["fd_sel"] = set(range(len(files)))
    _dialog(files)


def reset(st_):
    """Forget the opened files (after a review has been run)."""
    st_.session_state.pop("fd_files", None)
    st_.session_state.pop("fd_sel", None)

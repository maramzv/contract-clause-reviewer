"""Streamlit review screen: upload contracts, choose categories, see each finding with its quotation, page and status.

Run:  streamlit run app.py
Environment: CLAUSE_PROVIDER (mock by default), CLAUSE_DB (SQLite file, default review.db), plus the provider and
spend-limit variables described in the README.
"""
import logging
import tempfile
import time
from pathlib import Path

import streamlit as st

from clause_review.categories import CATEGORIES
from clause_review.pipeline import run_review
from clause_review.samples import format_duration, workers_from_env
from clause_review.provider_choice import CHOICES, NOTES, default_choice, problem, show_dev_tools, toggle_enabled
from clause_review.providers import BudgetExceeded, get_provider
from clause_review.replay import Recorder, play
import demo_picker
import overview
from common import DB_PATH, get_store, result_actions, resume_latest
from progress_ui import ProgressView
from theme import apply_theme, brand, hero, marquee, views

REPLAY_SPEEDS = {"Original": 1.0, "5×": 5.0, "20×": 20.0, "Skip to results": None}

st.set_page_config(page_title="Clautra · Overview", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
dev = False
tools = show_dev_tools()  # the dev and demo parts (Dev mode, Demo tag, saved runs and replay) are hidden by default
if tools and toggle_enabled():  # the switch itself is hidden when CLAUSE_DEV_TOGGLE=0, which leaves the app in user mode
    st.session_state.setdefault("dev_mode", st.query_params.get("dev") == "1")
    dev = st.toggle("Dev mode", key="dev_mode", help="Off: just what a reviewer sees. On: model choice, provider notes and usage.")


def run(files, categories, provider_name, on_event=None, workers=1):
    """Write the uploads to a temp folder (one subfolder each, so equal file names do not collide) and review them."""
    store, provider = get_store(), get_provider(provider_name)
    project = time.strftime("Review %Y-%m-%d %H:%M:%S")
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, f in enumerate(files):
            d = Path(tmp) / str(i)
            d.mkdir()
            p = d / Path(f.name).name
            p.write_bytes(f.getvalue())
            paths.append(p)
        pid = run_review(store, project, paths, provider, categories=categories,
                         workers=workers, on_event=on_event)
    return pid, provider, project


def new_review_form(dev):
    """The setup for a review, drawn in the sidebar under "New review": which clauses, which contracts, and Run.
    Returns what a run needs."""
    provider_name = default_choice()
    if dev:  # choose how this run is done: Mock, the local Claude agent, or the API (dev mode only)
        options = list(CHOICES) + ([provider_name] if provider_name not in CHOICES else [])  # keep e.g. CLAUSE_PROVIDER=local
        provider_name = st.selectbox("Run with", options, index=options.index(provider_name),
                                     format_func=lambda n: CHOICES.get(n, f"{n} (set by CLAUSE_PROVIDER)"))
    blocked = problem(provider_name)  # for everyone (#24): a missing key shows here, before Run, and disables Run
    if blocked:
        st.error(blocked)
    chosen = st.multiselect("Clause types to look for", list(CATEGORIES), default=list(CATEGORIES))
    if demo_picker.enabled():  # the demo's fake Open window with the ten tested contracts
        files = demo_picker.render(st)
    else:
        files = st.file_uploader("Upload contracts (PDF or text)", type=["pdf", "txt"], accept_multiple_files=True)
    workers = workers_from_env()
    n = len(files)
    if not n:
        st.caption("Add at least one contract to run a review.")
    elif not chosen:
        st.caption("Pick at least one clause type.")
    else:
        st.markdown(f"**{n} contract{'s' if n != 1 else ''} · {len(chosen)} clause type{'s' if len(chosen) != 1 else ''}**")
    go = st.button("Run review", type="primary", disabled=not files or not chosen or bool(blocked), use_container_width=True)
    return go, chosen, files, provider_name, workers


# Coming back: `?open=<run id>` opens that saved run (so a design change can be checked with a refresh); otherwise the latest
# saved review opens by itself, once per visit.
if "result" not in st.session_state and st.query_params.get("open", "").isdigit():
    saved = get_store().get_run(int(st.query_params["open"]))
    st.session_state["result"] = {"pid": saved["project_id"], "categories": saved["categories"],
                                  "provider": f"{saved['provider']} (saved run)", "usage": saved["usage"] or ""}
    st.session_state["_resumed"] = True
else:
    resume_latest(st, get_store())

# Sidebar: the two screens, the setup for a new review (open when there is nothing to continue), and the saved runs.
replay_req = open_req = None
runs = get_store().list_runs()
with st.sidebar:
    brand(st)
    views(st)
    # open when there is nothing to continue, or when another screen asked for it (kept open until that review is run)
    new_open = "result" not in st.session_state or bool(st.session_state.get("new_review"))
    with st.expander("New review", expanded=new_open, icon=":material/add:"):
        go, chosen, files, provider_name, workers = new_review_form(dev)
    if tools:  # saved runs and their replay are a developer and demo aid
        # Every finished run is saved with its step-by-step recording, so it can be replayed without calling the model.
        with st.expander("Saved runs", expanded=False):
            if not runs:
                st.caption("Each review you run is saved here automatically, so you can replay it later.")
            else:
                run_id = st.selectbox("Saved run", [r["id"] for r in runs],
                                      format_func=lambda i: next(f"{r['name']} · {r['docs']} contract(s) · {r['provider']} · "
                                                                 f"took {format_duration(r['duration']).replace('instant', 'under a second')}"
                                                                 for r in runs if r["id"] == i))
                speed_label = st.radio("Replay speed", list(REPLAY_SPEEDS), index=2, horizontal=True)
                r1, r2 = st.columns(2)
                if r1.button("Replay", type="primary", use_container_width=True, help="Plays the saved run again with no model calls. "
                             "Starts fresh: nothing is accepted or removed, and questions and answers are not copied."):
                    replay_req = (run_id, REPLAY_SPEEDS[speed_label])
                if r2.button("Open results", use_container_width=True, help="Opens the saved results as they were left."):
                    open_req = run_id

if replay_req:
    saved = get_store().get_run(replay_req[0])
    slot = st.empty()  # the progress screen lives in this slot so it can be cleared once the results are ready
    play(get_store().run_events(saved["id"]), ProgressView(st, slot.container()).handle, replay_req[1])
    pid = get_store().clone_project(saved["project_id"], f"Replay of run {saved['id']} ({saved['name']}) at {time.strftime('%H:%M:%S')}")
    st.session_state["result"] = {"pid": pid, "categories": saved["categories"], "provider": f"{saved['provider']} (replay)",
                                  "usage": "replay of a saved run, no model was called"}
    st.session_state.pop("new_review", None)
    slot.empty()
elif open_req:
    saved = get_store().get_run(open_req)
    st.session_state["result"] = {"pid": saved["project_id"], "categories": saved["categories"],
                                  "provider": f"{saved['provider']} (saved run)", "usage": saved["usage"] or ""}
    st.session_state.pop("new_review", None)

start_slot = None
if "result" not in st.session_state and not go:  # nothing to continue: say how to begin
    start_slot = st.empty()
    with start_slot.container():
        hero(st, demo=tools and not dev and default_choice() == "mock")
        st.info("Open **New review** on the left: choose the clause types, upload your contracts and select Run review. "
                "Your last review, if you have one, opens here by itself.")

if go:
    slot = st.empty()
    recorder = Recorder(forward=ProgressView(st, slot.container()).handle)
    try:
        pid, provider, project = run(files, chosen, provider_name, on_event=recorder, workers=workers)
        usage = provider.meter.summary()
        get_store().save_run(project, provider.name, getattr(provider, "model", ""), pid, chosen, usage, recorder.events)
        st.session_state["result"] = {"pid": pid, "categories": chosen, "usage": usage, "provider": provider.name}
        st.session_state.pop("new_review", None)  # done: the setup tucks away
        demo_picker.reset(st)
        st.rerun()  # redraw so the new run appears under Saved runs (the sidebar was drawn before the run)
    except BudgetExceeded as e:
        st.session_state.pop("result", None)
        st.error(f"Stopped at the spending limit: {e}. Responses already paid for are saved and are reused on a rerun.")
        if dev and provider_name == "anthropic":
            st.info("Dev toggle: switch Run with to Local Claude agent and run again. Responses already paid for are cached.")
    except Exception as e:  # never show a half-finished table as if it were complete
        logging.exception("Review failed")
        st.session_state.pop("result", None)
        st.error(f"The review could not be completed: {e}")
        if dev and provider_name == "anthropic":
            st.info("Dev toggle: switch Run with to Local Claude agent and run again. Responses already paid for are cached.")

res = st.session_state.get("result")
if not res:
    st.stop()  # the hint above (or the error) is what is on the page

result_actions(st, get_store(), res)
if dev:
    st.caption(f"Model: {res.get('provider', '?')}. Usage: {res['usage']}")
title_col, go_col = st.columns([5, 1.3], vertical_alignment="center")
title_col.markdown('<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Junior associate</div><h1>Overview</h1>'
                   '<p class="tag">Where every clause stands.</p></div>', unsafe_allow_html=True)
if go_col.button("Continue reviewing", type="primary", icon=":material/arrow_forward:", use_container_width=True, key="ov_back"):
    st.switch_page("pages/2_Review.py")
st.markdown('<hr class="rule">', unsafe_allow_html=True)
overview.render(st, get_store(), res)

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
from clause_review.samples import estimate_seconds, format_duration, list_samples, workers_from_env
from clause_review.provider_choice import CHOICES, NOTES, default_choice, problem, toggle_enabled
from clause_review.providers import BudgetExceeded, get_provider
from clause_review.replay import Recorder, play
from clause_review.view import load_results
import os

import workspace
import workspace_html
from common import DB_PATH, get_store, result_actions
from progress_ui import ProgressView
from theme import apply_theme, brand, hero, marquee, views

REPLAY_SPEEDS = {"Original": 1.0, "5×": 5.0, "20×": 20.0, "Skip to results": None}

st.set_page_config(page_title="Clautra · Contract review", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
dev = False
if toggle_enabled():  # the switch itself is hidden when CLAUSE_DEV_TOGGLE=0, which leaves the app in user mode
    st.session_state.setdefault("dev_mode", st.query_params.get("dev") == "1")
    dev = st.toggle("Dev mode", key="dev_mode", help="Off: just what a reviewer sees. On: model choice, provider notes and usage.")


def run(files, categories, provider_name, samples=(), on_event=None, workers=1):
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
        for j, smp in enumerate(samples):  # bundled sample contracts, named by id and title in the results
            d = Path(tmp) / f"s{j}"
            d.mkdir()
            p = d / f"{smp['label']}.txt"
            p.write_bytes(Path(smp["path"]).read_bytes())
            paths.append(p)
        pid = run_review(store, project, paths, provider, categories=categories,
                         workers=workers, on_event=on_event)
    return pid, provider, project


provider_name = default_choice()
blocked = None
with st.sidebar:
    brand(st)
    views(st, on_review=True)
    st.header("New review")
    if dev:  # choose how this run is done: Mock, the local Claude agent, or the API (dev mode only)
        options = list(CHOICES) + ([provider_name] if provider_name not in CHOICES else [])  # keep e.g. CLAUSE_PROVIDER=local
        provider_name = st.selectbox("Run with", options, index=options.index(provider_name),
                                     format_func=lambda n: CHOICES.get(n, f"{n} (set by CLAUSE_PROVIDER)"))
    blocked = problem(provider_name)  # for everyone (#24): a missing key shows here, before Run, and disables Run
    if blocked:
        st.error(blocked)
    chosen = st.multiselect("Clause categories", list(CATEGORIES), default=list(CATEGORIES))
    files = st.file_uploader("Contracts (PDF or text)", type=["pdf", "txt"], accept_multiple_files=True)
    samples = list_samples()
    workers = workers_from_env()
    by_id = {smp["id"]: smp for smp in samples}

    def set_samples(everything):
        st.session_state["sample_pick"] = list(by_id) if everything else []

    st.multiselect("Sample contracts", list(by_id), key="sample_pick", placeholder="Choose from the bundled contracts",
                   format_func=lambda i: f"{by_id[i]['title']} · {format_duration(estimate_seconds(by_id[i]['chunks'], provider_name, workers))}",
                   help="Public contracts that come with the app. The time beside each is a rough estimate for the model chosen.")
    picked = [by_id[i] for i in st.session_state.get("sample_pick", []) if i in by_id]
    b1, b2 = st.columns(2)
    b1.button("Select all samples", on_click=set_samples, args=(True,), use_container_width=True)
    b2.button("Clear", on_click=set_samples, args=(False,), use_container_width=True)
    if picked:
        total = estimate_seconds(sum(x["chunks"] for x in picked), provider_name, workers)
        st.markdown(f"**{len(picked)} selected · {format_duration(total)} in total**")
    go = st.button("Run review", type="primary", disabled=not (files or picked) or not chosen or bool(blocked))

    # Every finished run is saved with its step-by-step recording, so it can be replayed without calling the model.
    replay_req = open_req = None
    st.header("Saved runs")
    saved_runs = get_store().list_runs()
    if not saved_runs:
        st.caption("Each review you run is saved here automatically, so you can replay it later.")
    else:
        run_id = st.selectbox("Saved run", [r["id"] for r in saved_runs],
                              format_func=lambda i: next(f"{r['name']} · {r['docs']} contract(s) · {r['provider']} · "
                                                         f"took {format_duration(r['duration']).replace('instant', 'under a second')}"
                                                         for r in saved_runs if r["id"] == i))
        speed_label = st.radio("Replay speed", list(REPLAY_SPEEDS), index=2, horizontal=True)
        r1, r2 = st.columns(2)
        if r1.button("Replay", type="primary", use_container_width=True, help="Plays the saved run again with no model calls. "
                     "Starts fresh: nothing is accepted or removed, and questions and answers are not copied."):
            replay_req = (run_id, REPLAY_SPEEDS[speed_label])
        if r2.button("Open results", use_container_width=True, help="Opens the saved results as they were left."):
            open_req = run_id

if dev and NOTES.get(provider_name):
    st.warning(NOTES[provider_name])

if replay_req:
    saved = get_store().get_run(replay_req[0])
    slot = st.empty()  # the progress screen lives in this slot so it can be cleared once the results are ready
    play(get_store().run_events(saved["id"]), ProgressView(st, slot.container()).handle, replay_req[1])
    pid = get_store().clone_project(saved["project_id"], f"Replay of run {saved['id']} ({saved['name']}) at {time.strftime('%H:%M:%S')}")
    st.session_state["result"] = {"pid": pid, "categories": saved["categories"], "provider": f"{saved['provider']} (replay)",
                                  "usage": "replay of a saved run, no model was called"}
    slot.empty()
elif open_req or (st.query_params.get("open", "").isdigit() and "result" not in st.session_state):
    # `?open=<run id>` in the address opens a saved run's results directly, so a design change can be checked with a refresh
    saved = get_store().get_run(open_req or int(st.query_params["open"]))
    st.session_state["result"] = {"pid": saved["project_id"], "categories": saved["categories"],
                                  "provider": f"{saved['provider']} (saved run)", "usage": saved["usage"] or ""}

if go:
    slot = st.empty()
    recorder = Recorder(forward=ProgressView(st, slot.container()).handle)
    try:
        pid, provider, project = run(files, chosen, provider_name, picked, on_event=recorder, workers=workers)
        usage = provider.meter.summary()
        get_store().save_run(project, provider.name, getattr(provider, "model", ""), pid, chosen, usage, recorder.events)
        st.session_state["result"] = {"pid": pid, "categories": chosen, "usage": usage, "provider": provider.name}
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
    hero(st, demo=not dev and default_choice() == "mock")
    st.info("Choose categories, upload one or more contracts and select Run review.")
    st.stop()

docs = load_results(get_store(), res["pid"], res["categories"])
result_actions(st, get_store(), res)
if dev:
    st.caption(f"Model: {res.get('provider', '?')}. Usage: {res['usage']}")
(workspace if os.environ.get("CLAUSE_WORKSPACE") == "classic" else workspace_html).render(st, get_store(), res, docs)

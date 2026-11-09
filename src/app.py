"""Streamlit review screen: upload contracts, choose categories, see each finding with its quotation, page and status.

Run:  streamlit run app.py
Environment: CLAUSE_PROVIDER (mock by default), CLAUSE_DB (SQLite file, default review.db), plus the provider and
spend-limit variables described in the README.
"""
import os
import tempfile
import time
from pathlib import Path

import streamlit as st

from clause_review.categories import CATEGORIES
from clause_review.envfile import load_env
from clause_review.export import csv_text
from clause_review.pipeline import run_review
from clause_review.samples import estimate_seconds, format_duration, list_samples, workers_from_env
from clause_review.provider_choice import CHOICES, NOTES, default_choice, problem, toggle_enabled
from clause_review.providers import BudgetExceeded, get_provider
from clause_review.replay import Recorder, play
from clause_review.store import FAILED, FOUND, NOT_FOUND, Store
from clause_review.view import load_results, md_escape
from progress_ui import ProgressView

load_env()  # use the key and spend limit from .env, if there is one
ICON = {FOUND: "✅", NOT_FOUND: "⚠️", FAILED: "❌"}
DB_PATH = os.environ.get("CLAUSE_DB", "review.db")
REPLAY_SPEEDS = {"Original": 1.0, "5×": 5.0, "20×": 20.0, "Skip to results": None}

st.set_page_config(page_title="Contract clause review", layout="wide")
st.title("Contract clause review")
st.caption("Every finding is a quotation found word for word in the contract. "
           "A category with no verified finding is flagged for you to check, never left blank.")


@st.cache_resource
def get_store():
    return Store(DB_PATH)


def act(finding_id, state):
    get_store().set_review(finding_id, state)


def mark_reviewed(document_id, category, key):
    get_store().set_category_reviewed(document_id, category, st.session_state[key])


def run(files, categories, provider_name, samples=(), on_event=None):
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
                         workers=int(os.environ.get("CLAUSE_WORKERS", "1")), on_event=on_event)
    return pid, provider, project


provider_name = default_choice()
blocked = None
with st.sidebar:
    st.header("New review")
    if toggle_enabled():  # dev only: pick the model for this run (CLAUSE_DEV_TOGGLE=1)
        provider_name = st.selectbox("Model (dev)", list(CHOICES), index=list(CHOICES).index(provider_name) if provider_name in CHOICES else 0,
                                     format_func=CHOICES.get)
        blocked = problem(provider_name)
        if blocked:
            st.error(blocked)
    chosen = st.multiselect("Clause categories", list(CATEGORIES), default=list(CATEGORIES))
    files = st.file_uploader("Contracts (PDF or text)", type=["pdf", "txt"], accept_multiple_files=True)
    samples = list_samples()
    workers = workers_from_env()

    def set_samples(value):
        for smp in samples:
            st.session_state[f"sample_{smp['id']}"] = value

    picked = []
    with st.expander("Sample contracts (bundled)", expanded=True):
        st.caption("Public contracts that come with the app. The time is a rough estimate for the model chosen.")
        b1, b2 = st.columns(2)
        b1.button("Select all", on_click=set_samples, args=(True,), use_container_width=True)
        b2.button("Clear", on_click=set_samples, args=(False,), use_container_width=True)
        for smp in samples:
            est = format_duration(estimate_seconds(smp["chunks"], provider_name, workers))
            if st.checkbox(f"{smp['title']} · {est}", key=f"sample_{smp['id']}"):
                picked.append(smp)
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
                     "Starts fresh: nothing is accepted or removed."):
            replay_req = (run_id, REPLAY_SPEEDS[speed_label])
        if r2.button("Open results", use_container_width=True, help="Opens the saved results as they were left."):
            open_req = run_id

if NOTES.get(provider_name):
    st.warning(NOTES[provider_name])

if replay_req:
    saved = get_store().get_run(replay_req[0])
    slot = st.empty()  # the progress screen lives in this slot so it can be cleared once the results are ready
    play(get_store().run_events(saved["id"]), ProgressView(st, slot.container()).handle, replay_req[1])
    pid = get_store().clone_project(saved["project_id"], f"Replay of run {saved['id']} ({saved['name']}) at {time.strftime('%H:%M:%S')}")
    st.session_state["result"] = {"pid": pid, "categories": saved["categories"], "provider": f"{saved['provider']} (replay)",
                                  "usage": "replay of a saved run, no model was called"}
    slot.empty()
elif open_req:
    saved = get_store().get_run(open_req)
    st.session_state["result"] = {"pid": saved["project_id"], "categories": saved["categories"],
                                  "provider": f"{saved['provider']} (saved run)", "usage": saved["usage"] or ""}

if go:
    slot = st.empty()
    recorder = Recorder(forward=ProgressView(st, slot.container()).handle)
    try:
        pid, provider, project = run(files, chosen, provider_name, picked, on_event=recorder)
        usage = provider.meter.summary()
        get_store().save_run(project, provider.name, getattr(provider, "model", ""), pid, chosen, usage, recorder.events)
        st.session_state["result"] = {"pid": pid, "categories": chosen, "usage": usage, "provider": provider.name}
        st.rerun()  # redraw so the new run appears under Saved runs (the sidebar was drawn before the run)
    except BudgetExceeded as e:
        st.session_state.pop("result", None)
        st.error(f"Stopped at the spending limit: {e}. Responses already paid for are saved and are reused on a rerun.")
        if toggle_enabled() and provider_name == "anthropic":
            st.info("Dev toggle: switch Model (dev) to Claude Code and run again. Responses already paid for are cached.")
    except Exception as e:  # never show a half-finished table as if it were complete
        st.session_state.pop("result", None)
        st.error(f"The review could not be completed: {e}")
        if toggle_enabled() and provider_name == "anthropic":
            st.info("Dev toggle: switch Model (dev) to Claude Code and run again. Responses already paid for are cached.")

res = st.session_state.get("result")
if not res:
    st.info("Choose categories, upload one or more contracts and select Run review.")
    st.stop()

docs = load_results(get_store(), res["pid"], res["categories"])
all_f = [f for d in docs for f in d["findings"]]
n_check = sum(1 for d in docs for c in res["categories"] if d["categories"][c] != FOUND)
tally = {k: sum(1 for f in all_f if f["review"] == k) for k in ("pending", "accepted", "removed")}
st.subheader(f"{len(docs)} contract(s), {len(all_f) - tally['removed']} finding(s), {n_check} category check(s) for you")
n_marked = sum(1 for d in docs for c in res["categories"] if d["reviewed"][c])
st.caption(f"Reviewed: {tally['accepted']} accepted, {tally['removed']} removed, {tally['pending']} not yet reviewed. "
           f"{n_marked} of {len(docs) * len(res['categories'])} categories marked as reviewed. "
           f"Model: {res.get('provider', '?')}. Usage: {res['usage']}")
st.sidebar.download_button("Download CSV", csv_text(get_store(), res["pid"]), file_name="clause_review.csv",
                           mime="text/csv", help="Accepted and not-yet-reviewed findings, plus every category still to check.")

for d in docs:
    found = sum(1 for c in res["categories"] if d["categories"][c] == FOUND)
    label = f"{d['name']}  ·  {found} of {len(res['categories'])} categories found"
    if d["status"] == "failed":
        label = f"{d['name']}  ·  Failed to process"
    with st.expander(label, expanded=len(docs) <= 3):
        if d["status"] == "failed":
            st.error(f"Failed to process: {d['error']}")
        for c in res["categories"]:
            status = d["categories"][c] or FAILED
            st.markdown(f"**{ICON.get(status, '❌')} {c}** — {status}" + ("  ·  ✔ reviewed" if d["reviewed"][c] else ""))
            key = f"reviewed{d['id']}-{c}"
            st.checkbox("Mark this category as reviewed", value=d["reviewed"][c], key=key, on_change=mark_reviewed,
                        args=(d["id"], c, key), help="Only a progress mark: it does not change the status above.")
            for f in (x for x in d["findings"] if x["category"] == c):
                removed = f["review"] == "removed"
                with st.container(border=True):
                    st.caption(f"Page {f['page']} · {f['review'].capitalize() if f['review'] != 'pending' else 'Not yet reviewed'}")
                    quote = md_escape(f["quote"])
                    st.markdown("> " + (f"~~{quote}~~" if removed else quote))
                    b1, b2, _ = st.columns([1, 1, 6])
                    if removed:
                        b1.button("Restore", key=f"restore{f['id']}", on_click=act, args=(f["id"], "pending"))
                    else:
                        b1.button("Accept", key=f"accept{f['id']}", on_click=act, args=(f["id"], "accepted"),
                                  type="secondary" if f["review"] == "accepted" else "primary",
                                  disabled=f["review"] == "accepted")
                        b2.button("Remove", key=f"remove{f['id']}", on_click=act, args=(f["id"], "removed"))

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
from clause_review.export import csv_text
from clause_review.pipeline import run_review
from clause_review.samples import estimate_seconds, format_duration, list_samples, workers_from_env
from clause_review.provider_choice import CHOICES, NOTES, default_choice, problem, toggle_enabled
from clause_review.providers import BudgetExceeded, get_provider
from clause_review.replay import Recorder, play
from clause_review.store import ANSWERED, FAILED, FOUND, NOT_FOUND, OPEN, RESOLVED
from clause_review.view import load_results, md_escape
from common import DB_PATH, get_store
from progress_ui import ProgressView
from theme import apply_theme, brand, category_heading, hero, kpi_row, marquee, views

ICON = {FOUND: "✅", NOT_FOUND: "⚠️", FAILED: "❌"}
REPLAY_SPEEDS = {"Original": 1.0, "5×": 5.0, "20×": 20.0, "Skip to results": None}

st.set_page_config(page_title="Clautra · Contract review", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
dev = False
if toggle_enabled():  # the switch itself is hidden when CLAUSE_DEV_TOGGLE=0, which leaves the app in user mode
    st.session_state.setdefault("dev_mode", st.query_params.get("dev") == "1")
    dev = st.toggle("Dev mode", key="dev_mode", help="Off: just what a reviewer sees. On: model choice, provider notes and usage.")
hero(st, demo=not dev and default_choice() == "mock")


def act(finding_id, state):
    get_store().set_review(finding_id, state)


def save_question(finding_id, key):
    get_store().set_question(finding_id, st.session_state[key])


def resolve(finding_id, resolved):
    get_store().set_resolved(finding_id, resolved)


QSTATE_CHIP = {OPEN: ("chip-miss", "Question open: waiting for the senior lawyer"),
               ANSWERED: ("chip-found", "Answered by the senior lawyer"), RESOLVED: ("chip-found", "Question resolved")}


def mark_reviewed(document_id, category, key):
    get_store().set_category_reviewed(document_id, category, st.session_state[key])


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
    views(st)
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
    st.info("Choose categories, upload one or more contracts and select Run review.")
    st.stop()

docs = load_results(get_store(), res["pid"], res["categories"])
all_f = [f for d in docs for f in d["findings"]]
n_check = sum(1 for d in docs for c in res["categories"] if d["categories"][c] != FOUND)
tally = {k: sum(1 for f in all_f if f["review"] == k) for k in ("pending", "accepted", "removed")}
n_findings = len(all_f) - tally["removed"]
kpi_row(st, [(len(docs), "Contract" if len(docs) == 1 else "Contracts", None, False),
             (n_findings, "Finding" if n_findings == 1 else "Findings", "verbatim quotations", False),
             (n_check, "To check" , "categories for you to review", n_check > 0)])
qn = {k: sum(1 for f in all_f if f["review"] != "removed" and f["qstate"] == k) for k in (OPEN, ANSWERED, RESOLVED)}
n_marked = sum(1 for d in docs for c in res["categories"] if d["reviewed"][c])
st.caption(f"Reviewed: {tally['accepted']} accepted, {tally['removed']} removed, {tally['pending']} not yet reviewed. "
           f"{n_marked} of {len(docs) * len(res['categories'])} categories marked as reviewed. "
           + (f"Questions for the senior lawyer: {qn[OPEN]} open, {qn[ANSWERED]} answered, {qn[RESOLVED]} resolved. "
              if sum(qn.values()) else "")
           + (f"Model: {res.get('provider', '?')}. Usage: {res['usage']}" if dev else ""))
st.sidebar.button("Refresh", help="Reloads the results, to pick up answers the senior lawyer has just saved.",
                  use_container_width=True)
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
            st.markdown(category_heading(c, status, d["reviewed"][c]), unsafe_allow_html=True)
            key = f"reviewed{d['id']}-{c}"
            st.checkbox("Mark this category as reviewed", value=d["reviewed"][c], key=key, on_change=mark_reviewed,
                        args=(d["id"], c, key), help="Only a progress mark: it does not change the status above.")
            for f in (x for x in d["findings"] if x["category"] == c):
                removed = f["review"] == "removed"
                with st.container(border=True):
                    st.caption(f"Page {f['page']} · {f['review'].capitalize() if f['review'] != 'pending' else 'Not yet reviewed'}")
                    quote = md_escape(f["quote"])
                    st.markdown("> " + (f"~~{quote}~~" if removed else quote))
                    b1, b2, b3, _ = st.columns([1, 1, 2, 4])
                    if removed:
                        b1.button("Restore", key=f"restore{f['id']}", on_click=act, args=(f["id"], "pending"))
                    else:
                        b1.button("Accept", key=f"accept{f['id']}", on_click=act, args=(f["id"], "accepted"),
                                  type="secondary" if f["review"] == "accepted" else "primary",
                                  disabled=f["review"] == "accepted")
                        b2.button("Remove", key=f"remove{f['id']}", on_click=act, args=(f["id"], "removed"))
                        qkey = f"q{f['id']}"
                        with b3.popover("Edit question" if f["question"] else "Ask senior lawyer"):
                            st.text_area("Question for the senior lawyer", value=f["question"] or "", key=qkey, height=100,
                                         placeholder="e.g. Does a transfer to an affiliate count as assignment here?",
                                         help="One question per finding. Saving new text reopens it; saving empty text removes it.")
                            st.button("Save question", key=f"saveq{f['id']}", on_click=save_question, args=(f["id"], qkey))
                        if f["question"]:
                            cls, text = QSTATE_CHIP[f["qstate"] or OPEN]
                            st.markdown(f'<span class="chip {cls}">{text}</span>', unsafe_allow_html=True)
                            st.markdown("**Your question:** " + md_escape(f["question"]))
                            if f["answer"]:
                                st.markdown("**Senior lawyer:** " + md_escape(f["answer"]))
                                if f["qstate"] == RESOLVED:
                                    st.button("Reopen", key=f"reopen{f['id']}", on_click=resolve, args=(f["id"], False))
                                else:
                                    st.button("Mark resolved", key=f"resolve{f['id']}", on_click=resolve, args=(f["id"], True))

"""Recording a run, saving it, and replaying it fresh: events, storage, pacing and the progress screen. No model is called."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # progress_ui.py sits next to app.py

from clause_review.pipeline import run_review
from clause_review.providers import MockProvider
from clause_review.replay import Recorder, duration, play
from clause_review.store import FOUND, NOT_FOUND, Store
from clause_review.view import load_results
from progress_ui import ProgressView

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "sample_contract.txt"
FILLER = "The parties acknowledge the general terms set out in this schedule. " * 12


def long_contract(tmp_path, parts=6):
    text = "\n\n".join(FILLER + f"Section {i}. This Agreement shall be governed by the laws of the State of Delaware." for i in range(parts))
    f = tmp_path / "long.txt"
    f.write_text(text)
    return f


def record(store, paths, **kw):
    rec = Recorder()
    pid = run_review(store, "p", paths, MockProvider(), on_event=rec, **kw)
    return pid, rec.events


def test_a_run_reports_each_step_in_order(tmp_path):
    f = long_contract(tmp_path)
    _, events = record(Store(), [f])
    kinds = [e["kind"] for e in events]
    assert kinds[:2] == ["run_start", "doc_start"] and kinds[-2:] == ["doc_done", "run_done"]
    chunks = [e for e in events if e["kind"] == "chunk"]
    assert [c["done"] for c in chunks] == list(range(1, chunks[0]["total"] + 1))
    assert events[1]["chunks"] == chunks[0]["total"] > 1
    assert all(a["t"] <= b["t"] for a, b in zip(events, events[1:]))
    done = events[-2]
    assert done["findings"] >= 1 and "Governing Law" in done["found"]


def test_a_failed_file_is_reported_not_skipped(tmp_path):
    bad = tmp_path / "empty.txt"
    bad.write_text("too short")
    _, events = record(Store(), [bad, SAMPLE])
    failed = [e for e in events if e["kind"] == "doc_failed"]
    assert failed and failed[0]["index"] == 0 and "no extractable text" in failed[0]["error"]
    assert [e["index"] for e in events if e["kind"] == "doc_done"] == [1]


def test_parallel_workers_still_give_a_whole_ordered_recording(tmp_path):
    _, events = record(Store(), [long_contract(tmp_path, parts=12)], workers=4)
    done = [e["done"] for e in events if e["kind"] == "chunk"]
    assert done == sorted(done) and done[-1] == events[1]["chunks"]


def test_a_broken_listener_cannot_break_the_review():
    def boom(kind, data):
        raise RuntimeError("screen crashed")
    s = Store()
    pid = run_review(s, "p", [SAMPLE], MockProvider(), on_event=boom)
    assert any(d["categories"][c] == FOUND for d in load_results(s, pid) for c in d["categories"])


def test_saved_run_round_trips_with_its_events(tmp_path):
    s = Store()
    pid, events = record(s, [SAMPLE])
    rid = s.save_run("Review 1", "mock", "", pid, ["Renewal", "Governing Law"], "3 calls", events)
    run = s.list_runs()[0]
    assert (run["id"], run["name"], run["provider"], run["project_id"], run["docs"]) == (rid, "Review 1", "mock", pid, 1)
    assert run["categories"] == ["Renewal", "Governing Law"] and run["duration"] == duration(events)
    assert s.run_events(rid) == events
    assert s.get_run(rid)["usage"] == "3 calls"


def test_replay_copy_starts_fresh_and_never_touches_the_original():
    s = Store()
    pid, _ = record(s, [SAMPLE])
    doc = load_results(s, pid)[0]
    first = doc["findings"][0]
    s.set_review(first["id"], "accepted")
    other = next(f for f in doc["findings"] if f["id"] != first["id"])
    s.set_review(other["id"], "removed")
    s.set_category_reviewed(doc["id"], first["category"], True)

    copy = s.clone_project(pid, "Replay 1")
    cdoc = load_results(s, copy)[0]
    assert cdoc["name"] == doc["name"] and len(cdoc["findings"]) == len(doc["findings"])
    assert {f["review"] for f in cdoc["findings"]} == {"pending"}
    assert not any(cdoc["reviewed"].values())
    assert all(cdoc["categories"][c] == (FOUND if any(f["category"] == c for f in cdoc["findings"]) else NOT_FOUND)
               for c in cdoc["categories"])

    s.set_review(cdoc["findings"][0]["id"], "removed")  # acting on the copy...
    after = load_results(s, pid)[0]  # ...leaves the original as it was left
    assert {f["id"]: f["review"] for f in after["findings"]}[first["id"]] == "accepted"
    assert {f["id"]: f["review"] for f in after["findings"]}[other["id"]] == "removed"


def test_play_keeps_the_original_pace_divided_by_speed():
    events = [{"t": 0.0, "kind": "a"}, {"t": 2.0, "kind": "b", "x": 1}, {"t": 5.0, "kind": "c"}]
    seen, slept = [], []
    waited = play(events, lambda k, d: seen.append((k, d)), speed=1.0, sleep=slept.append)
    assert seen == [("a", {}), ("b", {"x": 1}), ("c", {})] and slept == [2.0, 3.0] and waited == 5.0
    slept.clear()
    assert play(events, lambda k, d: None, speed=5.0, sleep=slept.append) == 1.0 and slept == [0.4, 0.6]


def test_skip_to_results_plays_everything_without_waiting():
    seen, slept = [], []
    waited = play([{"t": 0.0, "kind": "a"}, {"t": 99.0, "kind": "b"}], lambda k, d: seen.append(k), speed=None, sleep=slept.append)
    assert seen == ["a", "b"] and slept == [] and waited == 0.0


class FakeBar:
    def __init__(self, log, i):
        self.log, self.i = log, i

    def progress(self, value, text=""):
        self.log.append((self.i, round(value, 2), text))


class FakeBox:
    def __init__(self):
        self.bars, self.notes = [], []

    def markdown(self, text):
        self.notes.append(("markdown", text))

    def progress(self, value, text=""):
        self.bars.append((len(self.bars), round(value, 2), text))
        return FakeBar(self.bars, len(self.bars) - 1)

    def success(self, text):
        self.notes.append(("success", text))

    def error(self, text):
        self.notes.append(("error", text))


def test_progress_screen_draws_each_contract_from_a_recording(tmp_path):
    bad = tmp_path / "empty.txt"
    bad.write_text("too short")
    _, events = record(Store(), [bad, long_contract(tmp_path)])
    box = FakeBox()
    view = ProgressView(None, box)
    play(events, view.handle, speed=None)
    last = {}
    for i, value, text in box.bars:
        last[i] = (value, text)
    assert last[0][1].startswith("❌ empty.txt") and last[1][0] == 1.0 and last[1][1].startswith("✅ long.txt")
    assert ("success", "Done. The results are below.") in box.notes

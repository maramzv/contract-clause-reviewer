import csv
import io

import pytest

from clause_review.export import csv_text, questions_csv_text
from clause_review.store import ANSWERED, OPEN, RESOLVED, Store
from clause_review.view import load_results
from test_review_actions import finding_ids, reviewed


def state(s, fid):
    r = s.db.execute("SELECT question, answer, qstate FROM Finding WHERE id=?", (fid,)).fetchone()
    return r["question"], r["answer"], r["qstate"]


def test_a_question_is_open_then_answered_then_resolved():
    s, pid = reviewed()
    (fid,) = finding_ids(s, "Governing Law")
    assert state(s, fid) == (None, None, None)
    s.set_question(fid, "  Is this the right court?  ")
    assert state(s, fid) == ("Is this the right court?", None, OPEN)
    s.set_answer(fid, "Yes.")
    assert state(s, fid) == ("Is this the right court?", "Yes.", ANSWERED)
    s.set_resolved(fid)
    assert state(s, fid)[2] == RESOLVED
    s.set_resolved(fid, False)
    assert state(s, fid)[2] == ANSWERED


def test_changing_the_question_drops_the_old_answer_and_empty_text_clears_it():
    s, pid = reviewed()
    (fid,) = finding_ids(s, "Governing Law")
    s.set_question(fid, "One?")
    s.set_answer(fid, "A")
    s.set_question(fid, "One?")  # unchanged: the answer stays
    assert state(s, fid) == ("One?", "A", ANSWERED)
    s.set_question(fid, "Two?")
    assert state(s, fid) == ("Two?", None, OPEN)
    s.set_question(fid, "  ")
    assert state(s, fid) == (None, None, None)


def test_an_empty_answer_reopens_and_the_rules_are_enforced():
    s, pid = reviewed()
    (fid,) = finding_ids(s, "Governing Law")
    with pytest.raises(ValueError):
        s.set_answer(fid, "no question yet")
    with pytest.raises(ValueError):
        s.set_resolved(fid)
    s.set_question(fid, "Q?")
    with pytest.raises(ValueError):
        s.set_resolved(fid)  # not answered yet
    s.set_answer(fid, "A")
    s.set_answer(fid, "")
    assert state(s, fid) == ("Q?", None, OPEN)
    with pytest.raises(ValueError):
        s.set_question(9999, "x")


def test_the_results_and_both_csv_files_carry_question_and_answer():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    s.set_question(law, "Q?")
    s.set_answer(law, "A")
    f = next(x for x in load_results(s, pid)[0]["findings"] if x["id"] == law)
    assert (f["question"], f["answer"], f["qstate"]) == ("Q?", "A", ANSWERED)
    full = list(csv.DictReader(io.StringIO(csv_text(s, pid))))
    row = next(r for r in full if r["question"] == "Q?")
    assert row["answer"] == "A"
    only = list(csv.DictReader(io.StringIO(questions_csv_text(s, pid))))
    assert [(r["question"], r["answer"], r["state"]) for r in only] == [("Q?", "A", ANSWERED)]
    s.set_review(law, "removed")  # a removed finding drops out of the senior lawyer's list
    assert list(csv.DictReader(io.StringIO(questions_csv_text(s, pid)))) == []


def test_an_older_database_gets_the_new_columns(tmp_path):
    import sqlite3
    path = tmp_path / "old.db"
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE Finding(id INTEGER PRIMARY KEY, document_id INT, category TEXT, quote TEXT, start INT, end INT, "
               "page INT, source TEXT, review TEXT DEFAULT 'pending', question TEXT)")
    db.commit(); db.close()
    s = Store(str(path))
    cols = {r["name"] for r in s.db.execute("PRAGMA table_info(Finding)")}
    assert {"answer", "qstate"} <= cols


def test_a_replay_copy_starts_without_questions():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    s.set_question(law, "Q?")
    copy = s.clone_project(pid, "copy")
    assert all(f["question"] is None for d in load_results(s, copy) for f in d["findings"])

"""Marking a category as reviewed is a progress flag: it is saved, cleared, and never changes a category's status."""
import pytest

from clause_review.export import csv_text
from clause_review.store import NOT_FOUND
from clause_review.view import load_results
from test_review_actions import finding_ids, reviewed


def doc_id(s):
    return s.db.execute("SELECT id FROM Document").fetchone()[0]


def flags(s, pid, cats=("Governing Law", "Assignment")):
    return load_results(s, pid, list(cats))[0]["reviewed"]


def test_nothing_is_marked_reviewed_to_begin_with():
    s, pid = reviewed()
    assert flags(s, pid) == {"Governing Law": False, "Assignment": False}


def test_mark_and_clear_one_category_only():
    s, pid = reviewed()
    s.set_category_reviewed(doc_id(s), "Governing Law", True)
    assert flags(s, pid) == {"Governing Law": True, "Assignment": False}
    s.set_category_reviewed(doc_id(s), "Governing Law", False)
    assert flags(s, pid) == {"Governing Law": False, "Assignment": False}


def test_the_mark_is_kept_in_the_database_file(tmp_path):
    from clause_review.pipeline import run_review
    from clause_review.providers import MockProvider
    from clause_review.store import Store
    from test_review_actions import SAMPLE
    path = str(tmp_path / "r.db")
    s = Store(path)
    pid = run_review(s, "p", [SAMPLE], MockProvider(), categories=["Governing Law"])
    s.set_category_reviewed(doc_id(s), "Governing Law", True)
    s.db.close()
    assert load_results(Store(path), pid, ["Governing Law"])[0]["reviewed"] == {"Governing Law": True}


def test_marking_reviewed_never_changes_the_status():
    s, pid = reviewed()
    d = load_results(s, pid, ["Governing Law", "Assignment"])[0]["categories"]
    for cat in d:
        s.set_category_reviewed(doc_id(s), cat, True)
    assert load_results(s, pid, ["Governing Law", "Assignment"])[0]["categories"] == d
    # a category with nothing found stays flagged for checking even after it is marked reviewed
    ids = finding_ids(s, "Governing Law")
    assert len(ids) == 1
    s.set_review(ids[0], "removed")
    s.set_category_reviewed(doc_id(s), "Governing Law", True)
    assert load_results(s, pid, ["Governing Law"])[0]["categories"]["Governing Law"] == NOT_FOUND


def test_accepting_or_removing_a_finding_keeps_the_mark():
    s, pid = reviewed()
    s.set_category_reviewed(doc_id(s), "Governing Law", True)
    fid = finding_ids(s, "Governing Law")[0]
    s.set_review(fid, "accepted")
    s.set_review(fid, "removed")
    assert flags(s, pid)["Governing Law"] is True


def test_unknown_category_or_document_is_refused():
    s, pid = reviewed()
    with pytest.raises(ValueError):
        s.set_category_reviewed(doc_id(s), "Renewal", True)  # not part of this review
    with pytest.raises(ValueError):
        s.set_category_reviewed(999, "Governing Law", True)


def test_the_csv_is_unchanged_by_the_mark():
    s, pid = reviewed()
    before = csv_text(s, pid)
    s.set_category_reviewed(doc_id(s), "Governing Law", True)
    assert csv_text(s, pid) == before

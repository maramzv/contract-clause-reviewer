import csv
import io
from pathlib import Path

import pytest

from clause_review.export import csv_text
from clause_review.pipeline import run_review
from clause_review.providers import MockProvider
from clause_review.store import FAILED, FOUND, NOT_FOUND, Store
from clause_review.view import load_results

SAMPLE = Path(__file__).parent.parent / "samples" / "sample_contract.txt"


def reviewed(cats=("Governing Law", "Assignment")):
    s = Store()
    pid = run_review(s, "p", [SAMPLE], MockProvider(), categories=list(cats))
    return s, pid


def finding_ids(s, category):
    return [r[0] for r in s.db.execute("SELECT id FROM Finding WHERE category=? ORDER BY id", (category,))]


def rows(s, pid):
    return list(csv.DictReader(io.StringIO(csv_text(s, pid))))


def test_accept_and_remove_set_the_review_state():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    s.set_review(law, "accepted")
    assert s.db.execute("SELECT review FROM Finding WHERE id=?", (law,)).fetchone()[0] == "accepted"
    s.set_review(law, "removed")
    shown = [f for f in load_results(s, pid)[0]["findings"] if f["id"] == law]
    assert [f["review"] for f in shown] == ["removed"]  # still listed, so it can be restored
    assert s.db.execute("SELECT COUNT(*) FROM Finding WHERE id=?", (law,)).fetchone()[0] == 1


def test_bad_state_or_unknown_finding_is_refused():
    s, _ = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    with pytest.raises(ValueError):
        s.set_review(law, "rejected")
    with pytest.raises(ValueError):
        s.set_review(999999, "accepted")


def test_removing_the_only_finding_flags_the_category_and_restoring_clears_it():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    s.set_review(law, "removed")
    (doc,) = load_results(s, pid)
    assert doc["categories"]["Governing Law"] == NOT_FOUND
    gaps = [r for r in rows(s, pid) if r["category"] == "Governing Law"]
    # the removed quote stays in the file, marked removed, and the category is also listed as a gap
    assert [(g["review"], g["quote"].startswith("[")) for g in gaps] == [("removed", False), ("", True)]
    assert gaps[1]["quote"] == "[Not found, review required]"
    s.set_review(law, "pending")
    assert load_results(s, pid)[0]["categories"]["Governing Law"] == FOUND


def test_removing_one_of_several_findings_keeps_the_category_found():
    s, pid = reviewed(("Renewal",))
    ids = finding_ids(s, "Renewal")
    if len(ids) < 2:  # make a second finding in the same category
        s.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source) "
                     "SELECT document_id,category,'another passage about renewal',9000,9030,1,'regex' FROM Finding WHERE id=?", (ids[0],))
        s.db.commit()
        ids = finding_ids(s, "Renewal")
    s.set_review(ids[0], "removed")
    assert load_results(s, pid)[0]["categories"]["Renewal"] == FOUND


def test_failed_status_is_never_overwritten(tmp_path):
    s = Store()
    bad = tmp_path / "scan.txt"
    bad.write_text("x")
    pid = run_review(s, "p", [bad], MockProvider(), categories=["Renewal"])
    assert load_results(s, pid)[0]["categories"]["Renewal"] == FAILED


def test_csv_keeps_removed_findings_marked_as_removed():
    s, pid = reviewed()
    a, = finding_ids(s, "Assignment")
    law, = finding_ids(s, "Governing Law")
    s.set_review(a, "accepted")
    s.set_review(law, "removed")
    table = rows(s, pid)
    (assign,) = [r for r in table if r["category"] == "Assignment"]
    assert assign["review"] == "accepted" and assign["quote"].startswith("Neither party")
    law_rows = [r for r in table if r["category"] == "Governing Law"]
    removed = [r for r in law_rows if r["review"] == "removed"]
    assert len(removed) == 1 and not removed[0]["quote"].startswith("[")  # the rejected quote is still on record
    assert [r["quote"] for r in law_rows if r["quote"].startswith("[")] == ["[Not found, review required]"]


def test_export_counts_only_findings_still_standing():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    s.set_review(law, "removed")
    import io as _io
    from clause_review.export import write_csv
    n, gaps = write_csv(s, pid, _io.StringIO())
    live = s.db.execute("SELECT COUNT(*) FROM Finding WHERE review!='removed'").fetchone()[0]
    assert n == live and gaps >= 1

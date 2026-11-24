import csv
from pathlib import Path

from clause_review.chunk import chunk
from clause_review.export import export_csv
from clause_review.pipeline import run_review
from clause_review.providers import MockProvider
from clause_review.score import score
from clause_review.store import FAILED, FOUND, NOT_FOUND, Store
from clause_review.verify import verify

SAMPLE = Path(__file__).parent.parent / "samples" / "sample_contract.txt"
TEXT = SAMPLE.read_text()


def statuses(s):
    return {(r[0], r[1]): r[2] for r in s.db.execute("SELECT d.name,c.category,c.status FROM CategoryStatus c JOIN Document d ON d.id=c.document_id")}


def test_verify_keeps_verbatim_drops_paraphrase():
    ok = {"category": "Governing Law", "quote": "This Agreement shall be governed by the laws of the State of Delaware"}
    ok2 = {"category": "Governing Law", "quote": "This Agreement shall be governed\nby the laws of the State of Delaware"}  # whitespace differs
    bad = {"category": "Governing Law", "quote": "Delaware law applies to this contract in all respects"}
    kept, dropped = verify([ok, bad], TEXT)
    assert len(kept) == 1 and len(dropped) == 1
    assert TEXT[kept[0]["start"]:kept[0]["end"]] == kept[0]["quote"]
    assert len(verify([ok, ok2], TEXT)[0]) == 1  # deduped by span


def test_chunk_covers_text_with_offsets():
    long = TEXT * 20
    for c in chunk(long, size=500, overlap=50):
        assert long[c.start:c.start + len(c.text)] == c.text


def test_end_to_end_found_and_not_found(tmp_path):
    s = Store()
    run_review(s, "p", [SAMPLE], MockProvider())
    st = statuses(s)
    assert st[("sample_contract.txt", "Governing Law")] == FOUND
    assert st[("sample_contract.txt", "Assignment")] == FOUND
    # remove governing law -> must say "review required", not silently empty
    f = tmp_path / "nolaw.txt"
    f.write_text(TEXT.split("13. Governing Law")[0])
    run_review(s, "p2", [f], MockProvider())
    assert statuses(s)[("nolaw.txt", "Governing Law")] == NOT_FOUND


def test_paraphrasing_provider_cannot_add_unverified_findings(tmp_path):
    s = Store()
    f = tmp_path / "c.txt"
    f.write_text("Boilerplate. " * 10 + "\n\nThis Agreement shall be governed by the laws of Delaware.\n")
    run_review(s, "p", [f], MockProvider(paraphrase=True))
    srcs = {r[0] for r in s.db.execute("SELECT source FROM Finding")}
    assert srcs <= {"regex"}  # every llm paraphrase was dropped


def test_failed_documents_are_flagged(tmp_path):
    s = Store()
    bad = tmp_path / "empty.txt"
    bad.write_text("x")
    run_review(s, "p", [bad], MockProvider())
    assert set(statuses(s).values()) == {FAILED}


def test_export_and_scorer(tmp_path):
    s = Store()
    pid = run_review(s, "p", [SAMPLE], MockProvider())
    out = tmp_path / "o.csv"
    n, gaps = export_csv(s, pid, out)
    rows = list(csv.DictReader(open(out)))
    assert n > 0 and any(r["category"] == "Governing Law" for r in rows)
    gold = {"Governing Law": [(TEXT.index("This Agreement shall be governed"), TEXT.index("principles.") + 11)]}
    pred = {"Governing Law": [(r[0], r[1]) for r in s.db.execute("SELECT start,end FROM Finding WHERE category='Governing Law'")]}
    assert score(gold, pred)["Governing Law"]["recall"] == 1.0


# --- concurrency and spend guard -------------------------------------------------------------------------------

import pytest

from clause_review.providers import BudgetExceeded, Meter


def long_contract(tmp_path, copies=60):
    # numbered copies, so no two chunks are identical (identical chunks would share one cached response)
    text = "\n\n".join(f"Agreement number {i}.\n\n{TEXT}" for i in range(copies))
    f = tmp_path / "long.txt"
    f.write_text(text)
    return f, len(chunk(text))


def finding_set(s):
    return sorted(tuple(r) for r in s.db.execute("SELECT category,start,end,quote,source FROM Finding"))


def test_parallel_extraction_matches_serial(tmp_path):
    f, n = long_contract(tmp_path)
    assert n >= 8
    serial, parallel = Store(), Store()
    run_review(serial, "p", [f], MockProvider(), workers=1)
    run_review(parallel, "p", [f], MockProvider(), workers=4)
    assert finding_set(serial) == finding_set(parallel) and finding_set(serial)


def test_budget_stops_run_and_paid_responses_are_kept(tmp_path):
    f, n = long_contract(tmp_path)
    s = Store()
    meter = Meter(price_in=1000, price_out=1000, budget=2.0)  # each mock call costs about $1
    with pytest.raises(BudgetExceeded):
        run_review(s, "p", [f], MockProvider(meter=meter))
    assert 0 < meter.calls < n and meter.cost >= 2.0
    assert set(statuses(s).values()) == {FAILED}  # a budget stop is never reported as "not found"
    cached = s.db.execute("SELECT COUNT(*) FROM LLMCache").fetchone()[0]
    assert cached == meter.calls  # every paid response was saved
    rerun = Meter()  # no budget: finish the job
    run_review(s, "p2", [f], MockProvider(meter=rerun))
    assert rerun.calls == n - cached  # earlier chunks come from the cache, not from a new payment


def test_budget_stop_with_parallel_workers_overshoots_by_at_most_the_workers(tmp_path):
    f, n = long_contract(tmp_path)
    meter = Meter(price_in=1000, price_out=1000, budget=2.0)
    with pytest.raises(BudgetExceeded):
        run_review(Store(), "p", [f], MockProvider(meter=meter), workers=4)
    assert meter.calls <= 3 + 4 and meter.calls < n


def test_budget_needs_prices():
    with pytest.raises(ValueError):
        Meter(budget=5.0)

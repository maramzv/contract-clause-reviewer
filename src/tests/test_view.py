from pathlib import Path

from clause_review.pipeline import run_review
from clause_review.providers import MockProvider
from clause_review.store import FAILED, FOUND, NOT_FOUND, Store
from clause_review.view import load_results, md_escape

SAMPLE = Path(__file__).parent.parent / "samples" / "sample_contract.txt"


def test_results_show_found_findings_with_page_and_selected_categories_only():
    s = Store()
    cats = ["Governing Law", "Assignment"]
    pid = run_review(s, "p", [SAMPLE], MockProvider(), categories=cats)
    (doc,) = load_results(s, pid, cats)
    assert set(doc["categories"]) == set(cats) and doc["status"] == "ok"
    assert doc["categories"]["Governing Law"] == FOUND
    law = [f for f in doc["findings"] if f["category"] == "Governing Law"]
    source = " ".join(SAMPLE.read_text().split())
    assert law and all(f["page"] == 1 and " ".join(f["quote"].split()) in source for f in law)
    assert {f["category"] for f in doc["findings"]} <= set(cats)


def test_no_category_is_ever_blank_and_failed_files_are_listed(tmp_path):
    s = Store()
    bad = tmp_path / "scan.txt"
    bad.write_text("x")  # too little text: stands in for a scanned PDF
    pid = run_review(s, "p", [SAMPLE, bad], MockProvider())
    good, failed = load_results(s, pid)
    assert all(v in (FOUND, NOT_FOUND) for v in good["categories"].values())
    assert failed["status"] == "failed" and "no extractable text" in failed["error"]
    assert all(v == FAILED for v in failed["categories"].values()) and failed["findings"] == []


def test_markdown_escape_neutralises_quotation_text():
    q = "Fees of $5 * 2 [see](http://x) <b>bold</b> _under_ #1"
    out = md_escape(q)
    for ch in "$*[]<>_#":
        assert out.count(ch) == out.count("\\" + ch)  # every special character is escaped
    assert md_escape("a\n  b") == "a b"


def test_section_numbers_and_dashes_do_not_become_lists():
    assert md_escape("2. Termination. Either party") == "2\\. Termination. Either party"
    assert md_escape("- item").startswith("\\-")


def test_failed_file_is_listed_by_name_not_path(tmp_path):
    s = Store()
    d = tmp_path / "deep" / "dir"
    d.mkdir(parents=True)
    bad = d / "scan.txt"
    bad.write_text("x")
    pid = run_review(s, "p", [bad], MockProvider())
    assert load_results(s, pid)[0]["name"] == "scan.txt"

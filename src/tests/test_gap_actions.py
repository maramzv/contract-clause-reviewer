"""A clause where nothing was found: the reviewer can ask the Senior Lawyer about it and can highlight the passage herself.
Both live in the same table as passages, so these tests check that they are never counted as something the tool found."""
import csv
import io

from clause_review.export import csv_text, questions_csv_text
from clause_review.review_view import found_by_you, gap_question, locate, overview_stats, question_flag
from clause_review.store import FOUND, NOT_FOUND
from clause_review.view import load_results
from test_review_actions import finding_ids, reviewed
from workspace_html import apply_action, build_view

CATS = ["Governing Law", "Assignment"]


def setup(cats=CATS):
    s, pid = reviewed(cats)
    return s, pid, lambda: load_results(s, pid, cats)


def a_gap(s, docs):
    """A (document, clause) with nothing found: remove the only passage of Governing Law."""
    (law,) = finding_ids(s, "Governing Law")
    s.set_review(law, "removed")
    d = docs()[0]
    assert d["categories"]["Governing Law"] == NOT_FOUND
    return d["id"], "Governing Law"


def test_locate_ignores_line_wrapping_and_returns_the_contracts_own_words():
    text = "Section 9.  This Agreement is governed\nby the laws of New York.\n\nNext."
    a, b = locate(text, "governed by the laws of New York.")
    assert text[a:b] == "governed\nby the laws of New York."
    assert locate(text, "words that are not there") is None and locate(text, "   ") is None


def test_a_question_on_a_gap_is_kept_apart_from_passages():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": "Could this sit under Miscellaneous?"}, docs())
    d = docs()[0]
    assert gap_question(d, cat)["question"] == "Could this sit under Miscellaneous?"
    assert all(f["source"] != "gap" for f in d["findings"])  # the placeholder row is never a passage
    assert d["categories"][cat] == NOT_FOUND  # and the clause is still a gap
    assert question_flag(d, cat) == "q"
    st = overview_stats(docs(), CATS)
    assert st["waiting"] == 1 and st["total"] == len(d["findings"])  # counted as a question, never as a passage


def test_the_senior_lawyer_can_answer_a_gap_question_and_the_reviewer_resolves_it():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": "Is it absent?"}, docs())
    q = gap_question(docs()[0], cat)
    s.set_answer(q["id"], "Yes, check the schedule.")
    assert question_flag(docs()[0], cat) == "a" and overview_stats(docs(), CATS)["answered"] == 1
    apply_action(s, {}, {"type": "resolve", "id": q["id"], "on": True}, docs())
    assert question_flag(docs()[0], cat) == "" and overview_stats(docs(), CATS)["answered"] == 0


def test_saving_empty_text_removes_the_gap_question():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": "Is it absent?"}, docs())
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": ""}, docs())
    assert gap_question(docs()[0], cat) is None and overview_stats(docs(), CATS)["waiting"] == 0
    other = {"type": "gapask", "doc": did, "name": "Termination", "text": "x"}  # a clause that is not in this review
    apply_action(s, {}, other, docs())
    assert s.db.execute("SELECT COUNT(*) FROM Finding WHERE source='gap'").fetchone()[0] == 1


def test_gap_questions_reach_the_senior_lawyers_csv_and_not_the_full_table():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": "Is it absent?"}, docs())
    only = list(csv.DictReader(io.StringIO(questions_csv_text(s, pid))))
    assert [(r["category"], r["quote"], r["question"]) for r in only] == [(cat, "[Nothing found]", "Is it absent?")]
    full = list(csv.DictReader(io.StringIO(csv_text(s, pid))))
    assert [r["quote"] for r in full if r["category"] == cat and r["quote"].startswith("[")] == ["[Not found, review required]"]  # listed as a gap once


def test_selecting_text_adds_a_passage_found_by_the_reviewer():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    text = s.document_text(did)
    sentence = " ".join(text.split()[25:37])
    state = {}
    apply_action(s, state, {"type": "addpassage", "doc": did, "name": cat, "text": sentence}, docs())
    d = docs()[0]
    new = [f for f in d["findings"] if f["category"] == cat and f["source"] == "manual"]
    assert len(new) == 1 and new[0]["review"] == "accepted"
    assert " ".join(new[0]["quote"].split()) == sentence and text[new[0]["start"]:new[0]["end"]] == new[0]["quote"]  # the contract's own words
    assert d["categories"][cat] == FOUND and found_by_you(d, cat)
    v = build_view(s, docs(), state)
    assert v["current"]["mine"] and v["findings"][0]["mine"] and v["findings"][0]["id"] == new[0]["id"]
    assert "found by you" in v["notice"]
    who = [r["found_by"] for r in csv.DictReader(io.StringIO(csv_text(s, pid))) if not r["quote"].startswith("[")]
    assert who.count("Reviewer") == 1 and set(who) == {"Reviewer", "Clautra"}  # the table says who found each passage


def test_a_highlight_that_is_not_in_the_contract_is_refused_with_a_message():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    state = {}
    apply_action(s, state, {"type": "addpassage", "doc": did, "name": cat, "text": "this sentence was never in the contract"}, docs())
    assert not any(f["source"] == "manual" for f in docs()[0]["findings"])
    assert "could not be matched" in build_view(s, docs(), state)["notice"]


def test_removing_a_passage_found_by_you_makes_the_clause_a_gap_again():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    text = s.document_text(did)
    apply_action(s, {}, {"type": "addpassage", "doc": did, "name": cat, "text": " ".join(text.split()[20:30])}, docs())
    (mine,) = [f for f in docs()[0]["findings"] if f["source"] == "manual"]
    s.set_review(mine["id"], "removed")
    assert docs()[0]["categories"][cat] == NOT_FOUND and not found_by_you(docs()[0], cat)


def test_a_gap_question_does_not_make_a_clause_look_found_and_is_not_copied_into_a_replay():
    s, pid, docs = setup()
    did, cat = a_gap(s, docs)
    apply_action(s, {}, {"type": "gapask", "doc": did, "name": cat, "text": "Is it absent?"}, docs())
    s.set_review(finding_ids(s, "Assignment")[0], "accepted")  # touching another clause must not flip this one
    assert docs()[0]["categories"][cat] == NOT_FOUND
    copy = s.clone_project(pid, "copy")
    d = load_results(s, copy, CATS)[0]
    assert d["gap_questions"] == {}  # a fresh replay starts without questions


def test_a_saved_review_has_a_title_a_date_and_a_one_line_label():
    from clause_review.review_view import run_label, run_when
    s, pid, docs = setup()
    rid = s.save_run("Company purchase", "mock", "", pid, CATS, "demo", [{"t": 0, "kind": "run_start", "documents": ["a", "b", "c"]}])
    run = s.run_for_project(pid)
    assert run["id"] == rid and run["name"] == "Company purchase" and run["docs"] == 3
    label = run_label(run)
    assert label.startswith("Company purchase · 3 contracts · ") and run_when(run["created"]) in label
    assert run_when("2026-11-11 09:15:03", with_time=True).startswith("11 Nov at ") and run_when(None) == ""
    assert run_label({"name": "Lease", "docs": 1, "created": None}) == "Lease · 1 contract"
    assert s.run_for_project(99999) is None


def test_the_review_title_becomes_a_safe_file_name():
    from clause_review.export import file_stem
    assert file_stem("Company purchase") == "Company_purchase"
    assert file_stem("  Kiosk / Waste2Energy: deal #2!  ") == "Kiosk_Waste2Energy_deal_2"
    assert file_stem("") == "clause_review" and file_stem(None) == "clause_review" and file_stem("///") == "clause_review"


def test_page_breaks_are_dividers_and_a_highlight_across_a_break_is_split_around_it():
    from clause_review.review_view import passage_html
    from workspace_html import readable
    text = "Page one text. The parties agree to this clause and\nit goes on.\nPage two starts here and ends."
    start = text.index("this clause")
    pages = [0, text.index("it goes on")]
    html_, lo, hi = passage_html(text, [(start, text.index("two starts"))], len(text), len(text), pages)
    out = readable(html_)
    assert out.count('class="pg"') == 2 and '<span>Page 1</span>' in out and '<span>Page 2</span>' in out
    assert "\x00" not in out and "\x04" not in out
    assert out.count("<mark>") == 2  # the highlight is closed before the page marker and opened again after it
    assert readable(passage_html(text, [], len(text), len(text))[0]).count('class="pg"') == 0  # a text file has none


def test_a_pdfs_page_starts_are_stored_and_the_findings_get_real_page_numbers(tmp_path):
    from pathlib import Path
    from clause_review.pipeline import run_review
    from clause_review.providers import MockProvider
    from clause_review.store import Store
    pdf = Path(__file__).parent.parent / "samples" / "contracts" / "contract_06.pdf"
    s = Store(); pid = run_review(s, "p", [pdf], MockProvider(), categories=["Governing Law", "Assignment"])
    did = s.db.execute("SELECT id FROM Document").fetchone()[0]
    starts = s.page_starts(did)
    assert len(starts) == 8 and starts[0] == 0 and starts == sorted(starts)
    pages = [r[0] for r in s.db.execute("SELECT page FROM Finding")]
    assert pages and all(1 <= p <= 8 for p in pages) and max(pages) > 1

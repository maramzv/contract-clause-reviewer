from clause_review.review_view import (build_slots, clause_state, is_gap, needs_work, passage_html, search_snippets,
                                       split_title)
from clause_review.store import NOT_FOUND
from clause_review.view import load_results
from test_review_actions import finding_ids, reviewed


def test_split_title_separates_code_title_and_party():
    assert split_title("contract_01 - Endorsement Licensing and Co-Branding Agreement (MusclePharm).txt") == (
        "Endorsement Licensing and Co-Branding Agreement", "MusclePharm", "contract_01")
    assert split_title("contract_08 - Cooperation Agreement, 50MWp Solar Project (Fenyi County).txt")[:2] == (
        "Cooperation Agreement, 50MWp Solar Project", "Fenyi County")
    assert split_title("contract_10 - Outsource Technology Development Agreement") == (
        "Outsource Technology Development Agreement", "", "contract_10")
    assert split_title("sample - Sample master services agreement (short).txt") == (
        "Sample master services agreement (short)", "", "sample")
    assert split_title("plain.pdf") == ("plain", "", "")


def test_slots_follow_documents_then_clauses():
    s, pid = reviewed()
    docs = load_results(s, pid, ["Governing Law", "Assignment"])
    assert build_slots(docs) == [(docs[0]["id"], "Assignment"), (docs[0]["id"], "Governing Law")]


def test_only_undecided_findings_are_work_and_a_gap_is_visible_but_never_a_task():
    s, pid = reviewed()
    (law,) = finding_ids(s, "Governing Law")
    doc = lambda: load_results(s, pid)[0]
    assert needs_work(doc(), "Governing Law") and not is_gap(doc(), "Governing Law")
    assert clause_state(doc(), "Governing Law") == "found"
    s.set_review(law, "accepted")
    assert not needs_work(doc(), "Governing Law") and clause_state(doc(), "Governing Law") == "accepted"
    s.set_review(law, "removed")  # nothing left: a gap the reader is told about, but no longer something to do
    assert doc()["categories"]["Governing Law"] == NOT_FOUND
    assert is_gap(doc(), "Governing Law") and not needs_work(doc(), "Governing Law")
    assert clause_state(doc(), "Governing Law") == "check"


def test_passage_marks_the_quotation_and_never_passes_contract_text_through_as_html():
    text = "Intro line.\nSecond <b>line</b>.\nThe quote is here & now.\nTail line.\n" + "x" * 50
    a = text.index("The quote")
    b = a + len("The quote is here & now.")
    out, lo, hi = passage_html(text, [(a, b)], before=5, after=5)
    assert "<mark>The quote is here &amp; now.</mark>" in out
    assert "\n" not in out and lo <= a and hi >= b
    whole, lo, hi = passage_html(text, [(a, b)])
    assert (lo, hi) == (0, len(text))
    assert "&lt;b&gt;line&lt;/b&gt;" in whole and "<b>" not in whole


def test_passage_without_quotations_shows_the_start_and_overlaps_merge():
    text = "A" * 10 + "\n" + "B" * 6000
    out, lo, hi = passage_html(text, [])
    assert lo == 0 and "<mark>" not in out and hi < len(text)
    out, _, _ = passage_html("abcdefghij", [(1, 5), (3, 8)])
    assert out.count("<mark>") == 1 and "<mark>bcdefgh</mark>" in out


def test_long_runs_of_blank_lines_collapse_to_one_gap():
    text = "Header\n\n\n\n   \n\n\nThe clause here.\nNext line."
    a = text.index("The clause")
    out, _, _ = passage_html(text, [(a, a + len("The clause here."))])
    assert out == "Header<br><br><mark>The clause here.</mark><br>Next line."


def test_search_snippets_are_literal_case_insensitive_and_capped():
    text = "Assignment. " * 20 + "The (Parent) may not assign."
    snips, total = search_snippets(text, "assign", limit=3)
    assert total == 21 and len(snips) == 3 and all("<mark>" in s for s in snips)
    one, n = search_snippets(text, "(Parent)")
    assert n == 1 and "<mark>(Parent)</mark>" in one[0]
    assert search_snippets(text, "a") == ([], 0)
    assert search_snippets(text, "   ") == ([], 0)



def test_display_name_drops_the_file_number_and_extension_unless_dev():
    from clause_review.review_view import display_name
    n = "contract_02 - Cooperation Agreement (HPIL Energytech and Ginares).txt"
    assert display_name(n) == "Cooperation Agreement (HPIL Energytech and Ginares)"
    assert display_name(n, dev=True) == "contract_02 · Cooperation Agreement (HPIL Energytech and Ginares)"
    assert display_name("Master services.pdf") == "Master services"


def test_overview_stats_count_progress_questions_and_gaps():
    from clause_review.review_view import overview_stats
    s, pid = reviewed()
    cats = ["Governing Law", "Assignment"]
    docs = lambda: load_results(s, pid, cats)
    (law,) = finding_ids(s, "Governing Law")
    (assign,) = finding_ids(s, "Assignment")
    st0 = overview_stats(docs(), cats)
    assert (st0["total"], st0["pending"], st0["decided"], st0["nothing"], st0["failed"]) == (2, 2, 0, 0, 0)
    assert st0["found_in"] == {"Governing Law": 1, "Assignment": 1} and sum(st0["left"].values()) == 2
    s.set_review(law, "accepted")
    s.set_review(assign, "removed")
    s.set_question(law, "Which law applies?")
    st1 = overview_stats(docs(), cats)
    assert (st1["pending"], st1["accepted"], st1["removed"], st1["decided"], st1["nothing"]) == (0, 1, 1, 2, 1)
    assert st1["waiting"] == 1 and st1["answered"] == 0
    s.set_answer(law, "English law.")
    st2 = overview_stats(docs(), cats)
    assert st2["waiting"] == 0 and st2["answered"] == 1 and st2["answered_ids"] == [law]

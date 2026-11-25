from types import SimpleNamespace

from clause_review.miss_check import ALSO_MENTIONS, Offline, also_mentions, check, classify_misses, sentence_spans
from clause_review.store import Store

RESTRICTION = "Neither party may assign this Agreement without the prior written consent of the other party."
CONSEQUENCE = "Any purported assignment in violation of this paragraph shall be void."
BINDING = "This Agreement binds and benefits the parties and their successors and assigns."
TEXT = f"1. Term. This Agreement lasts two years.\n\n12. Assignment. {RESTRICTION} {CONSEQUENCE} {BINDING}\n"


def span(sentence):
    a = TEXT.index(sentence)
    return a, a + len(sentence)


def test_a_miss_is_a_gap_when_nothing_was_shown():
    assert classify_misses([span(RESTRICTION)], []) == {"matched": 0, "missed": 1, "kind": "gap"}


def test_a_miss_is_silent_when_only_wrong_passages_were_shown():
    assert classify_misses([span(CONSEQUENCE)], [span(BINDING)]) == {"matched": 0, "missed": 1, "kind": "wrong"}


def test_a_miss_is_silent_and_partial_when_another_labeled_passage_was_found():
    got = classify_misses([span(RESTRICTION), span(CONSEQUENCE)], [span(RESTRICTION)])
    assert got == {"matched": 1, "missed": 1, "kind": "partial"}


def test_nothing_missed_has_no_kind():
    assert classify_misses([span(RESTRICTION)], [span(RESTRICTION)])["kind"] is None


def test_the_consequence_rule_finds_the_void_sentence_and_not_the_successors_line():
    found = [TEXT[a:b] for a, b in sentence_spans(TEXT, ALSO_MENTIONS["Assignment"])]
    assert CONSEQUENCE in found
    assert BINDING not in found


def test_the_list_leaves_out_what_is_already_shown():
    extra = also_mentions(TEXT, ALSO_MENTIONS["Assignment"], [span(CONSEQUENCE)])
    assert extra == []
    extra = also_mentions(TEXT, ALSO_MENTIONS["Assignment"], [span(RESTRICTION)])
    assert [TEXT[a:b] for a, b in extra] == [CONSEQUENCE]


def test_a_contract_without_saved_replies_is_skipped_not_paid_for():
    con = SimpleNamespace(text=TEXT, gold={"Assignment": [span(CONSEQUENCE)]})
    report, skipped = check([con], ["Assignment"], Store())
    assert skipped == 1 and report["Assignment"]["contracts"] == 0


def test_offline_files_replies_under_the_real_providers_name_and_model(monkeypatch):
    monkeypatch.setenv("CLAUSE_MODEL", "some-model")
    assert (Offline().name, Offline().model) == ("anthropic", "some-model")


def test_a_check_on_two_categories_still_finds_replies_saved_for_all_five():
    # Regression: asking about fewer categories builds a different prompt, so every saved reply was missed.
    import json

    from clause_review.categories import CATEGORIES
    from clause_review.pipeline import find_findings
    from clause_review.providers import Provider

    class Canned(Provider):
        name, model = "anthropic", "claude-sonnet-5-5"

        def _complete(self, prompt):
            return json.dumps([]), 0, 0

    cache = Store()
    find_findings(TEXT, list(CATEGORIES), Canned(), cache=cache)
    con = SimpleNamespace(text=TEXT, gold={"Assignment": [], "Change of Control": []})
    _, skipped = check([con], ["Assignment", "Change of Control"], cache)
    assert skipped == 0


def test_end_to_end_on_saved_replies_reports_a_silent_partial_miss_and_that_the_list_surfaces_it():
    import json

    from clause_review.pipeline import find_findings
    from clause_review.providers import Provider

    class Canned(Provider):  # stands in for the paid run that saved its replies
        name, model = "anthropic", "claude-sonnet-5-5"

        def _complete(self, prompt):
            return json.dumps([{"category": "Assignment", "quote": RESTRICTION}]), 0, 0

    cache = Store()
    from clause_review.categories import CATEGORIES
    find_findings(TEXT, list(CATEGORIES), Canned(), cache=cache)  # the paid run asks about all five categories
    con = SimpleNamespace(text=TEXT, gold={"Assignment": [span(RESTRICTION), span(CONSEQUENCE)]})
    report, skipped = check([con], ["Assignment"], cache)  # the check: reads the saved reply, calls nothing
    r = report["Assignment"]
    assert skipped == 0
    assert (r["labeled"], r["matched"], r["partial"], r["gap"], r["wrong"]) == (2, 1, 1, 0, 0)
    assert r["surfaced"] == 1 and r["list_lengths"] == [1]


def test_diagnose_names_the_provider_and_model_that_have_saved_replies():
    import hashlib

    from clause_review.categories import CATEGORIES
    from clause_review.chunk import chunk
    from clause_review.extract import PROMPT, describe
    from clause_review.miss_check import diagnose

    cache = Store()
    for ch in chunk(TEXT):
        pr = PROMPT.format(cats="\n".join(describe(c) for c in CATEGORIES), chunk=ch.text)
        cache.put(hashlib.sha256(f"anthropic|claude-sonnet-4-5|{pr}".encode()).hexdigest(), "[]")
    out = diagnose([SimpleNamespace(text=TEXT)], cache)
    assert "anthropic | claude-sonnet-4-5: 1 of 1" in out and "claude-sonnet-5-5:" not in out
    assert "no provider" in diagnose([SimpleNamespace(text=TEXT)], Store())

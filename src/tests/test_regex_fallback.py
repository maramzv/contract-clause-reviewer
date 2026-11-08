"""The keyword (regex) pass is a backstop: its findings are kept only where the model found nothing in that category."""
import json

from clause_review.pipeline import find_findings, regex_only_as_fallback
from clause_review.providers import Provider

TEXT = (
    "1. Term. This Agreement renews for successive one year terms unless either party gives notice.\n\n"
    "2. Merger. Nothing in this section limits the merger clause of the parent company records.\n\n"
    "3. Governing Law. This Agreement shall be governed by the laws of the State of New York, without regard to conflicts.\n"
)


class Fixed(Provider):
    """A model stand-in that answers with a fixed list of quotes."""
    name = "fixed"

    def __init__(self, quotes):
        super().__init__()
        self.quotes = quotes

    def _complete(self, prompt):
        return json.dumps(self.quotes), 1, 1


def f(cat, source, start=0):
    return {"category": cat, "source": source, "start": start, "end": start + 20, "quote": "x" * 20}


def test_keeps_the_model_and_drops_regex_in_the_same_category():
    out = regex_only_as_fallback([f("Renewal", "llm", 0), f("Renewal", "regex", 100)])
    assert [(x["source"], x["start"]) for x in out] == [("llm", 0)]


def test_keeps_regex_where_the_model_found_nothing_in_that_category():
    out = regex_only_as_fallback([f("Renewal", "llm"), f("Change of Control", "regex", 50)])
    assert {(x["category"], x["source"]) for x in out} == {("Renewal", "llm"), ("Change of Control", "regex")}


def test_the_rule_is_per_category_not_per_contract():
    out = regex_only_as_fallback([f("Renewal", "llm"), f("Governing Law", "regex", 50), f("Renewal", "regex", 90)])
    assert {(x["category"], x["source"]) for x in out} == {("Renewal", "llm"), ("Governing Law", "regex")}


def test_empty_input():
    assert regex_only_as_fallback([]) == []


def test_pipeline_end_to_end_model_clause_replaces_regex_hits_and_regex_fills_the_gap():
    model_quote = "This Agreement shall be governed by the laws of the State of New York, without regard to conflicts."
    found = find_findings(TEXT, ["Renewal", "Change of Control", "Governing Law"],
                          Fixed([{"category": "Governing Law", "quote": model_quote}]))
    by = {(x["category"], x["source"]) for x in found}
    assert ("Governing Law", "llm") in by and ("Governing Law", "regex") not in by  # the model found it
    assert ("Renewal", "regex") in by            # the model found no Renewal: the keyword hit is kept as a backstop
    assert ("Change of Control", "regex") in by  # same for Change of Control
    for x in found:
        assert TEXT[x["start"]:x["end"]] == x["quote"]  # every finding is still verbatim


def test_a_model_quote_that_is_not_in_the_contract_does_not_suppress_the_regex_backstop():
    found = find_findings(TEXT, ["Renewal"], Fixed([{"category": "Renewal", "quote": "The term renews every year forever and ever."}]))
    assert [(x["category"], x["source"]) for x in found] == [("Renewal", "regex")]

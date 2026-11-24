from clause_review.chunk import Chunk
from clause_review.extract import MAX_SENTENCE, regex_candidates
from clause_review.pipeline import run_review
from clause_review.providers import MockProvider
from clause_review.store import Store
from clause_review.verify import verify

WRAPPED = ("1. Term. This Agreement starts on the Effective Date.\n"
           "It shall automatically renew for successive one-year terms unless either party gives sixty days\n"
           "notice of non-renewal. 2. Fees. Fees are due monthly.\n")


def quotes(text, cat="Renewal"):
    return [c["quote"] for c in regex_candidates(Chunk(0, text), [cat])]


def test_regex_hit_is_the_whole_sentence_not_one_line():
    q = quotes(WRAPPED)
    assert q and all(x.startswith("It shall automatically renew") for x in q[:1])
    assert any(x.endswith("notice of non-renewal.") and "\n" in x for x in q)  # the wrapped line is inside one quote
    assert not any("Fees are due" in x for x in q)  # and the next sentence is not


def test_overlong_sentence_falls_back_to_the_line():
    text = "This Agreement shall renew for successive terms " + "and so on, " * 150 + "\nforever and ever.\n"  # sentence is over the cap
    (q, *_) = quotes(text)
    assert q.startswith("This Agreement shall renew") and "forever" not in q  # only the matched line, not the sentence


def test_model_quote_beats_overlapping_regex_fragments():
    cands = [
        {"category": "Renewal", "quote": "automatically renew for successive one-year terms unless either party gives sixty days", "source": "regex"},
        {"category": "Renewal", "quote": "notice of non-renewal.", "source": "regex"},
        {"category": "Renewal", "quote": "It shall automatically renew for successive one-year terms unless either party gives sixty days notice of non-renewal.", "source": "llm"},
    ]
    kept, _ = verify(cands, WRAPPED)
    assert [k["source"] for k in kept] == ["llm"]
    assert kept[0]["quote"].startswith("It shall automatically renew") and kept[0]["quote"].endswith("non-renewal.")


def test_wrapped_clause_is_one_finding_end_to_end(tmp_path):
    f = tmp_path / "c.txt"
    f.write_text(WRAPPED)
    s = Store()
    run_review(s, "p", [f], MockProvider(), categories=["Renewal"])
    rows = s.db.execute("SELECT quote, source FROM Finding").fetchall()
    assert len(rows) == 1 and rows[0]["quote"].endswith("notice of non-renewal.")

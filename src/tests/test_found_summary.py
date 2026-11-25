import pytest

from clause_review.review_view import found_summary


def f(page):
    return {"page": page, "review": "pending"}


@pytest.mark.parametrize("live, expected", [
    ([f(8)], "Found 1 passage, page 8."),
    ([f(31), f(8)], "Found 2 passages, pages 8 and 31."),
    ([f(8), f(8)], "Found 2 passages, page 8."),
    ([f(31), f(8), f(15)], "Found 3 passages, pages 8, 15 and 31."),
    ([f(None), f(None)], "Found 2 passages."),
    ([f(None)], "Found 1 passage."),
    ([f(8), f(None)], "Found 2 passages, page 8."),
])
def test_found_summary_wording(live, expected):
    assert found_summary(live) == expected


def test_found_summary_is_none_when_nothing_is_live():
    assert found_summary([]) is None


def test_looked_for_comes_from_the_category_definition(monkeypatch):
    from clause_review import review_view
    from clause_review.categories import CATEGORIES

    live = [f(8), f(31)]
    text = review_view.found_caption("Assignment", live)
    desc = CATEGORIES["Assignment"]["description"]
    assert text == (f"Looked for: {desc[:1].lower()}{desc[1:]} Found 2 passages, pages 8 and 31. "
                    "Check the rest of the contract for other wording.")
    monkeypatch.setitem(CATEGORIES["Assignment"], "description", "Another definition.")
    assert review_view.found_caption("Assignment", live).startswith("Looked for: another definition.")
    assert review_view.found_caption("Assignment", []) is None

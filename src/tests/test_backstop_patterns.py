"""The keyword patterns are a backstop, so they must not fire on every sentence that merely contains "acquisition" or "renew"."""
from clause_review.categories import COMPILED


def hits(cat, text):
    return any(p.search(text) for p in COMPILED[cat])


def test_change_of_control_matches_wording_and_merger_with_a_right():
    assert hits("Change of Control", "Either party may terminate this Agreement upon a Change of Control of the other party.")
    assert hits("Change of Control", "If a party enters into a merger or consolidation, the other party may terminate this Agreement on notice.")
    assert hits("Change of Control", "The other party's consent is required before any acquisition of all of its voting stock.")


def test_change_of_control_ignores_unrelated_acquisition_and_merger_words():
    for text in ("Assist the Client in identification and acquisition of corporate sponsors.",
                 "To identify technology acquisition opportunities from research universities.",
                 "The Client pays for the acquisition or supply of any hardware or software.",
                 "Nothing in this section limits the merger clause of the parent company records."):
        assert not hits("Change of Control", text), text


def test_renewal_matches_automatic_extensions_and_renewal_terms():
    assert hits("Renewal", "This Agreement renews automatically for successive one year terms.")
    assert hits("Renewal", "The term will automatically extend for additional periods of twelve months.")
    assert hits("Renewal", "Each renewal term shall be one (1) year.")


def test_renewal_ignores_a_bare_mention_of_renewal():
    for text in ("The Service Prices may change at the time of any renewal of this Agreement.",
                 "Licensee shall pay the renewal fee to the registrar."):
        assert not hits("Renewal", text), text

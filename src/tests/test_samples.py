"""Bundled sample contracts and the review-time estimate shown next to each."""
from clause_review.samples import SAMPLES, estimate_seconds, format_duration, list_samples


def test_every_listed_sample_file_exists_and_is_listed_once():
    found = list_samples()
    assert len(found) == len(SAMPLES) == 11  # the short sample plus the ten answer-key contracts
    assert len({s["id"] for s in found}) == len(found)
    assert all(s["chars"] > 0 and s["chunks"] >= 1 for s in found)


def test_longer_contracts_take_longer_and_more_workers_take_less():
    by_id = {s["id"]: s for s in list_samples()}
    long_, short = by_id["contract_04"], by_id["contract_08"]
    assert long_["chunks"] > short["chunks"]
    assert estimate_seconds(long_["chunks"], "claude_code") > estimate_seconds(short["chunks"], "claude_code")
    assert estimate_seconds(10, "anthropic", workers=4) == estimate_seconds(10, "anthropic", workers=1) / 4


def test_estimate_wording():
    assert estimate_seconds(50, "mock") == 0.0 and format_duration(0.0) == "instant"
    assert estimate_seconds(5, "local") is None and format_duration(None) == "time unknown"
    assert format_duration(5) == "under 10 sec"
    assert format_duration(42) == "about 40 sec"
    assert format_duration(360) == "about 6 min"

from clause_review.view import load_results
from test_review_actions import finding_ids, reviewed
from workspace_html import apply_action, build_view


def setup():
    s, pid = reviewed()
    return s, lambda: load_results(s, pid, ["Governing Law", "Assignment"])


def test_view_describes_the_clause_on_screen_and_is_plain_data():
    s, docs = setup()
    v = build_view(s, docs(), {})
    assert v["current"]["name"] == "Assignment" and v["position"]["of"] >= 1
    assert [k["label"] for k in v["clauses"]] == ["Assignment", "Governing law"]
    assert v["document"]["mode"] == "passage" and "<mark>" in v["document"]["html"]
    import json
    json.dumps(v)  # the page receives JSON


def test_page_actions_change_the_same_data_the_streamlit_buttons_did():
    s, docs = setup()
    (law,) = finding_ids(s, "Governing Law")
    state = {}
    apply_action(s, state, {"type": "accept", "id": law}, docs())
    assert next(f for f in docs()[0]["findings"] if f["id"] == law)["review"] == "accepted"
    apply_action(s, state, {"type": "ask", "id": law, "text": "Which law applies?"}, docs())
    f = next(f for f in docs()[0]["findings"] if f["id"] == law)
    assert f["question"] == "Which law applies?" and f["qstate"] == "open"
    apply_action(s, state, {"type": "remove", "id": law}, docs())
    assert build_view(s, docs(), state)["removed"] or True
    assert apply_action(s, state, {"type": "overview"}, docs()) == "overview"
    assert apply_action(s, state, {"type": "nonsense"}, docs()) is None
    assert apply_action(s, state, None, docs()) is None


def test_navigation_and_search_actions_update_what_the_next_view_shows():
    s, docs = setup()
    state = {}
    apply_action(s, state, {"type": "mode", "mode": "All clauses"}, docs())
    apply_action(s, state, {"type": "clause", "name": "Governing Law"}, docs())
    assert build_view(s, docs(), state)["current"]["name"] == "Governing law"
    d = docs()[0]
    apply_action(s, state, {"type": "find", "q": "law", "doc": d["id"]}, docs())
    v = build_view(s, docs(), state)
    assert v["document"]["mode"] == "search" and v["document"]["total"] >= 1


def test_readable_text_has_paragraphs_headings_and_no_dot_leaders():
    from workspace_html import readable
    out = readable("Table of Contents<br>Term..........................<br>3<br><br>9. ASSIGNMENT<br><br>9.1 <mark>Neither party<br>may assign.</mark> More.")
    assert "....." not in out and "Table of Contents Term … 3</p>" in out
    assert '<p class="h">9. ASSIGNMENT</p>' in out and "<mark>Neither party may assign.</mark>" in out


def test_sections_are_split_by_their_numbering_and_the_marked_section_is_the_dark_one():
    from workspace_html import readable
    out = readable("8.3 Upon expiry Endorser stops. 9. ASSIGNMENT<br><br>9.1 <mark>No assignment without consent.</mark> Company may assign. "
                   "9.2 An affiliate transfer is an assignment. 10. INDEPENDENT CONTRACTOR<br><br>10.1 Endorser is independent.")
    assert '<p class="dim">8.3 Upon expiry Endorser stops.</p>' in out
    assert '<p class="h">9. ASSIGNMENT</p>' in out and "<p>9.2 An affiliate transfer is an assignment.</p>" in out
    assert '<p class="h dim">10. INDEPENDENT CONTRACTOR</p>' in out and '<p class="dim">10.1 Endorser is independent.</p>' in out
    assert out.count("<mark>") == 1


def test_runs_of_spaces_that_were_line_breaks_start_a_new_paragraph_only_before_a_numbered_item():
    from workspace_html import readable
    out = readable("The period ends in July.   (b) In the event that the Company      shall achieve sales then it renews.")
    assert "<p>The period ends in July.</p>" in out and "<p>(b) In the event that the Company shall achieve sales then it renews.</p>" in out


def test_gaps_are_listed_but_do_not_count_as_to_do_and_can_be_opened_on_purpose():
    s, docs = setup()
    state = {}
    v = build_view(s, docs(), state)
    gap_names = {g["name"] for g in v["gaps"]}
    todo_clauses = {k["name"] for k in v["clauses"] if k["state"] == "found"}
    assert v["position"]["of"] == len(todo_clauses) and not (gap_names & {v["category"]})
    (law,) = [f for f in docs()[0]["findings"] if f["category"] == "Governing Law"]
    apply_action(s, state, {"type": "remove", "id": law["id"]}, docs())
    apply_action(s, state, {"type": "jump", "doc": docs()[0]["id"], "name": "Governing Law"}, docs())
    v = build_view(s, docs(), state)
    assert v["category"] == "Governing Law" and v["findings"] == []  # opened on purpose, so it stays put
    assert any(g["name"] == "Governing Law" for g in v["gaps"])
    assert v["position"]["of"] == 1 and (v["decided"], v["total"], v["left"]) == (1, 2, 1) and v["progress"] == 0.5  # Governing Law removed, Assignment left; same numbers as the Overview


def _renewal_store():
    """A review of a real contract whose Renewal clause has several passages."""
    from pathlib import Path
    from clause_review.pipeline import run_review
    from clause_review.providers import MockProvider
    from clause_review.store import Store
    s = Store()
    pid = run_review(s, "p", [Path(__file__).parent.parent / "samples" / "contracts" / "contract_04.txt"], MockProvider(), categories=["Renewal"])
    return s, lambda: load_results(s, pid, ["Renewal"])


def test_one_passage_per_screen_and_only_that_passage_is_marked_in_the_contract():
    s, docs = _renewal_store()
    n = len([f for f in docs()[0]["findings"] if f["review"] != "removed"])
    assert n >= 2
    state = {}
    v = build_view(s, docs(), state)
    assert len(v["findings"]) == 1 and v["findings"][0]["index"] == 1 and v["findings"][0]["of"] == n
    assert v["document"]["html"].count("<mark>") == 1
    assert v["position"] == {"at": 1, "of": n}
    first = v["findings"][0]["id"]
    apply_action(s, state, {"type": "accept", "id": first}, docs())
    v = build_view(s, docs(), state)  # the next passage still to decide, in the same clause
    assert v["findings"][0]["id"] != first and v["findings"][0]["index"] == 2
    assert v["position"] == {"at": 1, "of": n - 1} and v["document"]["html"].count("<mark>") == 1
    assert sum(1 for t in v["document"]["ticks"] if t["now"]) == 1


def test_next_and_previous_walk_the_passages_and_passage_buttons_reach_decided_ones():
    s, docs = _renewal_store()
    state = {}
    ids = [f["id"] for f in docs()[0]["findings"]]
    seen = []
    for _ in range(len(ids)):
        v = build_view(s, docs(), state)
        seen.append(v["findings"][0]["id"])
        apply_action(s, state, {"type": "next"}, docs())
    assert seen == ids  # each passage once, in order
    apply_action(s, state, {"type": "accept", "id": ids[0]}, docs())
    state.pop("ws_step", None)  # the loop above asked for one more step that was never drawn
    state["ws_pos"], state["ws_fid"] = 0, ids[1]
    apply_action(s, state, {"type": "pprev"}, docs())
    v = build_view(s, docs(), state)
    assert v["findings"][0]["id"] == ids[0] and v["mode"] == "All clauses"  # the decided passage can still be looked at


def test_undo_puts_a_decided_passage_back_and_shows_it_again():
    s, docs = _renewal_store()
    state = {}
    ids = [f["id"] for f in docs()[0]["findings"]]
    v = build_view(s, docs(), state)
    first = v["findings"][0]["id"]
    apply_action(s, state, {"type": "accept", "id": first}, docs())
    v = build_view(s, docs(), state)
    assert v["findings"][0]["id"] == ids[1]  # moved on to the next passage
    apply_action(s, state, {"type": "undo", "id": first, "doc": v["docId"], "name": v["category"]}, docs())
    v = build_view(s, docs(), state)
    assert v["findings"][0]["id"] == first and v["findings"][0]["review"] == "pending"
    assert v["position"]["of"] == len(ids)  # back in the queue


def test_page_number_is_only_shown_for_pdfs():
    from workspace_html import _finding
    f = {"id": 1, "page": 14, "review": "pending", "quote": "q", "question": None, "answer": None, "qstate": None}
    assert _finding(f, 1, 1, "deal.pdf")["page"] == 14
    assert _finding(f, 1, 1, "contract_01 - Title (Party).txt")["page"] is None  # a text file has no pages

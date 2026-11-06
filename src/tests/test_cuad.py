import json

import pytest

from clause_review.cuad import load_cuad, sample, split_contracts
from clause_review.evaluate import NoModel, evaluate, main
from clause_review.providers import MockProvider

GOV = "This Agreement shall be governed by the laws of the State of New York."
ASSIGN = "Neither party may assign this Agreement without the prior written consent of the other party."
TEXT_A = f"1. Term. Five years.\n\n{GOV}\n\n{ASSIGN}\n\n3. Fees. Paid monthly in arrears."
TEXT_B = "Preamble text that has nothing to say about the checklist at all, only about parties and dates."


def _item(title, text, answers):
    qas = []
    for label in ("Governing Law", "Anti-Assignment", "Change Of Control", "Parties", "Renewal Term",
                  "Termination For Convenience"):
        qas.append({"id": f"{title}__{label}", "question": "?", "is_impossible": not answers.get(label),
                    "answers": [{"text": t, "answer_start": text.index(t)} for t in answers.get(label, [])]})
    return {"title": title, "paragraphs": [{"context": text, "qas": qas}]}


@pytest.fixture
def files(tmp_path):
    a = _item("A_contract", TEXT_A, {"Governing Law": [GOV], "Anti-Assignment": [ASSIGN]})
    b = _item("B_contract", TEXT_B, {})
    c = _item("C_contract", TEXT_A + " more", {"Governing Law": [GOV]})
    (tmp_path / "all.json").write_text(json.dumps({"data": [a, b, c]}))
    (tmp_path / "test.json").write_text(json.dumps({"data": [c]}))
    return str(tmp_path / "all.json"), str(tmp_path / "test.json")


def test_load_maps_labels_to_our_categories_and_ignores_others(files):
    a, b, _ = load_cuad(files[0])
    assert a.gold["Governing Law"] == [(TEXT_A.index(GOV), TEXT_A.index(GOV) + len(GOV))]
    assert len(a.gold["Assignment"]) == 1 and a.gold["Renewal"] == []
    assert set(a.gold) == {"Assignment", "Change of Control", "Termination for Convenience", "Renewal", "Governing Law"}
    assert all(not v for v in b.gold.values())


def test_load_rejects_an_answer_that_is_not_at_its_offset(files, tmp_path):
    data = json.load(open(files[0]))
    data["data"][0]["paragraphs"][0]["qas"][0]["answers"][0]["answer_start"] += 3
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="not at offset"):
        load_cuad(str(bad))


def test_split_keeps_the_test_contracts_out_of_development(files):
    dev, test = split_contracts(load_cuad(files[0]), files[1])
    assert [c.title for c in test] == ["C_contract"]
    assert {c.title for c in dev} == {"A_contract", "B_contract"}


def test_split_refuses_a_test_file_from_another_release(files, tmp_path):
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"data": [_item("Z_contract", TEXT_A, {})]}))
    with pytest.raises(ValueError, match="same release"):
        split_contracts(load_cuad(files[0]), str(other))


def test_sample_is_repeatable_for_a_seed():
    from clause_review.cuad import Contract
    pool = [Contract(f"t{i}", "x") for i in range(30)]
    assert [c.title for c in sample(pool, 5, 7)] == [c.title for c in sample(list(reversed(pool)), 5, 7)]
    assert len(sample(pool, None, 1)) == 30


def test_regex_baseline_counts_hits_and_misses(files):
    dev, _ = split_contracts(load_cuad(files[0]), files[1])
    res = evaluate(dev, NoModel())
    law = res["categories"]["Governing Law"]
    assert (law["tp"], law["n_pred"], law["n_gold"]) == (1, 1, 1) and law["recall"] == 1.0
    asg = res["categories"]["Assignment"]
    assert (asg["tp"], asg["n_gold"]) == (1, 1)
    assert res["categories"]["Renewal"]["n_gold"] == 0 and res["scored"] == 2 and not res["failed"]


def test_a_false_match_lowers_precision_not_recall(files):
    from clause_review.cuad import Contract
    text = f"{GOV}\n\nThe vendor may use a subcontractor and the merger of any records is not restricted here."
    c = Contract("X", text, {"Governing Law": [(0, len(GOV))], "Assignment": [], "Change of Control": [],
                              "Termination for Convenience": [], "Renewal": []})
    res = evaluate([c], NoModel())
    coc = res["categories"]["Change of Control"]
    assert coc["n_pred"] == 1 and coc["tp"] == 0 and coc["precision"] == 0.0 and coc["n_gold"] == 0


def test_a_failed_contract_is_counted_not_scored_as_empty(files):
    class Broken(MockProvider):
        def _complete(self, prompt):
            raise RuntimeError("provider down")
    dev, _ = split_contracts(load_cuad(files[0]), files[1])
    res = evaluate(dev, Broken())
    assert res["scored"] == 0 and len(res["failed"]) == 2
    assert res["categories"]["Governing Law"]["n_gold"] == 0  # nothing was scored, so nothing is claimed


def test_test_split_is_refused_without_the_flag(files):
    with pytest.raises(SystemExit) as e:
        main(["--cuad", files[0], "--test", files[1], "--split", "test", "--baseline"])
    assert "held out" in str(e.value)


def test_cli_baseline_runs_on_development_split(files, capsys):
    main(["--cuad", files[0], "--test", files[1], "--baseline"])
    out = capsys.readouterr().out
    assert "dev split, 2 contracts" in out and "regex baseline" in out and "average of the five" in out

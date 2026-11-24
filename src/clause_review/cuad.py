"""Read CUAD (CUADv1.json, SQuAD format) into contracts with gold spans for the five checklist categories.

The data stays on your machine: nothing here downloads it or stores it in the repository. CUAD is CC BY 4.0
(github.com/TheAtticusProject/cuad). The file has one paragraph per contract: the full text and, for each of the
41 labels, a list of answers (answer_start, text). A label with no answers means the contract has no such clause.
"""
import json
import random
from dataclasses import dataclass, field

from .categories import CATEGORIES

CUAD_TO_CATEGORY = {v["cuad"].lower(): k for k, v in CATEGORIES.items()}


@dataclass
class Contract:
    title: str
    text: str
    gold: dict = field(default_factory=dict)  # category -> [(start, end), ...]; every checklist category is present


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["data"]


def load_cuad(path):
    """Every contract in the file, with gold spans mapped to our category names.
    Raises ValueError if an answer's text is not at its stated offset, because scoring would then be wrong."""
    out = []
    for item in _read(path):
        para = item["paragraphs"][0]
        text = para["context"]
        gold = {c: [] for c in CATEGORIES}
        for qa in para["qas"]:
            cat = CUAD_TO_CATEGORY.get(qa["id"].rsplit("__", 1)[-1].lower())
            if cat is None:
                continue
            for a in qa["answers"]:
                s, e = a["answer_start"], a["answer_start"] + len(a["text"])
                if text[s:e] != a["text"]:
                    raise ValueError(f"{item['title']}: answer for {cat} is not at offset {s}")
                gold[cat].append((s, e))
        out.append(Contract(item["title"], text, gold))
    return out


def test_titles(test_path):
    """Titles in CUAD's test split (test.json from the CUAD release): 102 contracts."""
    return {item["title"] for item in _read(test_path)}


def split_contracts(contracts, test_path):
    """(development, test). Development is every contract outside the test split: 408 of the 510."""
    held_out = test_titles(test_path)
    missing = held_out - {c.title for c in contracts}
    if missing:
        raise ValueError(f"{len(missing)} test-split titles are not in the CUAD file; are these the same release?")
    dev = [c for c in contracts if c.title not in held_out]
    test = [c for c in contracts if c.title in held_out]
    return dev, test


def sample(contracts, n, seed):
    """n contracts drawn with a recorded seed from the title-sorted list, so the same draw can be repeated."""
    pool = sorted(contracts, key=lambda c: c.title)
    return pool if n is None or n >= len(pool) else random.Random(seed).sample(pool, n)

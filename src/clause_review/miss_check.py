"""Where do the model's misses sit, and would an "also mentions" list surface them? Development split only, no model calls.

For each labeled passage the tool missed, say what the review screen would have shown for that clause in that contract:
  gap        nothing found: the row says "Nothing found" and the reviewer is told to search
  wrong      something was found but none of it is a labeled passage: the row says "Found"
  partial    something found is a labeled passage, and this one was missed: the row says "Found" and looks complete
`gap` misses are flagged. `wrong` and `partial` misses are silent: the screen gives no sign that a passage is missing.

It also tries a display-only keyword rule (ALSO_MENTIONS) for sentences the tool did not suggest, and reports how many of
the missed passages those sentences would put in front of the reader, and how long the list would be per contract.
Reads the CUAD files and the saved model replies (eval_cache.db) on your machine; a contract whose replies are not all
saved is skipped and counted, so nothing is paid for. It prints counts; it writes no answer key anywhere."""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys

from .categories import CATEGORIES
from .cuad import load_cuad, sample, split_contracts
from .chunk import chunk
from .extract import _BOUNDARY, PROMPT, describe
from .pipeline import find_findings
from .providers import Provider
from .score import coverage, overlap
from .store import Store

# Display-only rules, kept apart from the scored keyword patterns in categories.py so that nothing scored changes.
# Hypothesis to test: the sentences the model misses in Assignment are the ones that say what an assignment without
# consent does (void, null, of no effect, a breach or default).
ALSO_MENTIONS = {
    "Assignment": [
        r"\bassign(?:ed|ment|ments|s)?\b[^.]{0,250}\b(?:void|null and void|of no (?:force or )?effect|invalid|breach|default)\b",
        r"\b(?:void|null and void|of no (?:force or )?effect|invalid)\b[^.]{0,250}\bassign",
    ],
}


class Offline(Provider):
    """Any model call fails: a contract whose replies are not saved is skipped, never paid for. It carries the name and
    model of the real provider because the saved replies are filed under them (see llm_candidates)."""
    name = "anthropic"

    def __init__(self, model=None):
        super().__init__()
        self.model = model or os.environ.get("CLAUSE_MODEL", "claude-sonnet-5-5")

    def _complete(self, prompt):
        raise LookupError("reply not saved")


def classify_misses(gold, shown, threshold=0.5):
    """gold, shown: lists of (start, end) for one clause in one contract. Returns counts of matched labeled passages and of
    missed ones by what the screen showed."""
    taken, matched = set(), set()
    for s in shown:
        hit = next((i for i, g in enumerate(gold) if i not in taken and overlap(s, g) >= threshold), None)
        if hit is not None:
            taken.add(hit)
            matched.add(hit)
    missed = len(gold) - len(matched)
    kind = "gap" if not shown else ("partial" if matched else "wrong")
    return {"matched": len(matched), "missed": missed, "kind": kind if missed else None}


def sentence_spans(text, patterns):
    """The whole sentence around each hit of the patterns, as (start, end), without repeats."""
    cuts = [(m.start(), m.end()) for m in _BOUNDARY.finditer(text)]
    starts, ends = [c[0] for c in cuts], [c[1] for c in cuts]
    from bisect import bisect_left, bisect_right
    out = set()
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            i, j = bisect_right(ends, m.start()), bisect_left(starts, m.end())
            out.add((ends[i - 1] if i else 0, starts[j] if j < len(starts) else len(text)))
    return sorted(out)


def also_mentions(text, patterns, shown, threshold=0.5):
    """Sentences the rule finds that are not already shown (a shown passage covers them)."""
    return [s for s in sentence_spans(text, patterns) if not any(coverage(s, f) >= threshold for f in shown)]


def check(contracts, categories, cache, patterns=ALSO_MENTIONS):
    """Report on `categories`, but read the saved replies with all five: the evaluation asks the model about every
    category in one prompt, and the saved reply is filed under a hash of that whole prompt. Asking about fewer
    categories builds a different prompt and finds nothing."""
    ask = list(CATEGORIES)
    report = {c: {"contracts": 0, "labeled": 0, "matched": 0, "gap": 0, "wrong": 0, "partial": 0,
                  "surfaced": 0, "list_lengths": []} for c in categories}
    skipped = 0
    for con in contracts:
        try:
            found = find_findings(con.text, ask, Offline(), cache=cache)
        except LookupError:
            skipped += 1
            continue
        for cat in categories:
            r = report[cat]
            shown = [(f["start"], f["end"]) for f in found if f["category"] == cat]
            gold = con.gold[cat]
            r["contracts"] += 1
            r["labeled"] += len(gold)
            res = classify_misses(gold, shown)
            r["matched"] += res["matched"]
            if res["kind"]:
                r[res["kind"]] += res["missed"]
            if cat in patterns:
                extra = also_mentions(con.text, patterns[cat], shown)
                r["list_lengths"].append(len(extra))
                unmatched_gold = [g for g in gold if not any(overlap(s, g) >= 0.5 for s in shown)]
                r["surfaced"] += sum(1 for g in unmatched_gold if any(coverage(e, g) >= 0.5 for e in extra))
    return report, skipped


DIAGNOSE_MODELS = ["claude-sonnet-5-5", "claude-sonnet-4-5", "claude-opus-5-5", "claude-haiku-5-5"]
DIAGNOSE_PROVIDERS = ["anthropic", "claude_code", "local", "mock"]


def diagnose(contracts, cache, models=None, providers=None, n=5):
    """Why would a saved reply not be found? Counts the rows in the cache, then for the first n contracts counts how many
    chunk prompts have a saved reply under each provider and model, asking about all five categories. Prints counts only."""
    models = models or DIAGNOSE_MODELS
    providers = providers or DIAGNOSE_PROVIDERS
    rows = cache.db.execute("SELECT COUNT(*) FROM LLMCache").fetchone()[0]
    prompts = []
    for con in contracts[:n]:
        for ch in chunk(con.text):
            prompts.append(PROMPT.format(cats="\n".join(describe(c) for c in CATEGORIES), chunk=ch.text))
    lines = [f"rows in the cache: {rows}", f"prompts built from the first {min(n, len(contracts))} contracts: {len(prompts)}"]
    for prov in providers:
        for model in models + [""]:
            hits = sum(1 for pr in prompts
                       if cache.get(hashlib.sha256(f"{prov}|{model}|{pr}".encode()).hexdigest()) is not None)
            if hits:
                lines.append(f"  {prov} | {model or '(no model name)'}: {hits} of {len(prompts)} have a saved reply")
    if len(lines) == 2:
        lines.append("  no provider and model combination tried has a saved reply for these prompts. Either the model name is "
                     "one not tried (pass --models), or the prompt or definitions differ from the run that saved them.")
    return "\n".join(lines)


def format_report(report, skipped):
    lines = [f"{skipped} contracts skipped (replies not all saved)", ""]
    if skipped and not any(r["contracts"] for r in report.values()):
        lines += ["Every contract was skipped, so no saved reply matched. The usual causes: CLAUSE_MODEL is not the model the",
                  "development run used, the prompt or the Clause Definitions changed after that run, or --cache is not",
                  "the file that run wrote.", ""]
    for cat, r in report.items():
        missed = r["gap"] + r["wrong"] + r["partial"]
        lines.append(f"{cat}: {r['contracts']} contracts, {r['labeled']} labeled passages, {r['matched']} matched, {missed} missed")
        if missed:
            lines.append(f"  missed and flagged (the row said Nothing found): {r['gap']}")
            lines.append(f"  missed and silent, only wrong passages shown:     {r['wrong']}")
            lines.append(f"  missed and silent, row looked partly right:      {r['partial']}")
        if r["list_lengths"]:
            ll = r["list_lengths"]
            lines.append(f"  an also-mentions list would surface {r['surfaced']} of the {missed} missed passages; "
                         f"list length per contract: median {statistics.median(ll)}, max {max(ll)}")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cuad", required=True, help="path to CUADv1.json")
    ap.add_argument("--test", required=True, help="path to CUAD's test.json (it defines which contracts are held out)")
    ap.add_argument("--cache", default="eval_cache.db", help="the SQLite file of saved model replies from the development runs")
    ap.add_argument("--categories", nargs="+", default=["Assignment", "Change of Control"], choices=list(CATEGORIES))
    ap.add_argument("--limit", type=int, help="only this many development contracts, drawn with --seed")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--json", help="write the counts to this file")
    ap.add_argument("--diagnose", action="store_true", help="instead of the check, show why saved replies are not found")
    ap.add_argument("--models", nargs="+", help="model names to try with --diagnose")
    a = ap.parse_args(argv)
    dev, _ = split_contracts(load_cuad(a.cuad), a.test)  # the held-out test contracts are never read
    chosen = sample(dev, a.limit, a.seed)
    if a.diagnose:
        print(diagnose(chosen, Store(a.cache), a.models))
        return
    report, skipped = check(chosen, a.categories, Store(a.cache))
    print(format_report(report, skipped))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"skipped": skipped, "report": report}, fh, indent=1)


if __name__ == "__main__":
    main()

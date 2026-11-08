"""Score the extractor against CUAD labels.

  python -m clause_review.evaluate --cuad CUADv1.json --test test.json --limit 20 --seed 1
  python -m clause_review.evaluate --cuad CUADv1.json --test test.json --baseline      (regex pass only, no model)

Defaults to the development split (the 408 contracts outside CUAD's test split). The test split is refused unless
--allow-test is given: the plan is to leave it untouched until the answer key, definitions and prompts are frozen.

Scoring: a predicted span matches a gold span when their character overlap divided by their union is at least 0.5
(Jaccard, the measure CUAD's own evaluation uses). Each gold span matches at most one prediction. Each category's counts
are pooled over contracts; the headline is the average of the five categories' precision, recall and F1.
A second, more lenient result is printed beside it: a match when the overlap is at least half of the shorter of the two
spans. It exists because CUAD sometimes labels very long spans that a correct one-sentence answer cannot match under
Jaccard. It is secondary and was defined before any model run or test run; the headline stays Jaccard.
Contracts the model call failed on are left out of the scoring and counted, never scored as empty.
"""
import argparse
import json
import sys
import time

from .categories import CATEGORIES
from .cuad import load_cuad, sample, split_contracts
from .pipeline import find_findings
from .providers import BudgetExceeded, Provider, get_provider
from .score import MEASURES, score
from .store import Store


class NoModel(Provider):
    """Returns no passages, so only the regex pass of the extractor runs: the baseline in the evaluation plan."""
    name = "none"

    def _complete(self, prompt):
        return "[]", 0, 0


def _summarize(tot):
    out = {}
    for cat, t in tot.items():
        p = t["tp"] / t["n_pred"] if t["n_pred"] else 0.0
        r = t["tp"] / t["n_gold"] if t["n_gold"] else 0.0
        out[cat] = {**t, "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}
    avg = {k: sum(v[k] for v in out.values()) / len(out) for k in ("precision", "recall", "f1")}
    return out, avg


def evaluate(contracts, provider, categories=None, cache=None, workers=1, threshold=0.5, progress=None):
    """Run the extractor over the contracts. Returns the headline (Jaccard) result under 'categories' and 'average',
    the lenient result under 'lenient', plus 'scored', 'failed' and 'stopped'."""
    cats = list(categories or CATEGORIES)
    tots = {m: {c: {"tp": 0, "n_pred": 0, "n_gold": 0} for c in cats} for m in MEASURES}
    scored, failed, stopped = 0, [], None
    for i, c in enumerate(contracts, 1):
        try:
            found = find_findings(c.text, cats, provider, cache=cache, workers=workers)
        except BudgetExceeded as e:
            stopped = str(e)
            break
        except Exception as e:  # one bad response must not become an empty prediction
            failed.append((c.title, str(e)))
            continue
        pred = {cat: [(f["start"], f["end"]) for f in found if f["category"] == cat] for cat in cats}
        for m in MEASURES:
            for cat, r in score({k: c.gold[k] for k in cats}, pred, threshold, m).items():
                for k in ("tp", "n_pred", "n_gold"):
                    tots[m][cat][k] += r[k]
        scored += 1
        if progress:
            progress(i, len(contracts), c.title)
    out, avg = _summarize(tots["jaccard"])
    lout, lavg = _summarize(tots["coverage"])
    return {"categories": out, "average": avg, "lenient": {"categories": lout, "average": lavg},
            "scored": scored, "failed": failed, "stopped": stopped}


def _table(cats, avg, title):
    lines = [title, f"{'category':30} {'prec':>6} {'recall':>6} {'F1':>6}   tp / predicted / gold"]
    for cat, r in cats.items():
        lines.append(f"{cat:30} {r['precision']:6.2f} {r['recall']:6.2f} {r['f1']:6.2f}   {r['tp']} / {r['n_pred']} / {r['n_gold']}")
    lines.append(f"{'average of the five':30} {avg['precision']:6.2f} {avg['recall']:6.2f} {avg['f1']:6.2f}")
    return lines


def format_report(res, label):
    lines = [f"{label}: {res['scored']} contracts scored, {len(res['failed'])} failed", ""]
    lines += _table(res["categories"], res["average"], "HEADLINE: match = overlap / union >= 0.5 (Jaccard, as in CUAD)")
    lines += ["", *_table(res["lenient"]["categories"], res["lenient"]["average"],
                          "SECONDARY, more lenient: match = overlap >= half of the shorter span")]
    if res["stopped"]:
        lines.append(f"STOPPED EARLY, results are partial: {res['stopped']}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cuad", required=True, help="path to CUADv1.json")
    ap.add_argument("--test", required=True, help="path to CUAD's test.json (defines the held-out split)")
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--allow-test", action="store_true", help="required to touch the test split")
    ap.add_argument("--limit", type=int, help="score only this many contracts, drawn with --seed")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--baseline", action="store_true", help="regex pass only, no model call")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--cache", default="eval_cache.db", help="SQLite file that keeps paid model responses between runs")
    ap.add_argument("--json", help="write the full result to this file")
    a = ap.parse_args(argv)
    if a.split == "test" and not a.allow_test:
        sys.exit("The test split is held out until the freeze. Use --split dev, or add --allow-test when the key is frozen.")
    dev, test = split_contracts(load_cuad(a.cuad), a.test)
    pool = dev if a.split == "dev" else test
    chosen = sample(pool, a.limit, a.seed)
    provider = NoModel() if a.baseline else get_provider()
    cache = None if a.baseline else Store(a.cache)
    label = f"{a.split} split, {len(chosen)} contracts" + (f" (seed {a.seed})" if a.limit else "") + \
            f", {'regex baseline' if a.baseline else provider.name}"
    t0 = time.time()
    res = evaluate(chosen, provider, cache=cache, workers=a.workers,
                   progress=lambda i, n, t: print(f"[{i}/{n}] {t[:60]}", file=sys.stderr))
    print(format_report(res, label))
    usage = "none, regex pass only" if a.baseline else provider.meter.summary()
    print(f"model usage: {usage}; {time.time() - t0:.0f} s")
    if provider.name == "mock":
        print("The mock provider uses keyword rules, not a model: these numbers say nothing about model quality.")
    for title, err in res["failed"]:
        print(f"FAILED {title}: {err}")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"label": label, **res}, fh, indent=1)
    if res["stopped"] or res["failed"]:
        sys.exit(2)


if __name__ == "__main__":
    main()

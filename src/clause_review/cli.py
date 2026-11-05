"""python -m clause_review.cli <project> <db> <out.csv> <contract files...>

Environment: CLAUSE_PROVIDER (mock|anthropic|local), CLAUSE_WORKERS (parallel model calls, default 1),
CLAUSE_BUDGET_USD with CLAUSE_PRICE_IN and CLAUSE_PRICE_OUT (USD per million tokens) to stop at a spend limit.
"""
import os
import sys

from .export import export_csv
from .pipeline import run_review
from .providers import BudgetExceeded, get_provider
from .store import Store


def main(argv=None):
    project, db, out, *files = argv or sys.argv[1:]
    store = Store(db)
    provider = get_provider()
    workers = int(os.environ.get("CLAUSE_WORKERS", "1"))
    try:
        pid = run_review(store, project, files, provider, workers=workers)
    except BudgetExceeded as e:
        print(f"stopped: {e}\nPaid responses are saved in {db}; rerun to continue without paying for them again.")
        sys.exit(2)
    print("findings, gaps:", export_csv(store, pid, out))
    print("model usage:", provider.meter.summary())


if __name__ == "__main__":
    main()

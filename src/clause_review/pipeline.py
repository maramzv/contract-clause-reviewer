"""Run a review: ingest -> chunk -> extract -> verify -> store."""
import logging
from pathlib import Path

from .categories import CATEGORIES
from .chunk import chunk
from .extract import extract
from .ingest import IngestError, ingest
from .providers import BudgetExceeded
from .store import FAILED, FOUND, NOT_FOUND

log = logging.getLogger("clause_review")


def run_review(store, project, paths, provider, categories=None, workers=1):
    cats = list(categories or CATEGORIES)
    pid = store.project(project)
    for path in paths:
        try:
            doc = ingest(path)
        except IngestError as e:
            did = store.add_document(pid, Path(path).name, "", "failed", str(e))
            for c in cats:
                store.set_status(did, c, FAILED)
            continue
        did = store.add_document(pid, doc.name, doc.text)
        try:
            cands = extract(chunk(doc.text), cats, provider, cache=store, workers=workers)
            kept, dropped = verify_and_log(cands, doc.text)
        except BudgetExceeded as e:  # stop the whole run: the remaining documents would fail the same way
            store.db.execute("UPDATE Document SET status='failed', error=? WHERE id=?", (str(e), did))
            for c in cats:
                store.set_status(did, c, FAILED)
            store.commit()
            raise
        except Exception as e:  # provider outage etc.: fail loudly per document, never as "not found"
            store.db.execute("UPDATE Document SET status='failed', error=? WHERE id=?", (str(e), did))
            for c in cats:
                store.set_status(did, c, FAILED)
            continue
        for f in kept:
            store.add_finding(did, f, doc.page_at(f["start"]))
        found = {f["category"] for f in kept}
        for c in cats:
            store.set_status(did, c, FOUND if c in found else NOT_FOUND)
    store.commit()
    return pid


def verify_and_log(cands, text):
    from .verify import verify
    kept, dropped = verify(cands, text)
    for d in dropped:
        log.warning("dropped unverifiable %s quote: %.60s", d["category"], d["quote"])
    return kept, dropped

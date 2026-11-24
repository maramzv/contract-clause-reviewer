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


def find_findings(text, categories, provider, cache=None, workers=1, on_chunk=None):
    """Chunk, extract and verify one contract's text. Returns the verified findings (each with start, end,
    category, quote, source). Used by the review and by the CUAD evaluation, so both run the same code."""
    cands = extract(chunk(text), list(categories), provider, cache=cache, workers=workers, on_chunk=on_chunk)
    kept, _ = verify_and_log(cands, text)
    return regex_only_as_fallback(kept)


def regex_only_as_fallback(findings):
    """Keep a keyword (regex) finding only for a category where the model found nothing in this contract.
    The keyword pass matches words such as "merger" or "renew" in many sentences that are not the clause (on 60
    development contracts, 123 regex-only findings gave 6 correct ones), so it is a backstop for a model miss, not a
    second source of answers. Where the model found a clause, its findings are the ones shown."""
    from_model = {f["category"] for f in findings if f.get("source") == "llm"}
    return [f for f in findings if f.get("source") == "llm" or f["category"] not in from_model]


def run_review(store, project, paths, provider, categories=None, workers=1, on_event=None):
    """Review the files. on_event(kind, data), if given, is told about each step (run_start, doc_start, chunk, doc_done,
    doc_failed, run_aborted, run_done) so a screen can show progress and a recorder can save the run for replay.
    A failure inside on_event never stops the review."""
    cats = list(categories or CATEGORIES)

    def emit(kind, **data):
        if on_event:
            try:
                on_event(kind, data)
            except Exception:
                log.exception("on_event failed for %s", kind)

    pid = store.project(project)
    emit("run_start", documents=[Path(p).name for p in paths], categories=cats)
    for i, path in enumerate(paths):
        try:
            doc = ingest(path)
        except IngestError as e:
            did = store.add_document(pid, Path(path).name, "", "failed", str(e))
            for c in cats:
                store.set_status(did, c, FAILED)
            emit("doc_failed", index=i, doc=Path(path).name, error=str(e))
            continue
        did = store.add_document(pid, doc.name, doc.text, page_starts=doc.page_starts)
        emit("doc_start", index=i, doc=doc.name, chars=len(doc.text), chunks=len(chunk(doc.text)))
        try:
            kept = find_findings(doc.text, cats, provider, cache=store, workers=workers,
                                 on_chunk=lambda done, total, i=i, name=doc.name: emit(
                                     "chunk", index=i, doc=name, done=done, total=total))
        except BudgetExceeded as e:  # stop the whole run: the remaining documents would fail the same way
            store.db.execute("UPDATE Document SET status='failed', error=? WHERE id=?", (str(e), did))
            for c in cats:
                store.set_status(did, c, FAILED)
            store.commit()
            emit("doc_failed", index=i, doc=doc.name, error=str(e))
            emit("run_aborted", error=str(e))
            raise
        except Exception as e:  # provider outage etc.: fail loudly per document, never as "not found"
            store.db.execute("UPDATE Document SET status='failed', error=? WHERE id=?", (str(e), did))
            for c in cats:
                store.set_status(did, c, FAILED)
            emit("doc_failed", index=i, doc=doc.name, error=str(e))
            continue
        for f in kept:
            store.add_finding(did, f, doc.page_at(f["start"]))
        found = {f["category"] for f in kept}
        for c in cats:
            store.set_status(did, c, FOUND if c in found else NOT_FOUND)
        emit("doc_done", index=i, doc=doc.name, findings=len(kept), found=[c for c in cats if c in found],
             not_found=[c for c in cats if c not in found])
    store.commit()
    emit("run_done")
    return pid


def verify_and_log(cands, text):
    from .verify import verify
    kept, dropped = verify(cands, text)
    for d in dropped:
        log.warning("dropped unverifiable %s quote: %.60s", d["category"], d["quote"])
    return kept, dropped

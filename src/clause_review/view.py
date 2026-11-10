"""Read the stored results of one review in the shape the review screen shows them."""
import re

from .categories import CATEGORIES

_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]<>#$|~])")
_LIST_START = re.compile(r"^(\s*\d+)([.)])")


def md_escape(text: str) -> str:
    """Make contract text safe to place in Markdown: no emphasis, links, math or HTML from the quotation."""
    out = _MD_SPECIAL.sub(r"\\\1", " ".join(text.split()))
    out = _LIST_START.sub(r"\1\\\2", out)  # a section number such as "2." must not become a list item
    return "\\" + out if out.startswith(("- ", "+ ")) else out


def load_results(store, pid, categories=None):
    """One dict per uploaded document: name, status ('ok' or 'failed'), error, a status for each category,
    whether a person marked each category as reviewed, and the findings ordered by category and position. Only the
    categories asked for are included."""
    cats = [c for c in CATEGORIES if categories is None or c in categories]
    out = []
    for d in store.db.execute("SELECT id, name, status, error FROM Document WHERE project_id=? ORDER BY id", (pid,)):
        rows = store.db.execute("SELECT category, status, reviewed FROM CategoryStatus WHERE document_id=?",
                                (d["id"],)).fetchall()
        status = {r["category"]: r["status"] for r in rows}
        reviewed = {r["category"]: bool(r["reviewed"]) for r in rows}
        findings = [dict(r) for r in store.db.execute(
            "SELECT id, category, quote, page, start, end, source, review, question, answer, qstate FROM Finding "
            "WHERE document_id=? ORDER BY category, start", (d["id"],))]
        out.append({"id": d["id"], "name": d["name"], "status": d["status"], "error": d["error"],
                    "categories": {c: status.get(c) for c in cats},
                    "reviewed": {c: reviewed.get(c, False) for c in cats},
                    "findings": [f for f in findings if f["category"] in cats]})
    return out

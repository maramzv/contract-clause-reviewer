"""Export the review table to CSV (accepted and pending findings (removed ones are left out), plus unresolved category statuses)."""
import csv
import io


def write_csv(store, pid, fh):
    rows = store.db.execute("""
        SELECT d.name doc, f.category, f.quote, f.page, f.review, f.question
        FROM Finding f JOIN Document d ON d.id=f.document_id
        WHERE d.project_id=? AND f.review!='removed' ORDER BY d.name, f.category, f.start""", (pid,)).fetchall()
    gaps = store.db.execute("""
        SELECT d.name doc, s.category, s.status FROM CategoryStatus s JOIN Document d ON d.id=s.document_id
        WHERE d.project_id=? AND s.status!='Found' ORDER BY d.name, s.category""", (pid,)).fetchall()
    w = csv.writer(fh)
    w.writerow(["document", "category", "quote", "page", "review", "question"])
    for r in rows:
        w.writerow(list(r))
    for g in gaps:
        w.writerow([g["doc"], g["category"], f"[{g['status']}]", "", "", ""])
    return len(rows), len(gaps)


def csv_text(store, pid):
    buf = io.StringIO(newline="")
    write_csv(store, pid, buf)
    return buf.getvalue()


def export_csv(store, pid, path):
    with open(path, "w", newline="") as fh:
        return write_csv(store, pid, fh)

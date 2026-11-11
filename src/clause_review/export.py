"""Export the review table to CSV: every finding with its review state (pending, accepted or removed), plus a bracketed row
for each category with no verified finding. Removed findings stay in the file with review set to "removed", so the record
of what the reviewer rejected is kept."""
import csv
import io
import re


def file_stem(title):
    """A review's title as a file name: 'Company purchase' -> 'Company_purchase'. Anything that is not a letter or digit becomes one
    underscore, so the name is safe on every system; with no usable title it is 'clause_review'."""
    return re.sub(r"[^\w]+", "_", title or "").strip("_") or "clause_review"


def write_csv(store, pid, fh):
    rows = store.db.execute("""
        SELECT d.name doc, f.category, f.quote, f.page, f.review, f.question, f.answer,
               CASE WHEN f.source='manual' THEN 'Reviewer' ELSE 'Clautra' END found_by,
               CASE WHEN f.review='pending' THEN '' WHEN f.decided_by='senior' THEN 'Senior Lawyer' ELSE 'Junior Associate' END decided_by
        FROM Finding f JOIN Document d ON d.id=f.document_id
        WHERE d.project_id=? AND COALESCE(f.source,'')!='gap' ORDER BY d.name, f.category, f.start""", (pid,)).fetchall()
    gaps = store.db.execute("""
        SELECT d.name doc, s.category, s.status FROM CategoryStatus s JOIN Document d ON d.id=s.document_id
        WHERE d.project_id=? AND s.status!='Found' ORDER BY d.name, s.category""", (pid,)).fetchall()
    w = csv.writer(fh)
    w.writerow(["document", "category", "quote", "page", "review", "question", "answer", "found_by", "decided_by"])
    for r in rows:
        w.writerow(list(r))
    for g in gaps:
        w.writerow([g["doc"], g["category"], f"[{g['status']}]", "", "", "", "", "", ""])
    # the first number counts findings still standing (pending or accepted); removed ones are in the file but not counted
    return sum(1 for r in rows if r['review'] != 'removed'), len(gaps)


def questions_csv_text(store, pid):
    """Only the findings Maya asked about (not removed ones), with the answers so far: the Senior Lawyer's own list."""
    rows = store.db.execute("""
        SELECT d.name doc, f.category, CASE WHEN f.source='gap' THEN '[Nothing found]' ELSE f.quote END, f.page, f.question, f.answer, f.qstate
        FROM Finding f JOIN Document d ON d.id=f.document_id
        WHERE d.project_id=? AND f.question IS NOT NULL AND f.review!='removed'
        ORDER BY d.name, f.category, f.start""", (pid,)).fetchall()
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["document", "category", "quote", "page", "question", "answer", "state"])
    for r in rows:
        w.writerow(list(r))
    return buf.getvalue()


def csv_text(store, pid):
    buf = io.StringIO(newline="")
    write_csv(store, pid, buf)
    return buf.getvalue()


def export_csv(store, pid, path):
    with open(path, "w", newline="") as fh:
        return write_csv(store, pid, fh)

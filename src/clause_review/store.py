"""SQLite store: Project, Document, Finding, CategoryStatus, LLMCache, and saved Runs with their step events."""
import json
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS Project(id INTEGER PRIMARY KEY, name TEXT UNIQUE, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS Document(id INTEGER PRIMARY KEY, project_id INT, name TEXT, text TEXT, status TEXT, error TEXT, page_starts TEXT);
CREATE TABLE IF NOT EXISTS Finding(id INTEGER PRIMARY KEY, document_id INT, category TEXT, quote TEXT,
  start INT, end INT, page INT, source TEXT, review TEXT DEFAULT 'pending', question TEXT);
CREATE TABLE IF NOT EXISTS CategoryStatus(document_id INT, category TEXT, status TEXT, reviewed INT DEFAULT 0,
  PRIMARY KEY(document_id, category));
CREATE TABLE IF NOT EXISTS LLMCache(key TEXT PRIMARY KEY, response TEXT);
CREATE TABLE IF NOT EXISTS Run(id INTEGER PRIMARY KEY, name TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP, provider TEXT,
  model TEXT, project_id INT, categories TEXT, docs INT, usage TEXT, duration REAL);
CREATE TABLE IF NOT EXISTS RunEvent(run_id INT, seq INT, t REAL, kind TEXT, data TEXT, PRIMARY KEY(run_id, seq));
"""
FOUND, NOT_FOUND, FAILED = "Found", "Not found, review required", "Failed to process"
REVIEW_STATES = ("pending", "accepted", "removed")
# A question for the Senior Lawyer: None (no question), then open -> answered -> resolved.
OPEN, ANSWERED, RESOLVED = "open", "answered", "resolved"


class Store:
    def __init__(self, path=":memory:"):
        # The LLM cache is read and written from worker threads, so the connection is shared and guarded.
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        have = {r["name"] for r in self.db.execute("PRAGMA table_info(Finding)")}
        for col in ("answer", "qstate", "decided_by"):  # databases made before these existed get the new columns
            if col not in have:
                self.db.execute(f"ALTER TABLE Finding ADD COLUMN {col} TEXT")
        if "page_starts" not in {r["name"] for r in self.db.execute("PRAGMA table_info(Document)")}:
            self.db.execute("ALTER TABLE Document ADD COLUMN page_starts TEXT")
        self.db.commit()

    def project(self, name):
        self.db.execute("INSERT OR IGNORE INTO Project(name) VALUES(?)", (name,))
        return self.db.execute("SELECT id FROM Project WHERE name=?", (name,)).fetchone()[0]

    def add_document(self, pid, name, text, status="ok", error=None, page_starts=None):
        """`page_starts` are the character offsets where each page of a PDF begins (page 1 = index 0); a text file has none."""
        cur = self.db.execute("INSERT INTO Document(project_id,name,text,status,error,page_starts) VALUES(?,?,?,?,?,?)",
                              (pid, name, text, status, error, json.dumps(page_starts) if page_starts and len(page_starts) > 1 else None))
        return cur.lastrowid

    def page_starts(self, document_id):
        """Where each page of this document begins in its text, or [] for a document without pages (a text file)."""
        row = self.db.execute("SELECT page_starts FROM Document WHERE id=?", (document_id,)).fetchone()
        return json.loads(row["page_starts"]) if row and row["page_starts"] else []

    def add_finding(self, did, f, page):
        self.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source) VALUES(?,?,?,?,?,?,?)",
                        (did, f["category"], f["quote"], f["start"], f["end"], page, f["source"]))

    def add_manual_finding(self, did, category, quote, start, end, by="junior"):
        """A passage the reviewer highlighted herself because the tool missed it. It is saved as accepted (she picked it and
        read it), marked source 'manual' so it is never mistaken for something the tool found, and its clause stops being a gap.
        `quote` must be the contract's own words at text[start:end]."""
        with self._lock:
            if self.db.execute("SELECT 1 FROM Document WHERE id=?", (did,)).fetchone() is None:
                raise ValueError(f"no document with id {did}")
            cur = self.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source,review,decided_by) "
                                  "VALUES(?,?,?,?,?,NULL,'manual','accepted',?)", (did, category, quote, start, end, by))
            self.db.execute("UPDATE CategoryStatus SET status=? WHERE document_id=? AND category=? AND status!=?",
                            (FOUND, did, category, FAILED))
            self.db.commit()
            return cur.lastrowid

    def set_gap_question(self, did, category, text):
        """A question for the Senior Lawyer about a clause where nothing was found, for example 'could this sit under
        Miscellaneous?'. There is no passage to attach it to, so it lives on a hidden placeholder row (source 'gap') that
        the screens never count as a passage. Returns the row's id, or None when there is nothing to save."""
        with self._lock:
            row = self.db.execute("SELECT id FROM Finding WHERE document_id=? AND category=? AND source='gap'", (did, category)).fetchone()
            if row is None:
                if not (text or "").strip():
                    return None
                row_id = self.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source,review) "
                                         "VALUES(?,?,'',-1,-1,NULL,'gap','accepted')", (did, category)).lastrowid
                self.db.commit()
            else:
                row_id = row["id"]
        self.set_question(row_id, text)
        return row_id

    def document_text(self, document_id):
        row = self.db.execute("SELECT text FROM Document WHERE id=?", (document_id,)).fetchone()
        if row is None:
            raise ValueError(f"no document with id {document_id}")
        return row["text"] or ""

    def set_status(self, did, category, status):
        self.db.execute("INSERT OR REPLACE INTO CategoryStatus(document_id,category,status) VALUES(?,?,?)",
                        (did, category, status))

    def set_review(self, finding_id, state, by="junior"):
        """Accept, remove or restore (pending) one finding, and record who decided it ('junior' or 'senior'; nobody once it is
        pending again). A category whose findings are all removed goes back to
        'Not found, review required', so removing a false match never reads as a confirmed absence."""
        if state not in REVIEW_STATES:
            raise ValueError(f"review state must be one of {REVIEW_STATES}, not {state!r}")
        with self._lock:
            row = self.db.execute("SELECT document_id, category FROM Finding WHERE id=?", (finding_id,)).fetchone()
            if row is None:
                raise ValueError(f"no finding with id {finding_id}")
            self.db.execute("UPDATE Finding SET review=?, decided_by=? WHERE id=?", (state, None if state == "pending" else by, finding_id))
            live = self.db.execute("SELECT COUNT(*) FROM Finding WHERE document_id=? AND category=? AND review!='removed' "
                                   "AND COALESCE(source,'')!='gap'",
                                   (row["document_id"], row["category"])).fetchone()[0]
            self.db.execute("UPDATE CategoryStatus SET status=? WHERE document_id=? AND category=? AND status!=?",
                            (FOUND if live else NOT_FOUND, row["document_id"], row["category"], FAILED))
            self.db.commit()

    def _finding_row(self, finding_id):
        row = self.db.execute("SELECT question, qstate FROM Finding WHERE id=?", (finding_id,)).fetchone()
        if row is None:
            raise ValueError(f"no finding with id {finding_id}")
        return row

    def set_question(self, finding_id, text):
        """Maya's question for the Senior Lawyer on one finding. New or changed text makes it 'open' again and drops any
        earlier answer (it answered a different question); empty text removes the question."""
        text = (text or "").strip()
        with self._lock:
            row = self._finding_row(finding_id)
            if text == (row["question"] or ""):
                return
            self.db.execute("UPDATE Finding SET question=?, answer=NULL, qstate=? WHERE id=?",
                            (text or None, OPEN if text else None, finding_id))
            self.db.commit()

    def set_answer(self, finding_id, text):
        """The Senior Lawyer's answer. Empty text takes the answer back and the question returns to 'open'."""
        text = (text or "").strip()
        with self._lock:
            if not self._finding_row(finding_id)["question"]:
                raise ValueError(f"finding {finding_id} has no question to answer")
            self.db.execute("UPDATE Finding SET answer=?, qstate=? WHERE id=?",
                            (text or None, ANSWERED if text else OPEN, finding_id))
            self.db.commit()

    def set_resolved(self, finding_id, resolved=True):
        """Maya closes an answered question (or reopens it). Only an answered question can be resolved."""
        with self._lock:
            if self._finding_row(finding_id)["qstate"] not in (ANSWERED, RESOLVED):
                raise ValueError(f"finding {finding_id} has no answer to resolve")
            self.db.execute("UPDATE Finding SET qstate=? WHERE id=?", (RESOLVED if resolved else ANSWERED, finding_id))
            self.db.commit()

    def set_category_reviewed(self, document_id, category, reviewed=True):
        """Mark a category in one document as reviewed by a person, or clear the mark. This is a progress flag only:
        it never changes the category's status, so a 'Not found, review required' category stays flagged."""
        with self._lock:
            cur = self.db.execute("UPDATE CategoryStatus SET reviewed=? WHERE document_id=? AND category=?",
                                  (1 if reviewed else 0, document_id, category))
            if cur.rowcount == 0:
                raise ValueError(f"no category {category!r} for document {document_id}")
            self.db.commit()

    # Saved runs: the step-by-step events of a review, kept so it can be replayed without calling the model.
    def save_run(self, name, provider, model, project_id, categories, usage, events):
        """Save a finished run. `events` are dicts with a time `t` (seconds from the start) and a `kind`; every other
        key is kept as the event's data."""
        docs = next((len(e.get("documents", [])) for e in events if e["kind"] == "run_start"), 0)
        duration = max((e["t"] for e in events), default=0.0)
        with self._lock:
            cur = self.db.execute("INSERT INTO Run(name,provider,model,project_id,categories,docs,usage,duration) "
                                  "VALUES(?,?,?,?,?,?,?,?)",
                                  (name, provider, model, project_id, json.dumps(list(categories)), docs, usage, duration))
            rid = cur.lastrowid
            self.db.executemany("INSERT INTO RunEvent VALUES(?,?,?,?,?)",
                                [(rid, n, e["t"], e["kind"],
                                  json.dumps({k: v for k, v in e.items() if k not in ("t", "kind")}))
                                 for n, e in enumerate(events)])
            self.db.commit()
        return rid

    def list_runs(self):
        """Saved runs, newest first."""
        rows = self.db.execute("SELECT * FROM Run ORDER BY id DESC").fetchall()
        return [{**dict(r), "categories": json.loads(r["categories"])} for r in rows]

    def run_for_project(self, project_id):
        """The saved run a review belongs to (its title and when it was run), or None, for example for a replay copy."""
        r = self.db.execute("SELECT * FROM Run WHERE project_id=? ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
        return None if r is None else {**dict(r), "categories": json.loads(r["categories"])}

    def get_run(self, run_id):
        r = self.db.execute("SELECT * FROM Run WHERE id=?", (run_id,)).fetchone()
        if r is None:
            raise ValueError(f"no saved run with id {run_id}")
        return {**dict(r), "categories": json.loads(r["categories"])}

    def run_events(self, run_id):
        rows = self.db.execute("SELECT t, kind, data FROM RunEvent WHERE run_id=? ORDER BY seq", (run_id,)).fetchall()
        return [{"t": r["t"], "kind": r["kind"], **json.loads(r["data"])} for r in rows]

    def clone_project(self, src_pid, new_name):
        """A fresh copy of a saved review for a replay: same contracts and findings, but every finding not yet reviewed
        and no category marked reviewed. Category statuses follow the findings, so changes made to the copy never touch
        the original."""
        with self._lock:
            new_pid = self.db.execute("INSERT INTO Project(name) VALUES(?)", (new_name,)).lastrowid
            for d in self.db.execute("SELECT * FROM Document WHERE project_id=? ORDER BY id", (src_pid,)).fetchall():
                new_did = self.db.execute("INSERT INTO Document(project_id,name,text,status,error,page_starts) VALUES(?,?,?,?,?,?)",
                                          (new_pid, d["name"], d["text"], d["status"], d["error"], d["page_starts"])).lastrowid
                self.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source) "
                                "SELECT ?,category,quote,start,end,page,source FROM Finding WHERE document_id=? "
                                "AND COALESCE(source,'')!='gap' ORDER BY id", (new_did, d["id"]))
                for c in self.db.execute("SELECT category, status FROM CategoryStatus WHERE document_id=?",
                                         (d["id"],)).fetchall():
                    has = self.db.execute("SELECT COUNT(*) FROM Finding WHERE document_id=? AND category=? AND COALESCE(source,'')!='gap'",
                                          (new_did, c["category"])).fetchone()[0]
                    status = c["status"] if c["status"] == FAILED else (FOUND if has else NOT_FOUND)
                    self.db.execute("INSERT INTO CategoryStatus(document_id,category,status) VALUES(?,?,?)",
                                    (new_did, c["category"], status))
            self.db.commit()
        return new_pid

    # LLM cache interface used by extract()
    def get(self, key):
        with self._lock:
            r = self.db.execute("SELECT response FROM LLMCache WHERE key=?", (key,)).fetchone()
        return r[0] if r else None

    def put(self, key, response):
        # Committed at once: a paid response must survive a crash or a budget stop, so a rerun does not pay again.
        with self._lock:
            self.db.execute("INSERT OR REPLACE INTO LLMCache VALUES(?,?)", (key, response))
            self.db.commit()

    def commit(self):
        self.db.commit()

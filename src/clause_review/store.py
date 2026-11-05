"""SQLite store: Project, Document, Finding, CategoryStatus, LLMCache."""
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS Project(id INTEGER PRIMARY KEY, name TEXT UNIQUE, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS Document(id INTEGER PRIMARY KEY, project_id INT, name TEXT, text TEXT, status TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS Finding(id INTEGER PRIMARY KEY, document_id INT, category TEXT, quote TEXT,
  start INT, end INT, page INT, source TEXT, review TEXT DEFAULT 'pending', question TEXT);
CREATE TABLE IF NOT EXISTS CategoryStatus(document_id INT, category TEXT, status TEXT, reviewed INT DEFAULT 0,
  PRIMARY KEY(document_id, category));
CREATE TABLE IF NOT EXISTS LLMCache(key TEXT PRIMARY KEY, response TEXT);
"""
FOUND, NOT_FOUND, FAILED = "Found", "Not found, review required", "Failed to process"
REVIEW_STATES = ("pending", "accepted", "removed")


class Store:
    def __init__(self, path=":memory:"):
        # The LLM cache is read and written from worker threads, so the connection is shared and guarded.
        self.db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def project(self, name):
        self.db.execute("INSERT OR IGNORE INTO Project(name) VALUES(?)", (name,))
        return self.db.execute("SELECT id FROM Project WHERE name=?", (name,)).fetchone()[0]

    def add_document(self, pid, name, text, status="ok", error=None):
        cur = self.db.execute("INSERT INTO Document(project_id,name,text,status,error) VALUES(?,?,?,?,?)",
                              (pid, name, text, status, error))
        return cur.lastrowid

    def add_finding(self, did, f, page):
        self.db.execute("INSERT INTO Finding(document_id,category,quote,start,end,page,source) VALUES(?,?,?,?,?,?,?)",
                        (did, f["category"], f["quote"], f["start"], f["end"], page, f["source"]))

    def set_status(self, did, category, status):
        self.db.execute("INSERT OR REPLACE INTO CategoryStatus(document_id,category,status) VALUES(?,?,?)",
                        (did, category, status))

    def set_review(self, finding_id, state):
        """Accept, remove or restore (pending) one finding. A category whose findings are all removed goes back to
        'Not found, review required', so removing a false match never reads as a confirmed absence."""
        if state not in REVIEW_STATES:
            raise ValueError(f"review state must be one of {REVIEW_STATES}, not {state!r}")
        with self._lock:
            row = self.db.execute("SELECT document_id, category FROM Finding WHERE id=?", (finding_id,)).fetchone()
            if row is None:
                raise ValueError(f"no finding with id {finding_id}")
            self.db.execute("UPDATE Finding SET review=? WHERE id=?", (state, finding_id))
            live = self.db.execute("SELECT COUNT(*) FROM Finding WHERE document_id=? AND category=? AND review!='removed'",
                                   (row["document_id"], row["category"])).fetchone()[0]
            self.db.execute("UPDATE CategoryStatus SET status=? WHERE document_id=? AND category=? AND status!=?",
                            (FOUND if live else NOT_FOUND, row["document_id"], row["category"], FAILED))
            self.db.commit()

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

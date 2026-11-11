"""The "Reading your contracts" progress screen, used by a live run and by a replay of a saved run.

It takes the streamlit module as an argument (and never imports it), so the same code drives the real screen and a test
double. It only draws; restyle it here without touching the pipeline or the recorder. The events it understands are the
ones run_review sends: run_start, doc_start, chunk, doc_done, doc_failed, run_aborted, run_done."""
import threading


class ProgressView:
    def __init__(self, st, container=None):
        self.box = container if container is not None else st.container()
        self.rows = {}
        # Streamlit may only be drawn to from the thread that runs the page. A live run with several workers reports
        # chunks from other threads: those are recorded but not drawn, and the next contract-level event catches up.
        self._owner = threading.current_thread()

    def handle(self, kind, d):
        if threading.current_thread() is not self._owner:
            return
        if kind == "run_start":
            self.box.markdown("#### Reading your contracts")
            for i, name in enumerate(d["documents"]):
                self.rows[i] = {"name": name, "bar": self.box.progress(0.0, text=f"{name} · waiting")}
        elif kind == "doc_start":
            self._bar(d, 0.0, f"{d['doc']} · reading, {d['chunks']} part(s)")
        elif kind == "chunk":
            self._bar(d, d["done"] / max(1, d["total"]), f"{d['doc']} · part {d['done']} of {d['total']}")
        elif kind == "doc_done":
            n = d["findings"]
            self._bar(d, 1.0, f":material/check_circle: {d['doc']} · {n} finding{'s' if n != 1 else ''}")
        elif kind == "doc_failed":
            self._bar(d, 1.0, f":material/error: {d['doc']} · failed: {str(d['error'])[:120]}")
        elif kind == "run_aborted":
            self.box.error(f"The review stopped: {d['error']}")
        elif kind == "run_done":
            self.box.success("Done. Your contracts have been read.")

    def _bar(self, d, fraction, text):
        row = self.rows.get(d.get("index"))
        if row is not None:
            row["bar"].progress(min(1.0, max(0.0, fraction)), text=text)

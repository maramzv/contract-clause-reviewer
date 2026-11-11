"""The "Reading your contracts" progress screen, used by a live run and by a replay of a saved run.

It takes the streamlit module as an argument (and never imports it), so the same code drives the real screen and a test
double. It only draws; restyle it here without touching the pipeline or the recorder. The events it understands are the
ones run_review sends: run_start, doc_start, chunk, doc_done, doc_failed, run_aborted, run_done."""
import html
import threading

from clause_review.review_view import split_title

_CHECK = ('<svg class="pr-ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 9.5"/></svg>')
_WARN = ('<svg class="pr-ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/></svg>')


def row_html(name, fraction, state, note=""):
    """One contract on the progress screen: its title and party on the left, what it is doing on the right, a thin bar under.
    `state` is waiting, reading, done or failed; `note` is the text on the right ("part 2 of 4", "8 findings")."""
    title, party, _ = split_title(name)
    who = f'<span class="pr-party">{html.escape(party)}</span>' if party else ""
    icon = _CHECK if state == "done" else _WARN if state == "failed" else ""
    return (f'<div class="pr pr-{state}"><div class="pr-top"><div class="pr-name"><span class="pr-title" title="{html.escape(name)}">'
            f'{html.escape(title)}</span>{who}</div><div class="pr-note">{icon}{html.escape(note)}</div></div>'
            f'<div class="pr-bar"><span style="width:{round(min(1.0, max(0.0, fraction)) * 100)}%"></span></div></div>')


class ProgressView:
    def __init__(self, st, container=None, show_done=True, heading=None):
        self.show_done = show_done  # False when the caller shows the finish itself
        self.heading = heading  # an optional slot for the title line, so the caller can put a button beside it
        self.box = container if container is not None else st.container()
        self.rows = {}
        # Streamlit may only be drawn to from the thread that runs the page. A live run with several workers reports
        # chunks from other threads: those are recorded but not drawn, and the next contract-level event catches up.
        self._owner = threading.current_thread()

    def handle(self, kind, d):
        if threading.current_thread() is not self._owner:
            return
        if kind == "run_start":
            self._title("Reading your contracts")
            for i, name in enumerate(d["documents"]):
                self.rows[i] = {"name": name, "slot": self.box.empty()}
                self._draw(i, 0.0, "waiting", "Waiting")
        elif kind == "doc_start":
            self._draw(d.get("index"), 0.0, "reading", "Starting")
        elif kind == "chunk":
            self._draw(d.get("index"), d["done"] / max(1, d["total"]), "reading", f"Reading · part {d['done']} of {d['total']}")
        elif kind == "doc_done":
            n = d["findings"]
            self._draw(d.get("index"), 1.0, "done", f"{n} finding{'s' if n != 1 else ''}")
        elif kind == "doc_failed":
            self._draw(d.get("index"), 1.0, "failed", f"Failed: {str(d['error'])[:90]}")
        elif kind == "run_aborted":
            self.box.error(f"The review stopped: {d['error']}")
        elif kind == "run_done":
            if self.show_done:
                self.box.success("Done. Your contracts have been read.")
            else:
                self._title("Your contracts have been reviewed")

    def _title(self, text):
        """The line above the rows. Plain HTML, not a heading, which would get a link icon."""
        (self.heading if self.heading is not None else self.box).markdown(f'<div class="pr-head">{text}</div>', unsafe_allow_html=True)

    def _draw(self, index, fraction, state, note):
        row = self.rows.get(index)
        if row is not None:
            row["slot"].markdown(row_html(row["name"], fraction, state, note), unsafe_allow_html=True)

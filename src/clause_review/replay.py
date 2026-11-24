"""Record a review step by step, and play a saved recording back.

A Recorder is passed to run_review as on_event. It stamps each event with the seconds since the run began. play() then
feeds the saved events to a screen at the original pace, a faster pace, or all at once. Nothing here calls a model."""
import threading
import time


class Recorder:
    """Collects the events of one run. Safe to call from worker threads. `forward`, if given, is called with every
    event too (the live progress screen uses it)."""

    def __init__(self, forward=None, clock=time.monotonic):
        self.events = []
        self._forward, self._clock, self._lock = forward, clock, threading.Lock()
        self._start = clock()

    def __call__(self, kind, data):
        with self._lock:
            self.events.append({"t": round(self._clock() - self._start, 3), "kind": kind, **data})
        if self._forward:
            self._forward(kind, data)


def duration(events):
    return max((e["t"] for e in events), default=0.0)


def play(events, handle, speed=1.0, sleep=time.sleep):
    """Send each saved event to `handle(kind, data)`, waiting between events as long as the original run did, divided
    by `speed`. speed=None plays everything at once. Returns the seconds it waited."""
    waited, last = 0.0, 0.0
    for e in events:
        if speed:
            gap = max(0.0, e["t"] - last) / speed
            if gap:
                sleep(gap)
                waited += gap
        last = e["t"]
        handle(e["kind"], {k: v for k, v in e.items() if k not in ("t", "kind")})
    return waited

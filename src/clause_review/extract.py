"""Extract: regex pass (recall) + LLM pass (meaning). Returns unverified candidates."""
import bisect
import hashlib
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from .categories import CATEGORIES, COMPILED
from .providers import parse_json_list

PROMPT = """You are helping a lawyer review a contract. For each category below, copy the passages from the
contract that state the rule the category describes.
Rules:
- Quote EXACTLY, word for word; never paraphrase. Copy the whole sentence that states the rule, no more.
- Quote a passage only if it states the rule itself. Do not quote a heading or title, a definition on its own, or a
  sentence that only mentions the topic.
- Follow each category's "Counts" and "Does not count" lines.
- A passage may be quoted under more than one category if it fits each.
- Judge by meaning, not by keywords. Also quote a passage that has the same effect as the category but is worded differently
  (for example "no party may transfer its rights without the other's written approval" is an assignment restriction even
  though it never says "assign"), or that clearly bears on the category's rule even if it only partly fits (for example a
  right of first refusal on a sale of the company bears on Change of Control). The reviewer will confirm or remove it. The
  quotation itself must still be exact.
Return only a JSON list: [{{"category": "<name>", "quote": "<exact text>"}}]. Return [] if none.
Categories:
{cats}
<<<CONTRACT>>>
{chunk}"""


def describe(cat):
    c = CATEGORIES[cat]
    return f"- {cat}: {c['description']}\n  Counts: {c['counts']}\n  Does not count: {c['not_counts']}"


# A sentence ends at a blank line, or at . ! ? followed by whitespace and a capital letter, digit, bracket or quote.
_BOUNDARY = re.compile(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z0-9(\"\u201c])")
MAX_SENTENCE = 1000  # a longer "sentence" is probably a run-on or a table; fall back to the line


def _line_span(text, a, b):
    start = max(text.rfind("\n", 0, a) + 1, 0)
    end = text.find("\n", b)
    return start, (len(text) if end == -1 else end)


def regex_candidates(chunk, categories):
    """A regex hit becomes the whole sentence around it, so a clause that a PDF wraps over several lines is one quote."""
    text = chunk.text
    cuts = [(m.start(), m.end()) for m in _BOUNDARY.finditer(text)]
    starts, ends = [c[0] for c in cuts], [c[1] for c in cuts]
    for cat in categories:
        for pat in COMPILED[cat]:
            for m in pat.finditer(text):
                i = bisect.bisect_right(ends, m.start())
                j = bisect.bisect_left(starts, m.end())
                a = ends[i - 1] if i else 0
                b = starts[j] if j < len(starts) else len(text)
                if b - a > MAX_SENTENCE:
                    a, b = _line_span(text, m.start(), m.end())
                yield {"category": cat, "quote": text[a:b].strip(), "source": "regex"}


def llm_candidates(chunk, categories, provider, cache=None):
    prompt = PROMPT.format(cats="\n".join(describe(c) for c in categories), chunk=chunk.text)
    key = hashlib.sha256(f"{provider.name}|{getattr(provider, 'model', '')}|{prompt}".encode()).hexdigest()
    raw = cache.get(key) if cache else None
    if raw is None:
        raw = provider.complete(prompt)
        if cache:
            cache.put(key, raw)
    for d in parse_json_list(raw):
        if d["category"] in categories:
            yield {"category": d["category"], "quote": d["quote"], "source": "llm"}


def extract(chunks, categories, provider, cache=None, workers=1, on_chunk=None):
    """Candidates in chunk order, whatever the worker count. With workers > 1 the LLM calls run in parallel;
    if one fails (including BudgetExceeded), calls not yet started are cancelled and the error is raised.
    on_chunk(done, total), if given, is called after each chunk's model step finishes (from a worker thread when
    workers > 1; `done` only goes up)."""
    chunks = list(chunks)
    regex = [list(regex_candidates(ch, categories)) for ch in chunks]

    finished, progress_lock = [0], threading.Lock()

    def llm_for(ch):
        out = list(llm_candidates(ch, categories, provider, cache))
        if on_chunk:
            with progress_lock:
                finished[0] += 1
                on_chunk(finished[0], len(chunks))
        return out

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(llm_for, ch) for ch in chunks]
            try:
                llm = [f.result() for f in futures]
            except BaseException:
                for f in futures:
                    f.cancel()
                raise
    else:
        llm = [llm_for(ch) for ch in chunks]
    cands = []
    for r, l in zip(regex, llm):
        cands += r + l
    return cands

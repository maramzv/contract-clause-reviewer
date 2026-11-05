"""Model providers behind one interface. Select with CLAUSE_PROVIDER=mock|anthropic|local.

Every provider counts tokens through a Meter. Set CLAUSE_BUDGET_USD together with CLAUSE_PRICE_IN and
CLAUSE_PRICE_OUT (USD per million tokens, taken from the provider's price list; none are hard-coded)
and the run stops with BudgetExceeded once the budget is spent.
"""
import json
import os
import re
import threading
import urllib.request

from .categories import COMPILED


class BudgetExceeded(RuntimeError):
    pass


class Meter:
    """Thread-safe token and cost counter with a hard stop.

    The budget is checked before each call, so with N parallel workers the final spend can exceed the
    budget by at most N in-flight calls."""

    def __init__(self, price_in=None, price_out=None, budget=None):
        if budget is not None and (price_in is None or price_out is None):
            raise ValueError("a budget needs CLAUSE_PRICE_IN and CLAUSE_PRICE_OUT (USD per million tokens)")
        self.price_in, self.price_out, self.budget = price_in, price_out, budget
        self.calls = self.tokens_in = self.tokens_out = 0
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls):
        def num(name):
            v = os.environ.get(name)
            return float(v) if v else None
        return cls(num("CLAUSE_PRICE_IN"), num("CLAUSE_PRICE_OUT"), num("CLAUSE_BUDGET_USD"))

    @property
    def cost(self):
        if self.price_in is None or self.price_out is None:
            return 0.0
        return (self.tokens_in * self.price_in + self.tokens_out * self.price_out) / 1_000_000

    def check(self):
        if self.budget is not None and self.cost >= self.budget:
            raise BudgetExceeded(f"budget of ${self.budget:.2f} reached: {self.summary()}")

    def add(self, tokens_in, tokens_out):
        with self._lock:
            self.calls += 1
            self.tokens_in += tokens_in or 0
            self.tokens_out += tokens_out or 0

    def summary(self):
        cost = f", ${self.cost:.2f}" if self.price_in is not None and self.price_out is not None else ""
        return f"{self.calls} calls, {self.tokens_in} in / {self.tokens_out} out tokens{cost}"


class Provider:
    name = "base"

    def __init__(self, meter=None):
        self.meter = meter or Meter.from_env()

    def complete(self, prompt: str) -> str:  # returns JSON text; stops if the budget is spent
        self.meter.check()
        text, tokens_in, tokens_out = self._complete(prompt)
        self.meter.add(tokens_in, tokens_out)
        return text

    def _complete(self, prompt):  # -> (text, input tokens, output tokens)
        raise NotImplementedError


class MockProvider(Provider):
    """Offline, deterministic. Quotes the sentence containing a regex hit; paraphrase=True simulates a hallucination.
    Token counts are a rough estimate (4 characters per token) so the budget guard can be tested offline."""
    name = "mock"

    def __init__(self, paraphrase=False, meter=None):
        super().__init__(meter)
        self.paraphrase = paraphrase

    def _complete(self, prompt):
        text = prompt.split("<<<CONTRACT>>>", 1)[-1]
        out = []
        for cat, pats in COMPILED.items():
            for pat in pats:
                m = pat.search(text)
                if m:
                    a = max(text.rfind(". ", 0, m.start()) + 2, text.rfind("\n", 0, m.start()) + 1, 0)
                    b = text.find(". ", m.end())
                    b = len(text) if b == -1 else b + 1
                    q = " ".join(text[a:b].split())
                    out.append({"category": cat, "quote": ("The parties agree that " + q.lower()) if self.paraphrase else q})
                    break
        result = json.dumps(out)
        return result, len(prompt) // 4, len(result) // 4


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model=None, meter=None):
        super().__init__(meter)
        import anthropic  # lazy: optional dependency
        self.client = anthropic.Anthropic(max_retries=5)  # reads ANTHROPIC_API_KEY; retries rate limits with backoff
        self.model = model or os.environ.get("CLAUSE_MODEL", "claude-sonnet-5-5")

    def _complete(self, prompt):
        r = self.client.messages.create(model=self.model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return text, r.usage.input_tokens, r.usage.output_tokens


class LocalProvider(Provider):
    """Any OpenAI-compatible local server (Ollama, llama.cpp, vLLM)."""
    name = "local"

    def __init__(self, url=None, model=None, meter=None):
        super().__init__(meter)
        self.url = url or os.environ.get("CLAUSE_LOCAL_URL", "http://localhost:11434/v1/chat/completions")
        self.model = model or os.environ.get("CLAUSE_MODEL", "llama3.1")

    def _complete(self, prompt):
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(self.url, body, {"Content-Type": "application/json"})
        data = json.load(urllib.request.urlopen(req, timeout=120))
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return text, usage.get("prompt_tokens", len(prompt) // 4), usage.get("completion_tokens", len(text) // 4)


def get_provider(name=None) -> Provider:
    name = name or os.environ.get("CLAUSE_PROVIDER", "mock")
    return {"mock": MockProvider, "anthropic": AnthropicProvider, "local": LocalProvider}[name]()


def parse_json_list(raw: str):
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        data = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        return []
    return [d for d in data if isinstance(d, dict) and d.get("category") and d.get("quote")]

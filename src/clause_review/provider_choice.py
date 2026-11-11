"""The "Run with" dropdown on the review screen: which providers can be picked, and what is wrong with one that cannot be used.

It is always shown. CLAUSE_PROVIDER only chooses which option it starts on (mock if unset), and CLAUSE_DEV_TOGGLE=0
hides it so a run uses exactly the provider CLAUSE_PROVIDER names."""
import os

CHOICES = {
    "mock": "Mock (offline)",
    "claude_code": "Local Claude agent (no key)",
    "anthropic": "API key (Anthropic)",
}

NOTES = {
    "mock": "Mock provider: an offline provider that finds clauses with keyword rules, not a real model.",
    "claude_code": "Claude Code provider: the model runs through the Claude Code login on this computer. It is slower than "
                   "the API, counts against that login's usage limits, and is not the setup behind the measured results.",
    "anthropic": "",
}


def toggle_enabled(environ=None):
    """The dropdown is on unless CLAUSE_DEV_TOGGLE=0."""
    return (environ if environ is not None else os.environ).get("CLAUSE_DEV_TOGGLE", "1") != "0"


def show_dev_tools(environ=None):
    """The developer parts of the screens (the Dev mode switch, the Offline mode tag, the saved runs and their replay) are hidden unless CLAUSE_SHOW_DEV=1, so by default the app shows only what a user would see."""
    return (environ if environ is not None else os.environ).get("CLAUSE_SHOW_DEV", "0") == "1"


def default_choice(environ=None):
    """What CLAUSE_PROVIDER names, as written (so `local` still works with the toggle off); mock if unset."""
    return (environ if environ is not None else os.environ).get("CLAUSE_PROVIDER", "mock")


def problem(name, environ=None):
    """Why this provider cannot run right now, or None if it can."""
    env = environ if environ is not None else os.environ
    if name == "anthropic":
        if not env.get("ANTHROPIC_API_KEY"):
            return "ANTHROPIC_API_KEY is not set, so the API cannot be used. Pick Claude Code or Mock, or add the key to .env."
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return "The anthropic package is not installed (pip install anthropic)."
    if name == "claude_code":
        from .providers import ClaudeCodeProvider
        try:
            ClaudeCodeProvider._find_command()
        except RuntimeError as e:
            return str(e)
    return None

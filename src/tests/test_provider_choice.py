"""The dev model toggle: off unless asked for, and a provider that cannot run says why."""
from clause_review import provider_choice as pc


def test_dropdown_is_always_on_unless_hidden():
    assert pc.toggle_enabled({})
    assert pc.toggle_enabled({"CLAUSE_DEV_TOGGLE": "1"})
    assert not pc.toggle_enabled({"CLAUSE_DEV_TOGGLE": "0"})


def test_default_follows_clause_provider_as_written():
    assert pc.default_choice({}) == "mock"
    assert pc.default_choice({"CLAUSE_PROVIDER": "claude_code"}) == "claude_code"
    assert pc.default_choice({"CLAUSE_PROVIDER": "local"}) == "local"  # not in the dropdown, still not rewritten


def test_api_without_a_key_is_blocked_with_a_reason():
    assert "ANTHROPIC_API_KEY" in pc.problem("anthropic", {})
    assert pc.problem("mock", {}) is None


def test_claude_code_missing_is_blocked_with_a_reason(monkeypatch):
    from clause_review.providers import ClaudeCodeProvider

    def missing():
        raise RuntimeError("Claude Code CLI not found")
    monkeypatch.setattr(ClaudeCodeProvider, "_find_command", staticmethod(missing))
    assert "not found" in pc.problem("claude_code", {})


def test_every_choice_is_a_real_provider():
    from clause_review.providers import get_provider
    import inspect
    src = inspect.getsource(get_provider)
    assert all(f'"{name}"' in src for name in pc.CHOICES)


def test_dev_and_demo_parts_are_hidden_unless_asked_for():
    assert not pc.show_dev_tools({})
    assert not pc.show_dev_tools({"CLAUSE_SHOW_DEV": "0"})
    assert pc.show_dev_tools({"CLAUSE_SHOW_DEV": "1"})

"""The Claude Code provider: parses the CLI's JSON, counts tokens, and fails loudly. The CLI is faked, so no login is used."""
import json
import subprocess

import pytest

from clause_review.providers import ClaudeCodeProvider, get_provider


def fake_run(stdout, returncode=0, stderr=""):
    calls = []

    def run(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    run.calls = calls
    return run


def reply(result, **extra):
    return json.dumps({"result": result, "is_error": False,
                       "usage": {"input_tokens": 2, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 8,
                                 "output_tokens": 7}, **extra})


def test_returns_text_counts_tokens_and_disables_tools(monkeypatch):
    run = fake_run(reply('[{"category": "Renewal", "quote": "renews each year"}]'))
    monkeypatch.setattr(subprocess, "run", run)
    p = ClaudeCodeProvider(command="claude")
    assert json.loads(p.complete("PROMPT")) == [{"category": "Renewal", "quote": "renews each year"}]
    cmd, kw = run.calls[0]
    assert cmd[cmd.index("--tools") + 1] == ""  # the contract text can never trigger a tool
    assert kw["input"] == "PROMPT"  # the prompt goes in on stdin, not on the command line
    assert (p.meter.tokens_in, p.meter.tokens_out) == (110, 7)


def test_cli_failure_is_an_error_not_an_empty_result(monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run("", returncode=1, stderr="not logged in"))
    with pytest.raises(RuntimeError, match="not logged in"):
        ClaudeCodeProvider(command="claude").complete("x")


def test_error_flag_in_json_is_an_error(monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run(json.dumps({"is_error": True, "result": "rate limited"})))
    with pytest.raises(RuntimeError, match="rate limited"):
        ClaudeCodeProvider(command="claude").complete("x")


def test_model_is_passed_only_when_set(monkeypatch):
    run = fake_run(reply("[]"))
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.delenv("CLAUSE_MODEL", raising=False)
    ClaudeCodeProvider(command="claude").complete("x")
    assert "--model" not in run.calls[0][0]
    ClaudeCodeProvider(command="claude", model="sonnet").complete("x")
    assert run.calls[1][0][run.calls[1][0].index("--model") + 1] == "sonnet"


def test_command_comes_from_env_and_is_selectable(monkeypatch):
    monkeypatch.setenv("CLAUSE_CLAUDE_CMD", "my-claude")
    assert get_provider("claude_code").command == "my-claude"

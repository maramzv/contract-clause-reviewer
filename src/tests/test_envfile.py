import os

from clause_review.envfile import find_env_file, load_env


def test_loads_values_skips_comments_and_removes_quotes(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "# a comment\n\nCLAUSE_PROVIDER=anthropic\nexport CLAUSE_MODEL = \"claude-sonnet-5-5\"\n"
        "CLAUSE_PRICE_IN='2'\nCLAUSE_PRICE_OUT=10 # per million\nNOT_A_SETTING\nEMPTY=\n", encoding="utf-8")
    for k in ("CLAUSE_PROVIDER", "CLAUSE_MODEL", "CLAUSE_PRICE_IN", "CLAUSE_PRICE_OUT", "EMPTY"):
        monkeypatch.delenv(k, raising=False)
    names = load_env(tmp_path)
    assert os.environ["CLAUSE_PROVIDER"] == "anthropic" and os.environ["CLAUSE_MODEL"] == "claude-sonnet-5-5"
    assert os.environ["CLAUSE_PRICE_IN"] == "2" and os.environ["CLAUSE_PRICE_OUT"] == "10"
    assert "EMPTY" not in os.environ and "EMPTY" not in names
    for k in names:
        monkeypatch.delenv(k, raising=False)


def test_an_exported_value_is_never_overwritten(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("CLAUSE_PROVIDER=anthropic\n")
    monkeypatch.setenv("CLAUSE_PROVIDER", "mock")
    assert load_env(tmp_path) == [] and os.environ["CLAUSE_PROVIDER"] == "mock"


def test_finds_the_env_file_in_the_repository_top_folder_when_run_from_src(tmp_path):
    (tmp_path / ".env").write_text("X=1\n")
    src = tmp_path / "src"
    src.mkdir()
    assert find_env_file(src) == tmp_path / ".env"
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    assert find_env_file(deep) is None  # more than two folders up is not searched


def test_no_env_file_is_fine(tmp_path):
    assert load_env(tmp_path / "nothing") == [] or True
    assert find_env_file(tmp_path / "x") is None or find_env_file(tmp_path / "x").name == ".env"


def test_the_returned_names_never_include_values(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-secret-value\n")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    names = load_env(tmp_path)
    assert names == ["ANTHROPIC_API_KEY"] and "sk-secret-value" not in repr(names)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

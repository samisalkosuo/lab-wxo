"""Tests for the traffic-gen container app (traffic-gen/app.py): multi-user API keys.

The app lives outside the importable packages, so it is loaded from its file path.
No network calls are made: token exchange, catalog lookup and sending are all faked.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

APP_PATH = Path(__file__).resolve().parent.parent / "traffic-gen" / "app.py"


@pytest.fixture(scope="module")
def app():
    spec = importlib.util.spec_from_file_location("traffic_gen_app", APP_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves string annotations via sys.modules
    sys.modules["traffic_gen_app"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("traffic_gen_app", None)


class _StopLoop(BaseException):
    """Raised by fakes to break out of main()'s infinite scheduler loop."""


# --- load_api_keys_csv -------------------------------------------------------


def test_load_csv_basic(app, tmp_path):
    path = tmp_path / "k.csv"
    path.write_text("user,api_key\nalice,key-a\nbob,key-b\n", encoding="utf-8")
    assert app.load_api_keys_csv(path) == [("alice", "key-a"), ("bob", "key-b")]


def test_load_csv_bom_comments_blank_lines(app, tmp_path):
    path = tmp_path / "k.csv"
    path.write_text(
        "\ufeff# header comment\n\nuser,api_key\n\nalice,key-a\n"
        "# mid comment\n  ,  \nbob , key-b \n",
        encoding="utf-8",
    )
    assert app.load_api_keys_csv(path) == [("alice", "key-a"), ("bob", "key-b")]


def test_load_csv_empty_key_skipped_and_blank_user_numbered(app, tmp_path, capsys):
    path = tmp_path / "k.csv"
    path.write_text(
        "user,api_key\nalice,key-a\nbob,\n,key-c\ncarol\n", encoding="utf-8"
    )
    result = app.load_api_keys_csv(path)
    # Row numbers are 1-based data rows: blank-user row is data row 3.
    assert result == [("alice", "key-a"), ("user-3", "key-c")]
    out = capsys.readouterr().out
    assert "data row 2 has no api_key" in out
    assert "data row 4 has no api_key" in out
    assert "key-a" not in out and "key-c" not in out


def test_load_csv_without_user_column(app, tmp_path):
    path = tmp_path / "k.csv"
    path.write_text("api_key\nkey-a\nkey-b\n", encoding="utf-8")
    assert app.load_api_keys_csv(path) == [("user-1", "key-a"), ("user-2", "key-b")]


def test_load_csv_no_header_warns_and_returns_empty(app, tmp_path, capsys):
    path = tmp_path / "k.csv"
    path.write_text("alice,key-a\nbob,key-b\n", encoding="utf-8")
    assert app.load_api_keys_csv(path) == []
    out = capsys.readouterr().out
    assert "header must contain" in out
    assert "key-a" not in out


def test_load_csv_empty_file(app, tmp_path):
    path = tmp_path / "k.csv"
    path.write_text("", encoding="utf-8")
    assert app.load_api_keys_csv(path) == []


def test_load_csv_missing_file_raises(app, tmp_path):
    with pytest.raises(OSError):
        app.load_api_keys_csv(tmp_path / "nope.csv")


# --- build_user_keys ---------------------------------------------------------


def test_build_user_keys_default_first(app):
    pool = app.build_user_keys("env-key", [("alice", "key-a"), ("bob", "key-b")])
    assert pool == [("default", "env-key"), ("alice", "key-a"), ("bob", "key-b")]


def test_build_user_keys_no_csv(app):
    assert app.build_user_keys("env-key", []) == [("default", "env-key")]


def test_build_user_keys_dedupes_keys(app, capsys):
    pool = app.build_user_keys(
        "env-key", [("alice", "env-key"), ("bob", "key-b"), ("bob2", "key-b")]
    )
    assert pool == [("default", "env-key"), ("bob", "key-b")]
    out = capsys.readouterr().out
    assert "alice" in out and "bob2" in out
    assert "env-key" not in out and "key-b" not in out


def test_build_user_keys_duplicate_labels_suffixed(app):
    pool = app.build_user_keys(
        "env-key",
        [("alice", "k1"), ("alice", "k2"), ("alice", "k3"), ("default", "k4")],
    )
    assert [u for u, _ in pool] == ["default", "alice", "alice-2", "alice-3", "default-2"]
    assert [k for _, k in pool] == ["env-key", "k1", "k2", "k3", "k4"]


# --- send_prompt user label --------------------------------------------------


class _FakeApi:
    def __init__(self, name: str = "fake") -> None:
        self.name = name
        self.calls: list[tuple[str, str]] = []

    def request(self, url, *, method="GET", body=None, retries=3):
        self.calls.append((method, url))
        return {}  # no run_id -> fire-and-forget, no polling


def _entry(app):
    return app.PoolEntry(
        name="my_agent", agent_id="a-1", flow_triggering=False, prompts=["hello"]
    )


def test_send_prompt_prefixes_user_label(app, capsys):
    api = _FakeApi()
    app.send_prompt(api, "https://x/instances/1", _entry(app), "alice")
    out = capsys.readouterr().out
    assert "[alice] my_agent" in out
    assert api.calls == [("POST", "https://x/instances/1/v1/orchestrate/runs")]


def test_send_prompt_no_user_keeps_unprefixed_log(app, capsys):
    app.send_prompt(_FakeApi(), "https://x/instances/1", _entry(app))
    out = capsys.readouterr().out
    assert "my_agent" in out
    assert "[alice]" not in out
    # label must start right after the timestamp, i.e. no "[user] " prefix
    assert out.split("Z] ", 1)[1].startswith("my_agent")


# --- main(): per-call user selection ----------------------------------------


@pytest.fixture
def main_env(app, tmp_path, monkeypatch):
    """Patch everything main() touches so it runs offline and stops after N sends."""
    monkeypatch.setenv("WXO_API_KEY", "env-key")
    monkeypatch.setenv("WXO_URL", "https://x/instances/1")
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("WXO_API_KEYS_FILE", raising=False)
    monkeypatch.delenv("AGENT_FILTER", raising=False)

    class FakeTokens:
        failing: set[str] = set()

        def __init__(self, api_key, env_type):
            self.api_key = api_key

        def get(self):
            if self.api_key in FakeTokens.failing:
                raise RuntimeError("token exchange failed")
            return "tok"

        def refresh(self):
            return self.get()

    sent: list[tuple[str, str | None]] = []
    limit = {"n": 40}

    def fake_send(api, base_url, entry, user=None):
        sent.append((api._tokens.api_key, user))
        if len(sent) >= limit["n"]:
            raise _StopLoop

    spec = app.AgentSpec(name="my_agent", flow_triggering=False, prompts=["hi"])
    pool_entry = app.PoolEntry(
        name="my_agent", agent_id="a-1", flow_triggering=False, prompts=["hi"]
    )
    catalog_apis: list[str] = []

    def fake_catalog(api, base_url):
        catalog_apis.append(api._tokens.api_key)
        return {"my_agent": app.CatalogEntry("a-1", {})}

    monkeypatch.setattr(app, "TokenManager", FakeTokens)
    monkeypatch.setattr(app, "discover_agents", lambda root, flt: [spec])
    monkeypatch.setattr(app, "load_catalog", fake_catalog)
    monkeypatch.setattr(app, "resolve_pool", lambda s, c, e: [pool_entry])
    monkeypatch.setattr(app, "send_prompt", fake_send)
    monkeypatch.setattr(app.time, "sleep", lambda s: None)
    app.random.seed(1234)
    return {"sent": sent, "tokens": FakeTokens, "catalog": catalog_apis, "limit": limit}


def test_main_picks_random_user_per_call(app, main_env, tmp_path, monkeypatch, capsys):
    keys = tmp_path / "api-keys.csv"
    keys.write_text("user,api_key\nalice,key-a\nbob,key-b\n", encoding="utf-8")
    monkeypatch.setenv("WXO_API_KEYS_FILE", str(keys))

    with pytest.raises(_StopLoop):
        app.main()

    sent = main_env["sent"]
    assert len(sent) == 40
    used = {user for _, user in sent}
    assert used == {"default", "alice", "bob"}
    # each call's user label matches the key that was actually used
    expected = {"default": "env-key", "alice": "key-a", "bob": "key-b"}
    assert all(expected[user] == key for key, user in sent)
    # catalog uses the default user
    assert main_env["catalog"] == ["env-key"]
    out = capsys.readouterr().out
    assert "Users in pool (3): default, alice, bob" in out
    for secret in ("env-key", "key-a", "key-b"):
        assert secret not in out


def test_main_without_csv_single_default_user_unlabelled(app, main_env):
    main_env["limit"]["n"] = 5
    with pytest.raises(_StopLoop):
        app.main()
    # no CSV -> only the env key and no user label passed to send_prompt
    assert main_env["sent"] == [("env-key", None)] * 5


def test_main_missing_csv_file_falls_back_to_env_key(app, main_env, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("WXO_API_KEYS_FILE", str(tmp_path / "missing.csv"))
    main_env["limit"]["n"] = 3
    with pytest.raises(_StopLoop):
        app.main()
    assert main_env["sent"] == [("env-key", None)] * 3
    assert "Cannot read WXO_API_KEYS_FILE" in capsys.readouterr().out


def test_main_drops_failing_keys(app, main_env, tmp_path, monkeypatch, capsys):
    keys = tmp_path / "api-keys.csv"
    keys.write_text("user,api_key\nalice,key-a\nbob,key-b\n", encoding="utf-8")
    monkeypatch.setenv("WXO_API_KEYS_FILE", str(keys))
    main_env["tokens"].failing = {"key-a"}

    with pytest.raises(_StopLoop):
        app.main()

    assert {user for _, user in main_env["sent"]} == {"default", "bob"}
    out = capsys.readouterr().out
    assert "User 'alice': authentication failed" in out
    assert "key-a" not in out


def test_main_default_failing_uses_first_valid_user_for_catalog(
    app, main_env, tmp_path, monkeypatch
):
    keys = tmp_path / "api-keys.csv"
    keys.write_text("user,api_key\nalice,key-a\n", encoding="utf-8")
    monkeypatch.setenv("WXO_API_KEYS_FILE", str(keys))
    main_env["tokens"].failing = {"env-key"}

    with pytest.raises(_StopLoop):
        app.main()

    assert main_env["catalog"] == ["key-a"]
    assert {user for _, user in main_env["sent"]} == {"alice"}


def test_main_all_keys_failing_exits(app, main_env, tmp_path, monkeypatch):
    keys = tmp_path / "api-keys.csv"
    keys.write_text("user,api_key\nalice,key-a\n", encoding="utf-8")
    monkeypatch.setenv("WXO_API_KEYS_FILE", str(keys))
    main_env["tokens"].failing = {"env-key", "key-a"}

    with pytest.raises(SystemExit) as exc:
        app.main()
    assert exc.value.code == 1
    assert main_env["sent"] == []

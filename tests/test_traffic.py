"""Tests for traffic generator commands and container management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from helpers import make_scenario, make_standalone, write
from wxodemo import cli, config, traffic
from wxodemo.config import Config, UsageError
from wxodemo.logging_setup import setup_logging


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    """A test repo with one scenario, one standalone agent, and traffic-gen assets."""
    make_scenario(tmp_path, "test-scenario")
    # write smoke prompts in evaluation
    eval_dir = tmp_path / "evaluation" / "test-scenario"
    eval_dir.mkdir(parents=True, exist_ok=True)
    write(
        eval_dir / "ground_truth.json",
        json.dumps({
            "smoke_prompts": [
                {"id": "s1", "prompt": "Prompt for test scenario 1"},
                {"id": "s2", "prompt": "Prompt for test scenario 2"},
            ]
        }),
    )

    make_standalone(tmp_path, "test-standalone", "test_standalone", tool="greeting")
    # write standalone prompts in traffic-gen/prompts.yaml
    tg_dir = tmp_path / "traffic-gen"
    tg_dir.mkdir(parents=True, exist_ok=True)
    write(
        tg_dir / "prompts.yaml",
        "test_standalone:\n  - Standalone prompt 1\n  - Standalone prompt 2\n",
    )
    write(tg_dir / "Dockerfile", "FROM python:3.11-slim\n")

    setup_logging(tmp_path / "local" / "wxodemo.log")
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "log_path", lambda: tmp_path / "local" / "wxodemo.log")
    return tmp_path


def test_find_container_engine_preferred(monkeypatch):
    monkeypatch.setattr(
        traffic.shutil, "which", lambda cmd: f"/usr/bin/{cmd}" if cmd == "docker" else None
    )
    name, exe = traffic.find_container_engine("docker")
    assert name == "docker"
    assert exe == "/usr/bin/docker"

    with pytest.raises(UsageError, match="not found on PATH"):
        traffic.find_container_engine("podman")

    with pytest.raises(UsageError, match="Unsupported container engine"):
        traffic.find_container_engine("containerd")


def test_find_container_engine_autodetect(monkeypatch):
    def fake_which(cmd):
        if cmd == "podman":
            return "/usr/bin/podman"
        if cmd == "docker":
            return "/usr/bin/docker"
        return None

    monkeypatch.setattr(traffic.shutil, "which", fake_which)
    name, exe = traffic.find_container_engine()
    assert name == "podman"
    assert exe == "/usr/bin/podman"


def test_find_container_engine_none_found(monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: None)
    with pytest.raises(UsageError, match="No container engine"):
        traffic.find_container_engine()


def test_discover_traffic_pool(repo):
    pool = traffic.discover_traffic_pool(repo)
    names = [a.name for a in pool]
    assert "test_scenario" in names or "test_scenario_agent" in names or len(names) >= 2
    standalone = next(a for a in pool if a.kind == "standalone")
    assert standalone.name == "test_standalone"
    assert len(standalone.prompts) == 2


def test_discover_traffic_pool_with_filter(repo):
    pool = traffic.discover_traffic_pool(repo, agent_filter=["test_standalone"])
    assert len(pool) == 1
    assert pool[0].name == "test_standalone"


def test_traffic_pool_cli_output(repo, capsys):
    code = traffic.run_traffic_pool(repo)
    assert code == 0
    out = capsys.readouterr().out
    assert "Traffic Generator Discovered Pool" in out
    assert "test_standalone" in out


def test_traffic_pool_cli_json_output(repo, capsys):
    code = traffic.run_traffic_pool(repo, json_output=True)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert any(item["name"] == "test_standalone" for item in data)


def test_traffic_build_dry_run(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    code = traffic.run_traffic_build(repo, dry_run=True)
    assert code == 0
    out = capsys.readouterr().out
    assert (
        "[dry-run] would run: /usr/bin/docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen ."
        in out
    )


def test_traffic_start_dry_run(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    code = traffic.run_traffic_start(
        repo,
        cfg,
        interval=5,
        agents="agent1,agent2",
        env="draft",
        dry_run=True,
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "[dry-run] would run:" in out
    assert "-e CALL_INTERVAL_MINUTES=5" in out
    assert "-e AGENT_FILTER=agent1,agent2" in out
    assert "-e WXO_ENVIRONMENT=draft" in out
    # Secret should be masked
    assert "k-secret-1234" not in out


def _dry_run_start(repo, capsys, monkeypatch) -> tuple[int, str]:
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    code = traffic.run_traffic_start(repo, cfg, dry_run=True)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def test_read_api_keys_csv(tmp_path):
    path = tmp_path / "keys.csv"
    path.write_text(
        "\ufeff# comment\n\nuser,api_key\nalice,key-a\n,key-b\nbob,\n# skip\ncarol,  key-c  \n",
        encoding="utf-8",
    )
    assert traffic.read_api_keys_csv(path) == ["key-a", "key-b", "key-c"]


def test_read_api_keys_csv_no_header_or_empty(tmp_path):
    no_header = tmp_path / "noheader.csv"
    no_header.write_text("alice,key-a\nbob,key-b\n", encoding="utf-8")
    assert traffic.read_api_keys_csv(no_header) == []

    empty = tmp_path / "empty.csv"
    empty.write_text("\n# only comments\n", encoding="utf-8")
    assert traffic.read_api_keys_csv(empty) == []


def test_traffic_start_without_keys_csv(repo, capsys, monkeypatch):
    code, out = _dry_run_start(repo, capsys, monkeypatch)
    assert code == 0
    assert "api-keys.csv" not in out
    assert "WXO_API_KEYS_FILE" not in out
    assert " -v " not in out


def test_traffic_start_with_keys_csv(repo, capsys, monkeypatch):
    keys_file = repo / "api-keys.csv"
    keys_file.write_text("user,api_key\nalice,key-alice-111\nbob,key-bob-222\n", encoding="utf-8")
    code, out = _dry_run_start(repo, capsys, monkeypatch)
    assert code == 0
    assert f"-v {keys_file.resolve()}:/app/api-keys.csv:ro" in out
    assert "-e WXO_API_KEYS_FILE=/app/api-keys.csv" in out
    assert "Using 2 users from api-keys.csv" in out
    # Image name stays last; mount comes before it
    assert out.strip().splitlines()[-1].endswith(traffic.DEFAULT_IMAGE)
    # No key values anywhere in the output
    for secret in ("k-secret-1234", "key-alice-111", "key-bob-222"):
        assert secret not in out


def test_traffic_start_keys_csv_not_readable(repo, capsys, monkeypatch):
    (repo / "api-keys.csv").write_bytes(b"user,api_key\nalice,\xff\xfe\xfa\n")
    code, out = _dry_run_start(repo, capsys, monkeypatch)
    assert code == 0
    assert "Could not read api-keys.csv" in out
    assert "WXO_API_KEYS_FILE" not in out
    assert " -v " not in out


def test_traffic_start_keys_csv_without_header(repo, capsys, monkeypatch):
    (repo / "api-keys.csv").write_text("alice,key-alice-111\n", encoding="utf-8")
    code, out = _dry_run_start(repo, capsys, monkeypatch)
    assert code == 0
    assert "Using 0 users from api-keys.csv" in out
    assert "key-alice-111" not in out


def test_traffic_stop_dry_run(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/podman")
    code = traffic.run_traffic_stop(repo, dry_run=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "[dry-run] would stop and remove container 'wxo-traffic-gen' using podman" in out


def test_traffic_redeploy_dry_run(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    code = traffic.run_traffic_redeploy(repo, cfg, dry_run=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "[dry-run] would stop and remove container" in out
    assert "[dry-run] would run: /usr/bin/docker build" in out
    assert "[dry-run] would run: /usr/bin/docker run" in out


def test_traffic_restart_dry_run(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    code = traffic.run_traffic_restart(repo, cfg, dry_run=True)
    assert code == 0
    out = capsys.readouterr().out
    assert "[dry-run] would stop and remove container" in out
    assert "[dry-run] would run: /usr/bin/docker run" in out
    assert " build" not in out


def test_traffic_restart_starts_even_if_stop_fails(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    started = []

    def boom(*args, **kwargs):
        raise RuntimeError("stop exploded")

    monkeypatch.setattr(traffic, "run_traffic_stop", boom)
    monkeypatch.setattr(
        traffic, "run_traffic_start", lambda *a, **k: started.append(True) or 0
    )
    assert traffic.run_traffic_restart(repo, cfg) == 0
    assert started == [True]
    assert "starting anyway" in capsys.readouterr().out

    started.clear()
    monkeypatch.setattr(traffic, "run_traffic_stop", lambda *a, **k: 1)
    assert traffic.run_traffic_restart(repo, cfg) == 0
    assert started == [True]


def test_traffic_start_already_running(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    monkeypatch.setattr(traffic, "_is_container_running", lambda exe, name: True)
    cfg = Config(api_key="k-secret-1234", url="https://api.test/instances/1", env_name="demo")
    code = traffic.run_traffic_start(repo, cfg, dry_run=False)
    assert code == 1
    out = capsys.readouterr().out
    assert "already running" in out


def test_traffic_logs_defaults_to_follow(repo, monkeypatch):
    called_cmd = []

    def fake_run(cmd, **kwargs):
        called_cmd.extend(cmd)
        import subprocess

        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    monkeypatch.setattr(traffic, "_run_cmd", fake_run)
    code = traffic.run_traffic_logs(repo)
    assert code == 0
    assert called_cmd == ["/usr/bin/docker", "logs", "-f", "wxo-traffic-gen"]


def test_traffic_cli_dispatch(repo, capsys, monkeypatch):
    monkeypatch.setattr(traffic.shutil, "which", lambda cmd: "/usr/bin/docker")
    write(repo / "env.cfg", "WXO_API_KEY=k-secret-1234\nWXO_URL=https://x/instances/1\nWXO_ENV_NAME=demo\n")
    monkeypatch.setattr(cli, "load_config", lambda: config.load_config(repo / "env.cfg"))

    # test traffic build --dry-run
    code = cli.main(["traffic", "build", "--dry-run"])
    assert code == 0
    assert "[dry-run]" in capsys.readouterr().out

    # test traffic-gen pool
    code = cli.main(["traffic-gen", "pool"])
    assert code == 0
    assert "Traffic Generator Discovered Pool" in capsys.readouterr().out

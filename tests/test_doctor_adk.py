"""doctor (machine readiness) and adk (finding and running the orchestrate CLI)."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxodemo import adk, doctor
from wxodemo.config import Config, ConfigError
from wxodemo.logging_setup import register_secret, setup_logging

CFG = Config(api_key="k-secret-1234", url="https://x/instances/1", env_name="demo", env_type="mcsp")


@pytest.fixture(autouse=True)
def logging_ready(tmp_path: Path, capsys):
    setup_logging(tmp_path / "local" / "t.log")


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


@pytest.fixture
def healthy(monkeypatch):
    """Everything present and configured; tests break one thing at a time."""
    monkeypatch.setattr(doctor, "_package_version", lambda name: "1.2.3")
    monkeypatch.setattr(doctor, "find_orchestrate", lambda: Path("orchestrate"))
    monkeypatch.setattr(doctor, "load_config", lambda: CFG)
    monkeypatch.setattr(doctor, "active_env_lines", lambda: ["demo (active)"])
    monkeypatch.setattr(doctor, "in_virtualenv", lambda: True)


def test_doctor_all_good(healthy, capsys):
    assert doctor.run_doctor() == 0
    out = capsys.readouterr().out
    assert "orchestrate CLI found" in out
    assert "env.cfg is complete" in out
    assert "environment 'demo' is active" in out
    assert "k-secret-1234" not in out


def test_doctor_missing_env_cfg_is_exit_2_not_1(healthy, monkeypatch, capsys):
    def missing():
        raise ConfigError("env.cfg not found at x")

    monkeypatch.setattr(doctor, "load_config", missing)
    assert doctor.run_doctor() == 2
    assert "env.cfg: env.cfg not found" in capsys.readouterr().out


def test_doctor_missing_orchestrate_cli_fails(healthy, monkeypatch, capsys):
    monkeypatch.setattr(doctor, "find_orchestrate", lambda: None)
    assert doctor.run_doctor() == 1
    assert "orchestrate CLI not found" in capsys.readouterr().out


def test_doctor_missing_adk_package_fails_but_yaml_only_warns(healthy, monkeypatch, capsys):
    monkeypatch.setattr(doctor, "_package_version", lambda name: None)
    assert doctor.run_doctor() == 1
    out = capsys.readouterr().out
    assert "ibm-watsonx-orchestrate is not installed" in out
    assert "PyYAML is not installed" in out


def test_doctor_yaml_missing_alone_is_only_a_warning(healthy, monkeypatch):
    monkeypatch.setattr(
        doctor, "_package_version", lambda name: None if name == "PyYAML" else "1.0"
    )
    assert doctor.run_doctor() == 0


def test_doctor_old_python_fails(healthy, monkeypatch, capsys):
    monkeypatch.setattr(doctor.sys, "version_info", (3, 9, 0, "final", 0))
    assert doctor.run_doctor() == 1
    assert "3.11+ is required" in capsys.readouterr().out


def test_doctor_without_venv_is_only_informational(healthy, monkeypatch, capsys):
    monkeypatch.setattr(doctor, "in_virtualenv", lambda: False)
    assert doctor.run_doctor() == 0
    assert "No virtual environment (optional" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("active", "expected"),
    [
        ([], "No active WXO environment yet"),
        (["other (active)"], "Active WXO environment: other (active)"),
    ],
)
def test_doctor_reports_other_or_no_active_environment(
    healthy, monkeypatch, capsys, active, expected
):
    monkeypatch.setattr(doctor, "active_env_lines", lambda: active)
    assert doctor.run_doctor() == 0
    assert expected in capsys.readouterr().out


def test_in_virtualenv_follows_sys_prefix(monkeypatch):
    monkeypatch.setattr(doctor.sys, "prefix", "/venv")
    monkeypatch.setattr(doctor.sys, "base_prefix", "/usr")
    assert doctor.in_virtualenv() is True
    monkeypatch.setattr(doctor.sys, "base_prefix", "/venv")
    assert doctor.in_virtualenv() is False


def test_package_version_of_an_unknown_package_is_none():
    assert doctor._package_version("definitely-not-installed-xyz") is None
    assert doctor._package_version("pytest")


# ---------------------------------------------------------------------------
# adk: locating the CLI
# ---------------------------------------------------------------------------


def test_find_orchestrate_prefers_the_interpreters_own_folder(tmp_path, monkeypatch):
    fake_python = tmp_path / "python.exe"
    (tmp_path / "orchestrate.exe").write_text("")
    monkeypatch.setattr(adk.sys, "executable", str(fake_python))
    monkeypatch.setattr(adk.shutil, "which", lambda name: "/elsewhere/orchestrate")
    assert adk.find_orchestrate() == tmp_path / "orchestrate.exe"


def test_find_orchestrate_falls_back_to_path_then_none(tmp_path, monkeypatch):
    monkeypatch.setattr(adk.sys, "executable", str(tmp_path / "python.exe"))
    monkeypatch.setattr(adk.shutil, "which", lambda name: "/usr/bin/orchestrate")
    assert adk.find_orchestrate() == Path("/usr/bin/orchestrate")
    monkeypatch.setattr(adk.shutil, "which", lambda name: None)
    assert adk.find_orchestrate() is None


# ---------------------------------------------------------------------------
# adk: running it
# ---------------------------------------------------------------------------


@pytest.fixture
def popen(monkeypatch):
    """Replace subprocess.run inside adk; records the call and returns a canned result."""
    state = SimpleNamespace(calls=[], result=SimpleNamespace(returncode=0, stdout="out", stderr=""))
    monkeypatch.setattr(adk, "find_orchestrate", lambda: Path("/bin/orchestrate"))

    def run(command, **kwargs):
        state.calls.append((command, kwargs))
        return state.result

    monkeypatch.setattr(adk.subprocess, "run", run)
    return state


def test_run_orchestrate_passes_args_and_never_inherits_stdin(popen):
    adk.run_orchestrate(["agents", "list"])
    command, kwargs = popen.calls[0]
    assert command[1:] == ["agents", "list"]
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["env"]["PYTHONUTF8"] == "1"


def test_run_orchestrate_with_input_text_uses_a_pipe(popen):
    adk.run_orchestrate(["env", "add"], input_text="Y\n")
    _, kwargs = popen.calls[0]
    assert kwargs["input"] == "Y\n" and kwargs["stdin"] is None


def test_run_orchestrate_failure_raises_with_exit_code_and_masks_the_key(popen):
    register_secret("k-secret-1234")
    popen.result = SimpleNamespace(returncode=3, stdout="", stderr="bad key k-secret-1234\nline2")
    with pytest.raises(adk.AdkError) as info:
        adk.run_orchestrate(["env", "activate", "demo", "--api-key", "k-secret-1234"])
    assert info.value.returncode == 3
    assert "k-secret-1234" not in str(info.value) and "****" in str(info.value)


def test_run_orchestrate_check_false_returns_the_failure(popen):
    popen.result = SimpleNamespace(returncode=1, stdout="", stderr="nope")
    assert adk.run_orchestrate(["x"], check=False).returncode == 1


def test_run_orchestrate_without_cli_raises_127_with_a_hint(monkeypatch):
    monkeypatch.setattr(adk, "find_orchestrate", lambda: None)
    with pytest.raises(adk.AdkNotFoundError) as info:
        adk.run_orchestrate(["agents", "list"])
    assert info.value.returncode == 127 and "wxodemo.py setup" in str(info.value)


def test_run_orchestrate_logs_output_but_masks_secrets(popen, tmp_path):
    register_secret("k-secret-1234")
    popen.result = SimpleNamespace(returncode=0, stdout="token k-secret-1234", stderr="warn")
    adk.run_orchestrate(["x", "k-secret-1234"])
    text = (tmp_path / "local" / "t.log").read_text(encoding="utf-8")
    assert "k-secret-1234" not in text and "token ****" in text


# ---------------------------------------------------------------------------
# adk: login
# ---------------------------------------------------------------------------


def test_login_registers_then_activates_with_the_right_arguments(monkeypatch):
    calls = []
    monkeypatch.setattr(adk, "run_orchestrate", lambda args, **kw: calls.append((args, kw)))
    adk.login(CFG)
    (add_args, add_kw), (act_args, _) = calls
    assert add_args == [
        "env", "add", "-n", "demo", "-u", "https://x/instances/1", "--type", "mcsp"
    ]  # fmt: skip
    assert add_kw["input_text"] == "Y\n", "answers the 'update existing?' prompt: idempotent"
    assert act_args == ["env", "activate", "demo", "--api-key", "k-secret-1234"]


def test_login_stops_when_registering_fails(monkeypatch):
    def boom(args, **kw):
        raise adk.AdkError("add failed")

    monkeypatch.setattr(adk, "run_orchestrate", boom)
    with pytest.raises(adk.AdkError):
        adk.login(CFG)


def test_active_env_lines(monkeypatch):
    out = "a\ndemo   https://x   (active)\nother\n"
    monkeypatch.setattr(
        adk, "run_orchestrate", lambda args, **kw: SimpleNamespace(stdout=out, returncode=0)
    )
    assert adk.active_env_lines() == ["demo   https://x   (active)"]


def test_active_env_lines_is_empty_on_any_failure(monkeypatch):
    def boom(args, **kw):
        raise adk.AdkError("no cli", 127)

    monkeypatch.setattr(adk, "run_orchestrate", boom)
    assert adk.active_env_lines() == []


def test_running_python_executable_is_the_one_used_for_pip():
    # setup uses sys.executable; guard against anyone switching it to a bare "python"
    from wxodemo import cli

    assert "sys.executable" in Path(cli.__file__).read_text(encoding="utf-8")
    assert sys.executable

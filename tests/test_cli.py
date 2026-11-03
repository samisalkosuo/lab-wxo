"""The command line end to end: argument parsing, exit codes and wiring, orchestrate mocked.

Every test runs `main([...])` against a throwaway repo, so it never reads the real env.cfg,
never writes the real log and never calls WXO.
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import FakeOrchestrate, make_scenario, make_standalone, make_tool_pkg, write
from wxodemo import cli, config, deploy, scaffold

ENV_OK = "WXO_API_KEY=k-secret-1234\nWXO_URL=https://x/instances/1\nWXO_ENV_NAME=demo\n"
REAL_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo(tmp_path: Path, monkeypatch, capsys) -> Path:
    """A repo with one live scenario, one standalone agent and a valid env.cfg."""
    make_scenario(tmp_path, "alpha")
    make_standalone(tmp_path, "hello-world", "hello_world", tool="greeting")
    write(tmp_path / "env.cfg", ENV_OK)
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "log_path", lambda: tmp_path / "local" / "wxodemo.log")
    monkeypatch.setattr(cli, "load_config", lambda: config.load_config(tmp_path / "env.cfg"))
    return tmp_path


@pytest.fixture
def fake(repo, monkeypatch) -> FakeOrchestrate:
    fake = FakeOrchestrate()
    monkeypatch.setattr(deploy, "run_orchestrate", fake)
    monkeypatch.setattr(deploy, "login", lambda cfg: None)
    return fake


def run(capsys, *argv: str) -> tuple[int, str]:
    code = cli.main(list(argv))
    return code, capsys.readouterr().out


# ---------------------------------------------------------------------------
# parser
# ---------------------------------------------------------------------------


def test_no_command_prints_help_and_exits_0(capsys):
    assert cli.main([]) == 0
    assert "usage: wxodemo" in capsys.readouterr().out


def test_every_documented_command_is_registered():
    parser = cli.build_parser()
    choices = next(a for a in parser._actions if a.dest == "command").choices
    expected = {
        "setup", "doctor", "login", "activate", "list", "status", "deploy", "undeploy",
        "validate", "smoke", "export-chats", "new-scenario", "eval", "logs",
        "traffic", "traffic-gen",
    }  # fmt: skip
    assert expected <= set(choices)


def test_activate_is_an_alias_of_login():
    parser = cli.build_parser()
    assert parser.parse_args(["activate"]).func is cli.cmd_login


def test_unknown_command_and_bad_flag_exit_2_via_argparse():
    for argv in (["frobnicate"], ["deploy", "--nope"], ["new-scenario"]):
        with pytest.raises(SystemExit) as info:
            cli.build_parser().parse_args(argv)
        assert info.value.code == 2


# ---------------------------------------------------------------------------
# list / validate / logs
# ---------------------------------------------------------------------------


def test_list_shows_all_and_filters_by_kind(repo, capsys):
    make_tool_pkg(repo, "report_generator", tools=["gen_rep"])
    code, out = run(capsys, "list")
    assert code == 0 and "alpha" in out and "hello_world" in out and "report_generator" in out
    _, only_standalone = run(capsys, "list", "--kind", "standalone")
    assert (
        "hello_world" in only_standalone
        and "alpha" not in only_standalone
        and "report_generator" not in only_standalone
    )
    _, only_tools = run(capsys, "list", "--kind", "tool")
    assert (
        "report_generator" in only_tools
        and "hello_world" not in only_tools
        and "alpha" not in only_tools
    )


def test_list_empty_repo(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "log_path", lambda: tmp_path / "local" / "x.log")
    assert run(capsys, "list") == (0, "Nothing found.\n")


def test_validate_ok_and_unknown_name(repo, capsys):
    write(repo / "docs/demo/scenarios/alpha.js", "//")
    write(repo / scaffold.PRESENTATION, '<script src="scenarios/alpha.js"></script>\n')
    code, out = run(capsys, "validate")
    assert code == 0 and "alpha" in out
    code, out = run(capsys, "validate", "nope")
    assert code == 2 and "Unknown target 'nope'" in out


def test_validate_standalone_only_has_nothing_to_check(repo, capsys):
    code, out = run(capsys, "validate", "hello_world")
    assert code == 0 and "No scenarios selected" in out


def test_validate_reports_problems_with_exit_1(repo, capsys):
    (repo / "docs/demo/alpha-demo.md").unlink()
    code, out = run(capsys, "validate", "alpha")
    assert code == 1 and "problem(s)" in out


def test_logs_before_and_after_a_run(repo, capsys):
    (repo / "local").mkdir(exist_ok=True)
    code, out = run(capsys, "logs")
    # main() itself logs "wxodemo x.y: logs", so the file exists once main has started
    assert code == 0 and "Log file:" in out
    code, out = run(capsys, "logs", "-n", "1")
    assert code == 0 and "wxodemo" in out


# ---------------------------------------------------------------------------
# deploy / undeploy / status wiring and exit codes
# ---------------------------------------------------------------------------


def test_deploy_needs_a_target(repo, capsys):
    code, out = run(capsys, "deploy")
    assert code == 2 and "--all" in out


def test_deploy_name_and_all_together_is_a_usage_error(repo, capsys):
    code, _ = run(capsys, "deploy", "alpha", "--all")
    assert code == 2


def test_deploy_dry_run_works_without_env_cfg(repo, fake, capsys):
    (repo / "env.cfg").unlink()
    code, out = run(capsys, "deploy", "--all", "--dry-run")
    assert code == 0 and "Dry run only" in out
    assert fake.calls == []


def test_deploy_without_env_cfg_fails_with_2_and_explains(repo, fake, capsys):
    (repo / "env.cfg").unlink()
    code, out = run(capsys, "deploy", "alpha")
    assert code == 2
    assert "env.cfg not found" in out and "WXO_API_KEY" in out
    assert fake.calls == []


def test_deploy_with_incomplete_env_cfg_names_the_missing_keys(repo, fake, capsys):
    write(repo / "env.cfg", "WXO_API_KEY=abc\n")
    code, out = run(capsys, "deploy", "alpha")
    assert code == 2 and "WXO_URL" in out and "WXO_ENV_NAME" in out


def test_deploy_runs_orchestrate_and_hides_the_key(repo, fake, capsys):
    code, out = run(capsys, "deploy", "alpha")
    assert code == 0 and "Deployed 1 target(s)" in out
    assert any(c.startswith("agents import") for c in fake.commands())
    log = (repo / "local" / "wxodemo.log").read_text(encoding="utf-8")
    assert "k-secret-1234" not in out + log


def test_deploy_failure_exits_1_and_points_to_the_log(repo, fake, capsys):
    fake.fail_on = ["tools import"]
    code, out = run(capsys, "deploy", "alpha")
    assert code == 1 and "failed" in out


def test_deploy_all_skips_soon_scenarios(repo, fake, capsys):
    make_scenario(repo, "beta", status="soon", tool="other")
    code, _ = run(capsys, "deploy", "--all", "--dry-run")
    assert code == 0
    code, out = run(capsys, "deploy", "--all", "--dry-run")
    assert "beta" not in out and "alpha" in out


def test_undeploy_refuses_without_yes_when_not_interactive(repo, fake, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: False))
    code, out = run(capsys, "undeploy", "alpha")
    assert code == 2 and "--yes" in out
    assert not any("remove" in c for c in fake.commands())


def test_undeploy_yes_removes_and_second_run_is_a_noop(repo, fake, capsys):
    fake.existing = {"agents": ["agent_alpha"], "tools": ["do_it"], "knowledge-bases": ["kb_alpha"]}
    code, out = run(capsys, "undeploy", "alpha", "--yes")
    assert code == 0 and "Removed resources" in out
    assert "agents remove --name agent_alpha --kind native" in fake.commands()

    fake.calls.clear()
    fake.existing = {"agents": [], "tools": [], "knowledge-bases": []}
    code, out = run(capsys, "undeploy", "alpha", "--yes")
    assert code == 0 and "Nothing to remove" in out
    assert not any("remove" in c for c in fake.commands())


def test_undeploy_dry_run_changes_nothing(repo, fake, capsys):
    code, out = run(capsys, "undeploy", "--all", "--dry-run")
    assert code == 0 and "Would undeploy" in out and fake.calls == []


def test_status_prints_a_table(repo, fake, capsys):
    code, out = run(capsys, "status", "--all")
    assert code == 0 and "not deployed" in out and "alpha" in out


def test_kind_flag_disambiguates_a_name_used_by_both_kinds(repo, fake, capsys):
    make_standalone(repo, "alpha-agent", "alpha")
    code, out = run(capsys, "deploy", "alpha", "--dry-run")
    assert code == 2 and "--kind" in out
    code, out = run(capsys, "deploy", "alpha", "--kind", "scenario", "--dry-run")
    assert code == 0 and "(scenario)" in out


def test_deploy_and_undeploy_tool_cli(repo, fake, capsys):
    make_tool_pkg(repo, "report_generator", tools=["gen_rep"])
    code, out = run(capsys, "deploy", "report_generator", "--dry-run")
    assert code == 0
    assert "Deploying report_generator (tool)" in out
    assert "tools import -k python -p" in out

    code, out = run(capsys, "undeploy", "report_generator", "--dry-run")
    assert code == 0
    assert "Would undeploy report_generator (tool)" in out
    assert "tools remove --name gen_rep" in out


# ---------------------------------------------------------------------------
# login / setup / doctor
# ---------------------------------------------------------------------------


def test_login_dry_run_and_real(repo, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(cli, "login", lambda cfg: seen.append(cfg))
    code, out = run(capsys, "login", "--dry-run")
    assert code == 0 and "would register 'demo'" in out and seen == []
    assert "k-secret-1234" not in out

    code, out = run(capsys, "activate")
    assert code == 0 and "Environment 'demo' is active" in out
    assert seen[0].env_name == "demo"


def test_login_without_env_cfg_exits_2(repo, capsys):
    (repo / "env.cfg").unlink()
    code, out = run(capsys, "login")
    assert code == 2 and "env.cfg not found" in out


def test_setup_dry_run_shows_the_pip_command(repo, capsys):
    write(repo / "requirements.txt", "x\n")
    code, out = run(capsys, "setup", "--dry-run")
    assert code == 0 and "-m pip install -r" in out


def test_setup_without_requirements_file(repo, capsys):
    code, out = run(capsys, "setup")
    assert code == 1 and "requirements.txt not found" in out


@pytest.mark.parametrize(("pip_rc", "expected"), [(0, "doctor-called"), (1, 1)])
def test_setup_runs_pip_then_doctor(repo, monkeypatch, capsys, pip_rc, expected):
    write(repo / "requirements.txt", "x\n")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=pip_rc, stdout="", stderr="resolver exploded")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(cli, "run_doctor", lambda: "doctor-called")
    code, out = run(capsys, "setup")
    assert code == expected
    assert calls[0][:3] == [sys.executable, "-m", "pip"]
    if pip_rc:
        assert "pip install failed" in out and "resolver exploded" in out


def test_setup_warns_but_continues_outside_a_venv(repo, monkeypatch, capsys):
    write(repo / "requirements.txt", "x\n")
    monkeypatch.setattr(cli, "in_virtualenv", lambda: False)
    code, out = run(capsys, "setup", "--dry-run")
    assert code == 0 and "virtual environment" in out


def test_doctor_command_returns_the_doctor_exit_code(repo, monkeypatch, capsys):
    monkeypatch.setattr(cli, "run_doctor", lambda: 2)
    assert cli.main(["doctor"]) == 2


# ---------------------------------------------------------------------------
# smoke / eval / export-chats / new-scenario wiring
# ---------------------------------------------------------------------------


def test_smoke_dry_run(repo, capsys):
    code, out = run(capsys, "smoke", "alpha", "--dry-run")
    assert code == 0 and "[p1] hi" in out


def test_smoke_unknown_prompt_id_exits_2(repo, capsys):
    code, out = run(capsys, "smoke", "alpha", "--only", "zzz", "--dry-run")
    assert code == 2 and "Unknown prompt id" in out


def test_smoke_rejects_a_standalone_agent(repo, capsys):
    code, out = run(capsys, "smoke", "hello_world", "--dry-run")
    assert code == 2 and "Unknown target" in out


def test_eval_without_eval_config_exits_2(repo, capsys):
    code, out = run(capsys, "eval", "alpha", "--dry-run")
    assert code == 2 and "eval_config.yaml not found" in out


def test_eval_dry_run(repo, capsys):
    write(repo / "evaluation/alpha/eval_config.yaml", "n_runs: 1\n")
    code, out = run(capsys, "eval", "alpha", "--dry-run")
    assert code == 0 and "evaluations evaluate --config evaluation/alpha/eval_config.yaml" in out


def test_eval_dry_run_standalone_agent(repo, capsys):
    write(repo / "standalone/hello-world/eval_config.yaml", "n_runs: 1\n")
    code, out = run(capsys, "eval", "hello_world", "--dry-run")
    assert code == 0
    assert "evaluations evaluate --config standalone/hello-world/eval_config.yaml" in out


def test_eval_standalone_agent_without_eval_config_exits_2(repo, capsys):
    code, out = run(capsys, "eval", "hello_world", "--dry-run")
    assert code == 2 and "eval_config.yaml not found" in out


def test_export_chats_dry_run_and_bad_window(repo, capsys):
    code, out = run(capsys, "export-chats", "--dry-run", "--last", "2d", "--agent", "translator")
    assert code == 0 and "would export chats of agent 'translator' (last 2d)" in out
    code, out = run(capsys, "export-chats", "--dry-run", "--last", "soon")
    assert code == 2 and "--last" in out


def test_export_chats_honours_output_dir(repo, capsys):
    target = repo / "elsewhere"
    code, out = run(capsys, "export-chats", "--dry-run", "--output-dir", str(target))
    assert code == 0 and str(target) in out and not target.exists()


def test_new_scenario_through_the_cli(repo, capsys):
    write(repo / scaffold.TEMPLATE, "# {{NAME}}\n")
    write(repo / scaffold.PRESENTATION, '<script src="scenarios/alpha.js"></script>\n')
    argv = ["new-scenario", "gamma", "--name", "Gamma", "--description", "d"]
    code, _ = run(capsys, *argv, "--dry-run")
    assert code == 0 and not (repo / "scenarios/gamma").exists()
    code, out = run(capsys, *argv)
    assert code == 0 and (repo / "scenarios/gamma/scenario.yaml").is_file()
    code, out = run(capsys, *argv)
    assert code == 2 and "already exists" in out


# ---------------------------------------------------------------------------
# main(): error to exit-code mapping
# ---------------------------------------------------------------------------


def force_command_error(monkeypatch, exc):
    """Make the `list` command raise `exc`, whatever main() does around it."""

    def boom(args):
        raise exc

    args = cli.build_parser().parse_args(["list"])
    args.func = boom
    monkeypatch.setattr(cli.argparse.ArgumentParser, "parse_args", lambda self, a=None: args)


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (cli.UsageError("bad usage"), 2),
        (cli.ManifestError("bad manifest"), 1),
        (cli.ExportError("api down"), 1),
        (cli.AdkError("cli broke", 1), 1),
        (cli.AdkError("cli missing", 127), 127),
        (KeyboardInterrupt(), 130),
        (RuntimeError("surprise"), 1),
    ],
)
def test_main_maps_errors_to_exit_codes(repo, monkeypatch, capsys, exc, code):
    force_command_error(monkeypatch, exc)
    assert cli.main(["list"]) == code


def test_unexpected_error_is_logged_with_a_traceback_not_shown(repo, monkeypatch, capsys):
    force_command_error(monkeypatch, RuntimeError("surprise"))
    assert cli.main(["list"]) == 1
    out = capsys.readouterr().out
    assert "Unexpected error: surprise" in out and "Traceback" not in out
    assert "Traceback" in (repo / "local" / "wxodemo.log").read_text(encoding="utf-8")


def test_verbose_flag_shows_debug_lines(repo, capsys):
    _, quiet = run(capsys, "list")
    _, loud = run(capsys, "-v", "list")
    assert "wxodemo 0." in loud and "wxodemo 0." not in quiet


# ---------------------------------------------------------------------------
# the real repo and the real launchers (no network, no env.cfg needed)
# ---------------------------------------------------------------------------


def launch(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REAL_ROOT / "wxodemo.py"), *argv],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REAL_ROOT,
        timeout=60,
        check=False,
    )


def test_launcher_runs_from_the_repo_root():
    proc = launch("list")
    assert proc.returncode == 0
    for name in ("incident-triage", "travel-request", "hello_world", "translator"):
        assert name in proc.stdout


def test_launcher_works_from_any_directory(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(REAL_ROOT / "wxodemo.py"), "--version"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout.startswith("wxodemo ")


def test_python_dash_m_entry_point():
    proc = subprocess.run(
        [sys.executable, "-m", "wxodemo", "--version"],
        capture_output=True,
        text=True,
        cwd=REAL_ROOT,
        env={**__import__("os").environ, "PYTHONPATH": str(REAL_ROOT / "src")},
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0 and "wxodemo" in proc.stdout


def test_real_repo_validates_and_dry_runs_cleanly():
    assert launch("validate").returncode == 0
    deploy_run = launch("deploy", "--all", "--dry-run")
    assert deploy_run.returncode == 0
    for command in ("tools import", "knowledge-bases import", "agents import", "agents deploy"):
        assert command in deploy_run.stdout
    undeploy_run = launch("undeploy", "--all", "--dry-run")
    assert undeploy_run.returncode == 0 and "agents remove" in undeploy_run.stdout


def test_real_repo_deploy_order_puts_scenarios_before_standalone():
    out = launch("deploy", "--all", "--dry-run").stdout
    assert out.index("(scenario)") < out.index("(standalone)")
    undeploy = launch("undeploy", "--all", "--dry-run").stdout
    assert undeploy.index("(standalone)") < undeploy.index("(scenario)")


def test_real_repo_smoke_dry_run_prints_every_prompt():
    proc = launch("smoke", "travel-request", "--dry-run")
    assert proc.returncode == 0 and "Dry run only" in proc.stdout

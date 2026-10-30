"""deploy / undeploy / status: action building and the safety rules, with orchestrate mocked."""

from pathlib import Path

import pytest

from helpers import FakeOrchestrate, make_scenario, make_standalone, make_tool_pkg
from wxodemo import deploy
from wxodemo.adk import AdkError
from wxodemo.config import Config, UsageError
from wxodemo.discovery import all_targets, resolve_targets
from wxodemo.logging_setup import setup_logging
from wxodemo.manifest import load_scenarios

CFG = Config(api_key="k-secret-1234", url="https://x/instances/1", env_name="demo")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    make_scenario(tmp_path, "alpha")
    make_standalone(tmp_path, "hello-world", "hello_world", tool="greeting")
    make_standalone(tmp_path, "plain", "plain_agent")
    return tmp_path


def targets_of(repo: Path, *names: str):
    targets, _ = all_targets(repo)
    return resolve_targets(targets, list(names), select_all=not names)


@pytest.fixture
def fake(monkeypatch, tmp_path, capsys):
    # capsys is requested first so the logger binds to the captured stdout.
    setup_logging(tmp_path / "test.log")  # commands report progress through the logger
    fake = FakeOrchestrate()
    monkeypatch.setattr(deploy, "run_orchestrate", fake)
    monkeypatch.setattr(deploy, "login", lambda cfg: None)
    return fake


# ---------------------------------------------------------------------------
# deploy
# ---------------------------------------------------------------------------


def test_scenario_deploy_order_and_promotion(repo, fake):
    deploy.run_deploy(targets_of(repo, "alpha"), CFG, repo, dry_run=False)
    kinds = [c.split(" ")[0:2] for c in fake.commands()]
    assert kinds == [
        ["tools", "import"],
        ["knowledge-bases", "import"],
        ["agents", "import"],
        ["agents", "deploy"],
    ]


def test_standalone_imports_tools_before_agent(repo, fake):
    deploy.run_deploy(targets_of(repo, "hello_world"), CFG, repo, dry_run=False)
    assert [c.split(" ")[0:2] for c in fake.commands()] == [
        ["tools", "import"],
        ["agents", "import"],
        ["agents", "deploy"],
    ]


def test_scenarios_deploy_before_standalone(repo, fake):
    deploy.run_deploy(targets_of(repo, "hello_world", "alpha"), CFG, repo, dry_run=False)
    first_agent = next(c for c in fake.commands() if c.startswith("agents import"))
    assert "agents" in first_agent and "alpha" in first_agent


def test_dry_run_runs_nothing_and_needs_no_config(repo, fake, capsys):
    assert deploy.run_deploy(targets_of(repo, "alpha"), None, repo, dry_run=True) == 0
    assert fake.calls == []


def test_deploy_stops_at_first_failure_and_names_the_step(repo, fake):
    fake.fail_on = ["knowledge-bases import"]
    with pytest.raises(AdkError, match="Knowledge base"):
        deploy.run_deploy(targets_of(repo, "alpha"), CFG, repo, dry_run=False)
    assert not any(c.startswith("agents") for c in fake.commands())


def test_promotion_failure_is_fatal(repo, fake):
    fake.fail_on = ["agents deploy"]
    with pytest.raises(AdkError, match="live"):
        deploy.run_deploy(targets_of(repo, "alpha"), CFG, repo, dry_run=False)


# ---------------------------------------------------------------------------
# undeploy
# ---------------------------------------------------------------------------


def alpha_existing():
    return {"agents": ["agent_alpha"], "tools": ["do_it"], "knowledge-bases": ["kb_alpha"]}


def test_undeploy_requires_tty_or_yes(repo, fake, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    with pytest.raises(UsageError, match="--yes"):
        deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, assume_yes=False)
    assert fake.calls == []


def test_undeploy_dry_run_needs_neither_tty_nor_yes(repo, fake, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)
    assert deploy.run_undeploy(targets_of(repo, "alpha"), None, repo, True, False) == 0
    assert fake.calls == []


def test_undeploy_with_yes_removes_in_dependency_order(repo, fake):
    fake.existing = alpha_existing()
    deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, assume_yes=True)
    assert fake.commands() == [
        "agents remove --name agent_alpha --kind native",
        "tools remove --name do_it",
        "knowledge-bases remove --name kb_alpha",
    ]


def test_undeploy_skips_what_is_already_gone(repo, fake):
    fake.existing = {"agents": [], "tools": ["do_it"], "knowledge-bases": []}
    deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, assume_yes=True)
    assert fake.commands() == ["tools remove --name do_it"]


def test_undeploy_nothing_present_is_success_without_prompt(repo, fake, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("must not prompt"))
    assert deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, True) == 0
    assert fake.commands() == []


@pytest.mark.parametrize(
    ("answer", "removed"), [("y", True), ("yes", True), ("n", False), ("", False)]
)
def test_undeploy_prompt_answers(repo, fake, monkeypatch, answer, removed):
    fake.existing = alpha_existing()
    monkeypatch.setattr("sys.stdin.isatty", lambda: True, raising=False)
    monkeypatch.setattr("builtins.input", lambda *_: answer)
    code = deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, assume_yes=False)
    assert bool(fake.commands()) is removed
    assert code == (0 if removed else 1)


def test_undeploy_stops_at_first_failure(repo, fake):
    fake.existing = alpha_existing()
    fake.fail_on = ["tools remove"]
    with pytest.raises(AdkError, match="Tool do_it"):
        deploy.run_undeploy(targets_of(repo, "alpha"), CFG, repo, False, assume_yes=True)
    assert not any(c.startswith("knowledge-bases") for c in fake.commands())


def test_standalone_goes_before_scenarios_on_undeploy(repo, fake):
    fake.existing = {
        "agents": ["agent_alpha", "hello_world"],
        "tools": ["do_it", "greeting"],
        "knowledge-bases": ["kb_alpha"],
    }
    deploy.run_undeploy(targets_of(repo, "alpha", "hello_world"), CFG, repo, False, True)
    cmds = fake.commands()
    assert cmds.index("agents remove --name hello_world --kind native") < cmds.index(
        "agents remove --name agent_alpha --kind native"
    )


# ---------------------------------------------------------------------------
# status and helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("existing", "state"),
    [
        (alpha_existing(), "deployed"),
        ({"agents": [], "tools": [], "knowledge-bases": []}, "not deployed"),
        ({"agents": ["agent_alpha"], "tools": [], "knowledge-bases": []}, "partial"),
    ],
)
def test_status_states(repo, fake, capsys, existing, state):
    fake.existing = existing
    deploy.run_status(targets_of(repo, "alpha"), CFG)
    assert state in capsys.readouterr().out


def test_json_parser_accepts_raw_newlines_in_strings():
    text = 'banner\n[{"name": "a", "description": "line one\nline two"}]'
    assert deploy._json_from(text, "kb")[0]["name"] == "a"


def test_json_parser_reports_garbage():
    with pytest.raises(AdkError):
        deploy._json_from("not json at all", "kb")


def test_tool_deploy_package_actions(repo, fake):
    make_tool_pkg(repo, "report_generator", tools=["gen_rep_1", "gen_rep_2"], reqs=True)
    deploy.run_deploy(targets_of(repo, "report_generator"), CFG, repo, dry_run=False)
    cmds = fake.commands()
    assert len(cmds) == 1
    assert "tools import -k python -p" in cmds[0]
    assert "report_generator" in cmds[0]
    assert "-r" in cmds[0]


def test_tool_undeploy_actions(repo, fake):
    make_tool_pkg(repo, "report_generator", tools=["gen_rep_1", "gen_rep_2"], reqs=True)
    fake.existing = {"agents": [], "tools": ["gen_rep_1", "gen_rep_2"], "knowledge-bases": []}
    deploy.run_undeploy(targets_of(repo, "report_generator"), CFG, repo, dry_run=False, assume_yes=True)
    cmds = fake.commands()
    assert "tools remove --name gen_rep_1" in cmds
    assert "tools remove --name gen_rep_2" in cmds


def test_tool_status_deployed_and_missing(repo, fake, capsys):
    make_tool_pkg(repo, "report_generator", tools=["gen_rep_1", "gen_rep_2"])
    fake.existing = {"agents": [], "tools": ["gen_rep_1", "gen_rep_2"], "knowledge-bases": []}
    deploy.run_status(targets_of(repo, "report_generator"), CFG)
    out = capsys.readouterr().out
    assert "deployed" in out

    fake.existing = {"agents": [], "tools": ["gen_rep_1"], "knowledge-bases": []}
    deploy.run_status(targets_of(repo, "report_generator"), CFG)
    out = capsys.readouterr().out
    assert "partial" in out
    assert "missing: tool gen_rep_2" in out


def test_every_scenario_action_is_an_orchestrate_call(repo):
    scenarios = load_scenarios(repo)
    actions = deploy.scenario_deploy_actions(scenarios["alpha"], scenarios)
    assert all(a.args[0] in {"tools", "knowledge-bases", "agents"} for a in actions)

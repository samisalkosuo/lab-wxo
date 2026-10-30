"""smoke (prompt loading, result extraction, run loop) and eval (command building)."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import make_scenario, make_standalone, write
from wxodemo import evaluate, smoke
from wxodemo.adk import AdkError
from wxodemo.config import Config, UsageError
from wxodemo.discovery import all_targets
from wxodemo.logging_setup import setup_logging
from wxodemo.manifest import ManifestError, load_scenarios

CFG = Config(api_key="k-secret-1234", url="https://x/instances/1", env_name="demo")


@pytest.fixture
def repo(tmp_path: Path, capsys) -> Path:
    setup_logging(tmp_path / "local" / "t.log")
    make_scenario(tmp_path, "alpha")
    return tmp_path


def scenario_of(repo: Path):
    return load_scenarios(repo)["alpha"]


def target_of(repo: Path, name: str = "alpha"):
    targets, _ = all_targets(repo)
    return next(t for t in targets if t.matches(name))


# ---------------------------------------------------------------------------
# smoke: loading
# ---------------------------------------------------------------------------


def test_load_plan(repo: Path):
    name, cases = smoke.load_smoke_plan(scenario_of(repo))
    assert name == "agent_alpha"
    assert cases == [smoke.SmokeCase("p1", "hi")]


def test_load_plan_uses_smoke_agent(repo: Path):
    manifest = repo / "scenarios/alpha/scenario.yaml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace("agents:\n", "smoke_agent: agent_second\nagents:\n  - name: agent_second\n"
                        "    path: agents/alpha\n    kind: native\n", 1)
    write(manifest, text)
    name, _ = smoke.load_smoke_plan(scenario_of(repo))
    assert name == "agent_second"


def test_load_plan_rejects_unknown_smoke_agent(repo: Path):
    manifest = repo / "scenarios/alpha/scenario.yaml"
    write(manifest, manifest.read_text(encoding="utf-8") + "smoke_agent: nope\n")
    with pytest.raises(ManifestError, match="smoke_agent"):
        smoke.load_smoke_plan(scenario_of(repo))


def test_load_plan_without_prompts(repo: Path):
    write(repo / "evaluation/alpha/ground_truth.json", json.dumps({"smoke_prompts": []}))
    with pytest.raises(ManifestError, match="smoke_prompts"):
        smoke.load_smoke_plan(scenario_of(repo))


def test_load_plan_invalid_json(repo: Path):
    write(repo / "evaluation/alpha/ground_truth.json", "{nope")
    with pytest.raises(ManifestError, match="not valid JSON"):
        smoke.load_smoke_plan(scenario_of(repo))


def test_load_plan_missing_ground_truth(repo: Path):
    (repo / "evaluation/alpha/ground_truth.json").unlink()
    with pytest.raises(ManifestError, match="ground_truth.json not found"):
        smoke.load_smoke_plan(scenario_of(repo))


def test_select_cases():
    cases = [smoke.SmokeCase("a", "1"), smoke.SmokeCase("b", "2")]
    assert smoke.select_cases(cases, []) == cases
    assert smoke.select_cases(cases, ["b"]) == [cases[1]]
    with pytest.raises(UsageError, match="Unknown prompt id"):
        smoke.select_cases(cases, ["zzz"])


def test_dry_run_sends_nothing(repo: Path, capsys):
    assert smoke.run_smoke(scenario_of(repo), None, [], True) == 0
    out = capsys.readouterr().out
    assert "[p1] hi" in out and "nothing was sent" in out


# ---------------------------------------------------------------------------
# smoke: extracting results
# ---------------------------------------------------------------------------


def test_extract_results_from_step_history_and_content_list():
    messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": [{"text": "first"}],
            "step_history": [
                {"step_details": [{"type": "tool_call", "name": "get_incident"}]},
                {"step_details": [{"type": "other", "name": "ignored"}]},
            ],
        },
        {"role": "assistant", "content": [{"text": "final"}, {"text": "answer"}]},
    ]
    assert smoke.extract_results(messages) == (["get_incident"], "final answer")


def test_extract_results_legacy_tool_messages_and_dict_wrapper():
    messages = {
        "messages": [
            {"role": "tool_call", "tool_name": "a", "content": []},
            {"role": "tool_calls", "content": [{"tool_name": "b"}, {"x": 1}]},
            {"role": "tool", "tool_name": "c"},
            {"role": "assistant", "content": "plain text"},
        ]
    }
    assert smoke.extract_results(messages) == (["a", "b", "c"], "plain text")


@pytest.mark.parametrize("empty", [None, [], {}, "garbage", 5])
def test_extract_results_tolerates_odd_input(empty):
    assert smoke.extract_results(empty) == ([], "")


def test_extract_results_accepts_objects():
    msg = SimpleNamespace(role="assistant", content="obj answer", tool_name="", step_history=None)
    assert smoke.extract_results([msg]) == ([], "obj answer")


# ---------------------------------------------------------------------------
# smoke: the run loop, with the ADK clients faked
# ---------------------------------------------------------------------------


class FakeRunClient:
    def __init__(self, status="completed", fail_create=False):
        self.status, self.fail_create, self.sent = status, fail_create, []

    def create_run(self, message, agent_id):
        if self.fail_create:
            raise RuntimeError("no capacity")
        self.sent.append((message, agent_id))
        return {"run_id": "r1", "thread_id": "t1"}

    def wait_for_run_completion(self, run_id, poll_interval, max_retries):
        return {"status": self.status}


class FakeThreads:
    def get_thread_messages(self, thread_id):
        return [{"role": "assistant", "content": "done"}]


def test_run_case_success():
    case = smoke.SmokeCase("p1", "hi")
    result = smoke._run_case(FakeRunClient(), FakeThreads(), "agent-id", case)
    assert result.passed and result.answer == "done" and result.thread_id == "t1"


def test_run_case_failed_status_is_not_a_pass():
    result = smoke._run_case(FakeRunClient("failed"), FakeThreads(), "a", smoke.SmokeCase("p", "x"))
    assert not result.passed


def test_run_case_create_error_is_reported_not_raised():
    result = smoke._run_case(
        FakeRunClient(fail_create=True), FakeThreads(), "a", smoke.SmokeCase("p", "x")
    )
    assert not result.passed and "no capacity" in result.status


def test_run_case_timeout():
    class Slow(FakeRunClient):
        def wait_for_run_completion(self, **_):
            raise TimeoutError

    result = smoke._run_case(Slow(), FakeThreads(), "a", smoke.SmokeCase("p", "x"))
    assert result.status == "timeout"


# ---------------------------------------------------------------------------
# eval
# ---------------------------------------------------------------------------


def test_eval_requires_config_file(repo: Path):
    with pytest.raises(UsageError, match="eval_config.yaml not found"):
        evaluate.run_eval(repo, target_of(repo), CFG, dry_run=True)


def test_eval_dry_run_shows_command(repo: Path, capsys):
    write(repo / "evaluation/alpha/eval_config.yaml", "n_runs: 1\n")
    assert evaluate.run_eval(repo, target_of(repo), None, dry_run=True) == 0
    out = capsys.readouterr().out
    assert "orchestrate evaluations evaluate --config evaluation/alpha/eval_config.yaml" in out


def test_eval_runs_attached_to_terminal_and_reports_failure(repo: Path, monkeypatch):
    write(repo / "evaluation/alpha/eval_config.yaml", "n_runs: 1\n")
    seen = {}
    monkeypatch.setattr(evaluate, "find_orchestrate", lambda: Path("orchestrate"))
    monkeypatch.setattr(evaluate, "login", lambda cfg: seen.setdefault("login", cfg))

    def fake_run(command, **kwargs):
        seen["command"], seen["kwargs"] = command, kwargs
        return SimpleNamespace(returncode=seen.get("rc", 0))

    monkeypatch.setattr(evaluate.subprocess, "run", fake_run)

    assert evaluate.run_eval(repo, target_of(repo), CFG, dry_run=False) == 0
    assert seen["login"] is CFG
    assert seen["command"][1:] == [
        "evaluations",
        "evaluate",
        "--config",
        "evaluation/alpha/eval_config.yaml",
    ]
    assert "capture_output" not in seen["kwargs"], "output must reach the terminal, not a pipe"
    assert seen["kwargs"]["cwd"] == repo

    seen["rc"] = 3
    with pytest.raises(AdkError) as info:
        evaluate.run_eval(repo, target_of(repo), CFG, dry_run=False)
    assert info.value.returncode == 3


def test_eval_without_cli(repo: Path, monkeypatch):
    write(repo / "evaluation/alpha/eval_config.yaml", "n_runs: 1\n")
    monkeypatch.setattr(evaluate, "find_orchestrate", lambda: None)
    with pytest.raises(AdkError, match="not found"):
        evaluate.run_eval(repo, target_of(repo), CFG, dry_run=False)

def test_eval_standalone_agent_dry_run(repo: Path, capsys):
    make_standalone(repo, "echo-agent", "echo_agent")
    write(repo / "standalone/echo-agent/eval_config.yaml", "n_runs: 1\n")
    assert evaluate.run_eval(repo, target_of(repo, "echo_agent"), None, dry_run=True) == 0
    out = capsys.readouterr().out
    assert "Evaluating 'echo_agent'" in out
    assert "orchestrate evaluations evaluate --config standalone/echo-agent/eval_config.yaml" in out


def test_eval_standalone_agent_requires_config_file(repo: Path):
    make_standalone(repo, "echo-agent", "echo_agent")
    with pytest.raises(UsageError, match="standalone/echo-agent/eval_config.yaml not found"):
        evaluate.run_eval(repo, target_of(repo, "echo_agent"), None, dry_run=True)

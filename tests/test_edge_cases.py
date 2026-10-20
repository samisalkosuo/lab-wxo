"""Edge cases found by coverage and by real runs: HTTP retries, smoke's live path, deploy steps."""

import http.client
import io
import json
import urllib.error
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import FakeOrchestrate, make_scenario, make_standalone, write
from wxodemo import chats, deploy, smoke
from wxodemo.adk import AdkError
from wxodemo.config import Config, UsageError
from wxodemo.discovery import all_targets, resolve_targets
from wxodemo.logging_setup import setup_logging
from wxodemo.manifest import DeployStep, load_scenarios

CFG = Config(api_key="k-secret-1234", url="https://x/instances/1", env_name="demo")


@pytest.fixture(autouse=True)
def logging_ready(tmp_path: Path, capsys):
    setup_logging(tmp_path / "local" / "t.log")


# ---------------------------------------------------------------------------
# Api.request: retries (a cut-off chunked body broke a real export once)
# ---------------------------------------------------------------------------


class Response:
    def __init__(self, body: bytes | Exception):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        if isinstance(self.body, Exception):
            raise self.body
        return self.body


def http_error(code: int, body: bytes = b"detail") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "msg", {}, io.BytesIO(body))


@pytest.fixture
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(chats.time, "sleep", sleeps.append)
    return sleeps


def script_urlopen(monkeypatch, outcomes):
    """urlopen returns / raises the given outcomes in order."""
    calls = []

    def fake(request, timeout):
        calls.append(request)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(chats.urllib.request, "urlopen", fake)
    return calls


def test_request_retries_a_truncated_chunked_response(monkeypatch, no_sleep):
    calls = script_urlopen(
        monkeypatch,
        [Response(http.client.IncompleteRead(b"partial")), Response(b'{"ok": true}')],
    )
    assert chats.Api("tok").request("http://x") == {"ok": True}
    assert len(calls) == 2 and no_sleep == [1]


def test_request_retries_rate_limits_then_succeeds(monkeypatch, no_sleep):
    calls = script_urlopen(monkeypatch, [http_error(429), http_error(429), Response(b"[1]")])
    assert chats.Api("tok").request("http://x") == [1]
    assert len(calls) == 3 and no_sleep == [2, 4]


def test_request_gives_up_after_the_last_rate_limit(monkeypatch, no_sleep):
    script_urlopen(monkeypatch, [http_error(429)] * 3)
    with pytest.raises(chats.ExportError, match="HTTP 429"):
        chats.Api("tok").request("http://x")


def test_request_does_not_retry_client_errors(monkeypatch, no_sleep):
    calls = script_urlopen(monkeypatch, [http_error(404, b"missing")])
    with pytest.raises(chats.ExportError, match="HTTP 404.*missing"):
        chats.Api("tok").request("http://x")
    assert len(calls) == 1 and no_sleep == []


def test_request_reports_the_last_error_after_all_attempts(monkeypatch, no_sleep):
    script_urlopen(monkeypatch, [urllib.error.URLError("dns")] * 3)
    with pytest.raises(chats.ExportError, match="failed after 3 attempts.*dns"):
        chats.Api("tok").request("http://x")
    assert no_sleep == [1, 2]


def test_request_empty_body_is_an_empty_dict_and_sends_auth(monkeypatch):
    calls = script_urlopen(monkeypatch, [Response(b"")])
    assert chats.Api("tok-9").request("http://x") == {}
    assert calls[0].get_header("Authorization") == "Bearer tok-9"


def test_request_sends_a_json_body(monkeypatch):
    calls = script_urlopen(monkeypatch, [Response(b"{}")])
    chats.Api("t").request("http://x", method="POST", body={"a": 1})
    assert calls[0].data == b'{"a": 1}' and calls[0].get_method() == "POST"


@pytest.mark.parametrize(
    ("env_type", "host"), [("ibm_iam", "iam.cloud.ibm.com"), ("mcsp", "iam.platform.saas.ibm.com")]
)
def test_token_url_depends_on_env_type(monkeypatch, env_type, host):
    calls = script_urlopen(monkeypatch, [Response(b'{"access_token": "abc-token"}')])
    cfg = Config("k-secret-1234", "https://x", "demo", env_type)
    assert chats.get_token(cfg) == "abc-token"
    assert host in calls[0].full_url
    assert b"k-secret-1234" in calls[0].data, "the key is sent to IAM, and only there"


def test_token_without_access_token_is_an_error(monkeypatch):
    script_urlopen(monkeypatch, [Response(b"{}")])
    with pytest.raises(chats.ExportError, match="access_token"):
        chats.get_token(CFG)


# ---------------------------------------------------------------------------
# smoke: the live path with the ADK clients faked
# ---------------------------------------------------------------------------


class FakeRunClient:
    def __init__(self, statuses):
        self.statuses = list(statuses)
        self.sent = []

    def create_run(self, message, agent_id):
        self.sent.append(message)
        return {"run_id": f"r{len(self.sent)}", "thread_id": f"t{len(self.sent)}"}

    def wait_for_run_completion(self, run_id, poll_interval, max_retries):
        return {"status": self.statuses.pop(0)}


class FakeThreads:
    def get_thread_messages(self, thread_id):
        return [
            {
                "role": "assistant",
                "content": "answer " + thread_id,
                "step_history": [{"step_details": [{"type": "tool_call", "name": "get_it"}]}],
            }
        ]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    make_scenario(tmp_path, "alpha")
    write(
        tmp_path / "evaluation/alpha/ground_truth.json",
        json.dumps({"smoke_prompts": [{"id": "a", "prompt": "one"}, {"id": "b", "prompt": "two"}]}),
    )
    return tmp_path


def live_smoke(monkeypatch, repo, statuses, agent_lookup=lambda name: "agent-id-1"):
    pytest.importorskip("ibm_watsonx_orchestrate")
    runs = FakeRunClient(statuses)
    logins = []
    monkeypatch.setattr(smoke, "login", logins.append)
    monkeypatch.setattr(smoke, "_find_agent_id", agent_lookup)

    def fake_instantiate(cls):
        return runs if cls.__name__ == "RunClient" else FakeThreads()

    monkeypatch.setattr("ibm_watsonx_orchestrate.client.utils.instantiate_client", fake_instantiate)
    scenario = load_scenarios(repo)["alpha"]
    return smoke.run_smoke(scenario, CFG, [], False), runs, logins


def test_live_smoke_all_completed(monkeypatch, repo, capsys):
    code, runs, logins = live_smoke(monkeypatch, repo, ["completed", "COMPLETED"])
    out = capsys.readouterr().out
    assert code == 0 and runs.sent == ["one", "two"] and logins == [CFG]
    assert "Agent id: agent-id-1" in out and "get_it" in out and "answer t1" in out
    assert "All 2 prompt(s) completed" in out


def test_live_smoke_one_failure_exits_1_and_still_runs_the_rest(monkeypatch, repo, capsys):
    code, runs, _ = live_smoke(monkeypatch, repo, ["failed", "completed"])
    out = capsys.readouterr().out
    assert code == 1 and runs.sent == ["one", "two"]
    assert "1 of 2 prompt(s) did not complete: a" in out


def test_live_smoke_stops_when_the_agent_is_not_deployed(monkeypatch, repo):
    def missing(name):
        raise AdkError(f"No agent named '{name}'")

    with pytest.raises(AdkError, match="No agent named 'agent_alpha'"):
        live_smoke(monkeypatch, repo, [], missing)


def test_smoke_dry_run_with_only_filter(repo, capsys):
    scenario = load_scenarios(repo)["alpha"]
    assert smoke.run_smoke(scenario, None, ["b"], True) == 0
    out = capsys.readouterr().out
    assert "[b] two" in out and "[a]" not in out and "1 prompt(s)" in out


def test_find_agent_id_outcomes(monkeypatch):
    pytest.importorskip("ibm_watsonx_orchestrate")
    answers = {
        "none": [],
        "two": [{"id": "1"}, {"id": "2"}],
        "noid": [{"name": "x"}],
        "ok": [{"id": "z"}],
    }

    class FakeAgents:
        def __init__(self, key):
            self.key = key

        def get_draft_by_name(self, name):
            return answers[self.key]

    for key, expected in (
        ("none", "No agent named"),
        ("two", "2 agents named"),
        ("noid", "without an 'id'"),
    ):
        monkeypatch.setattr(
            "ibm_watsonx_orchestrate.client.utils.instantiate_client",
            lambda cls, k=key: FakeAgents(k),
        )
        with pytest.raises(AdkError, match=expected):
            smoke._find_agent_id("agent_x")
    monkeypatch.setattr(
        "ibm_watsonx_orchestrate.client.utils.instantiate_client", lambda cls: FakeAgents("ok")
    )
    assert smoke._find_agent_id("agent_x") == "z"


def test_run_case_without_run_id_and_with_unreadable_thread():
    class NoRun(FakeRunClient):
        def create_run(self, message, agent_id):
            return {"thread_id": "t"}

    result = smoke._run_case(NoRun([]), FakeThreads(), "a", smoke.SmokeCase("p", "x"))
    assert result.status.startswith("no_run_id") and not result.passed

    class BrokenThreads:
        def get_thread_messages(self, thread_id):
            raise RuntimeError("gone")

    ok_run = smoke._run_case(
        FakeRunClient(["completed"]), BrokenThreads(), "a", smoke.SmokeCase("p", "x")
    )
    assert ok_run.passed and ok_run.answer == "" and ok_run.tools == []


def test_run_case_poll_error_is_reported():
    class Flaky(FakeRunClient):
        def wait_for_run_completion(self, **_):
            raise RuntimeError("socket closed")

    result = smoke._run_case(Flaky([]), FakeThreads(), "a", smoke.SmokeCase("p", "x"))
    assert result.status == "poll_error: socket closed" and not result.passed


def test_run_case_accepts_objects_instead_of_dicts():
    class ObjRun(FakeRunClient):
        def create_run(self, message, agent_id):
            return SimpleNamespace(run_id="r", thread_id="t")

        def wait_for_run_completion(self, **_):
            return "completed"  # some client versions return a bare status string

    assert smoke._run_case(ObjRun([]), FakeThreads(), "a", smoke.SmokeCase("p", "x")).passed


# ---------------------------------------------------------------------------
# deploy: step kinds and the standalone knowledge-base warning
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("step", "expected"),
    [
        (DeployStep("tool_py", Path("t.py")), ["tools", "import", "-k", "python", "-f", "t.py"]),
        (
            DeployStep("tool_openapi", Path("a.yaml")),
            ["tools", "import", "-k", "openapi", "-f", "a.yaml"],
        ),
        (DeployStep("kb", Path("kb.yaml")), ["knowledge-bases", "import", "-f", "kb.yaml"]),
        (DeployStep("flow", Path("f.py")), ["tools", "import", "-k", "flow", "-f", "f.py"]),
    ],
)
def test_each_deploy_step_kind_builds_one_orchestrate_call(step, expected):
    (action,) = deploy._step_actions(step)
    assert action.args == expected


def test_tool_package_step_passes_entry_and_requirements():
    entry, reqs = Path("p") / "e.py", Path("p") / "r.txt"
    step = DeployStep("tool_pkg", Path("p"), entry=entry, requirements=reqs)
    (action,) = deploy._step_actions(step)
    assert action.args == [
        "tools",
        "import",
        "-k",
        "python",
        "-p",
        "p",
        "-f",
        str(entry),
        "-r",
        str(reqs),
    ]


def test_unknown_step_kind_is_a_programming_error():
    with pytest.raises(ValueError, match="unknown deploy step kind"):
        deploy._step_actions(DeployStep("mystery", Path("x")))


def test_connections_are_imported_before_scenarios(tmp_path, monkeypatch):
    make_scenario(tmp_path, "alpha")
    write(tmp_path / "connections" / "b.yaml", "x")
    write(tmp_path / "connections" / "a.yaml", "x")
    fake = FakeOrchestrate()
    monkeypatch.setattr(deploy, "run_orchestrate", fake)
    monkeypatch.setattr(deploy, "login", lambda cfg: None)
    targets, _ = all_targets(tmp_path)
    deploy.run_deploy(resolve_targets(targets, ["alpha"]), CFG, tmp_path, dry_run=False)
    cmds = fake.commands()
    assert [c.split("\\")[-1].split("/")[-1] for c in cmds[:2]] == ["a.yaml", "b.yaml"]
    assert cmds[0].startswith("connections import") and cmds[2].startswith("tools import")


def test_standalone_warns_when_its_knowledge_base_is_missing(tmp_path, monkeypatch, capsys):
    make_standalone(tmp_path, "qa", "qa_agent")
    write(tmp_path / "standalone/qa/agent.yaml", "name: qa_agent\nknowledge_base: [docs_kb]\n")
    fake = FakeOrchestrate()
    monkeypatch.setattr(deploy, "run_orchestrate", fake)
    monkeypatch.setattr(deploy, "login", lambda cfg: None)
    targets, _ = all_targets(tmp_path)
    assert deploy.run_deploy(resolve_targets(targets, ["qa_agent"]), CFG, tmp_path, False) == 0
    out = capsys.readouterr().out
    assert "Knowledge base(s) not found: docs_kb" in out

    fake.existing["knowledge-bases"] = ["docs_kb"]
    deploy.run_deploy(resolve_targets(targets, ["qa_agent"]), CFG, tmp_path, False)
    assert "not found: docs_kb" not in capsys.readouterr().out


def test_deploy_all_with_only_soon_scenarios_is_a_usage_error(tmp_path):
    make_scenario(tmp_path, "beta", status="soon")
    targets, _ = all_targets(tmp_path)
    with pytest.raises(UsageError, match="No targets"):
        resolve_targets(targets, [], select_all=True, kind="scenario", live_only=True)

"""Smoke test: send a scenario's prompts to its deployed agent through the ADK run API.

Per prompt: look the agent up BY NAME in the active environment, create a run, poll until it
finishes, then report the tools that were called and the start of the final answer. It does not
judge whether the answer is right; compare with ground_truth.json yourself. It sends real
prompts, so each run uses LLM capacity.

Prompts come from `smoke_prompts` in <evaluation.path>/ground_truth.json, a list of
{"id": "...", "prompt": "..."}. Use diagnosis-only prompts: an approval form (human in the loop)
cannot be answered through the run API.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from wxodemo.adk import AdkError, login
from wxodemo.config import Config, UsageError
from wxodemo.logging_setup import fail, get_logger, ok, plain
from wxodemo.manifest import ManifestError, Scenario

MAX_RETRIES = 36  # 36 x 5 s = 3 min per prompt
POLL_SECONDS = 5
ANSWER_CHARS = 600


@dataclass(frozen=True)
class SmokeCase:
    id: str
    prompt: str


@dataclass
class CaseResult:
    id: str
    status: str
    thread_id: str | None = None
    tools: list[str] = field(default_factory=list)
    answer: str = ""

    @property
    def passed(self) -> bool:
        return self.status.lower() == "completed"


def load_smoke_plan(scenario: Scenario) -> tuple[str, list[SmokeCase]]:
    """(agent name, cases) from the manifest and ground_truth.json."""
    agents = scenario.get("agents") or []
    if not agents:
        raise ManifestError(f"scenario '{scenario.id}' has no agents in its manifest")
    evaluation = (scenario.get("evaluation") or {}).get("path")
    if not evaluation:
        raise ManifestError(f"scenario '{scenario.id}' has no evaluation.path in its manifest")
    truth = scenario.root / evaluation / "ground_truth.json"
    if not truth.is_file():
        raise ManifestError(f"{evaluation}/ground_truth.json not found")
    try:
        data = json.loads(truth.read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise ManifestError(f"{evaluation}/ground_truth.json is not valid JSON: {exc}") from exc
    cases = [SmokeCase(p["id"], p["prompt"]) for p in data.get("smoke_prompts") or []]
    if not cases:
        raise ManifestError(
            f"{evaluation}/ground_truth.json has no 'smoke_prompts' (a list of {{id, prompt}})"
        )
    return agents[0]["name"], cases


def select_cases(cases: list[SmokeCase], only: list[str]) -> list[SmokeCase]:
    if not only:
        return cases
    known = [c.id for c in cases]
    unknown = sorted(set(only) - set(known))
    if unknown:
        raise UsageError(f"Unknown prompt id(s) {unknown}. Known: {known}")
    return [c for c in cases if c.id in only]


def _field(item: Any, name: str, default: Any = "") -> Any:
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def extract_results(messages: Any) -> tuple[list[str], str]:
    """(tool names, last assistant text) from the messages of a thread."""
    tools: list[str] = []
    last_assistant = ""
    if isinstance(messages, dict):
        messages = messages.get("messages", [])
    if not isinstance(messages, list):
        return tools, last_assistant

    for msg in messages:
        role = _field(msg, "role")
        content = _field(msg, "content", [])
        tool_name = _field(msg, "tool_name")

        if role in ("tool_call", "tool_calls"):
            if tool_name:
                tools.append(tool_name)
            elif isinstance(content, list):
                tools += [
                    item["tool_name"]
                    for item in content
                    if isinstance(item, dict) and item.get("tool_name")
                ]
        elif role == "tool" and tool_name:
            tools.append(tool_name)

        # Current ADK thread messages record tool calls inside step_history.
        for step in _field(msg, "step_history", None) or []:
            for detail in step.get("step_details", []) if isinstance(step, dict) else []:
                if (
                    isinstance(detail, dict)
                    and detail.get("type") == "tool_call"
                    and detail.get("name")
                ):
                    tools.append(detail["name"])

        if role == "assistant":
            if isinstance(content, str):
                last_assistant = content
            elif isinstance(content, list):
                parts = [
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                ]
                last_assistant = " ".join(parts).strip()
            elif content:
                last_assistant = str(content)

    return tools, last_assistant


def _find_agent_id(agent_name: str) -> str:
    from ibm_watsonx_orchestrate.client.agents.agent_client import AgentClient
    from ibm_watsonx_orchestrate.client.utils import instantiate_client

    found = instantiate_client(AgentClient).get_draft_by_name(agent_name)
    if not found:
        raise AdkError(
            f"No agent named '{agent_name}' in the active environment. "
            f"Deploy it first: python wxodemo.py deploy <scenario>"
        )
    if len(found) > 1:
        raise AdkError(f"{len(found)} agents named '{agent_name}' found; cannot choose one.")
    agent_id = found[0].get("id")
    if not agent_id:
        raise AdkError(f"Agent '{agent_name}' came back without an 'id' field: {sorted(found[0])}")
    return agent_id


def _run_case(run_client: Any, thread_client: Any, agent_id: str, case: SmokeCase) -> CaseResult:
    log = get_logger()
    plain(f"[{case.id}] {case.prompt}")

    try:
        response = run_client.create_run(message=case.prompt, agent_id=agent_id)
    except Exception as exc:  # noqa: BLE001 - the client raises many different error types
        log.debug("create_run failed", exc_info=True)
        return CaseResult(case.id, f"create_error: {exc}")

    run_id = _field(response, "run_id", None)
    thread_id = _field(response, "thread_id", None)
    log.debug("run_id=%s thread_id=%s", run_id, thread_id)
    if not run_id:
        return CaseResult(case.id, f"no_run_id: {response}")

    try:
        final = run_client.wait_for_run_completion(
            run_id=run_id, poll_interval=POLL_SECONDS, max_retries=MAX_RETRIES
        )
        status = final.get("status", str(final)) if isinstance(final, dict) else str(final)
    except TimeoutError:
        status = "timeout"
    except Exception as exc:  # noqa: BLE001
        log.debug("polling failed", exc_info=True)
        status = f"poll_error: {exc}"

    messages: Any = []
    if thread_id:
        try:
            messages = thread_client.get_thread_messages(thread_id)
        except Exception as exc:  # noqa: BLE001
            log.debug("get_thread_messages failed", exc_info=True)
            log.warning("could not read messages for %s: %s", case.id, exc)

    tools, answer = extract_results(messages)
    log.debug("[%s] status=%s tools=%s\nanswer:\n%s", case.id, status, tools, answer)
    return CaseResult(case.id, status, thread_id, tools, answer)


def _report(result: CaseResult) -> None:
    line = f"[{result.id}] {result.status}"
    (ok if result.passed else fail)(line)
    plain(f"    tools : {result.tools or '(none found in messages)'}")
    shown = " ".join(result.answer[:ANSWER_CHARS].split())
    plain(f"    answer: {shown}")


def run_smoke(scenario: Scenario, cfg: Config | None, only: list[str], dry_run: bool) -> int:
    """Send the scenario's smoke prompts to its agent. 0 if every run completed, else 1."""
    agent_name, cases = load_smoke_plan(scenario)
    cases = select_cases(cases, only)

    plain(f"Smoke test: {scenario.id} (agent '{agent_name}', {len(cases)} prompt(s))")
    if dry_run:
        for case in cases:
            plain(f"  [{case.id}] {case.prompt}")
        plain("Dry run only: nothing was sent.")
        return 0

    try:
        from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
        from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient
        from ibm_watsonx_orchestrate.client.utils import instantiate_client
    except ImportError as exc:
        raise UsageError(
            "The ibm-watsonx-orchestrate package is not installed for this Python. "
            "Run: python wxodemo.py setup"
        ) from exc

    login(cfg)  # refreshes the 2-hour token; safe to repeat
    agent_id = _find_agent_id(agent_name)
    plain(f"Agent id: {agent_id}")
    run_client = instantiate_client(RunClient)
    thread_client = instantiate_client(ThreadsClient)

    results = []
    for case in cases:
        result = _run_case(run_client, thread_client, agent_id, case)
        _report(result)
        results.append(result)

    bad = [r.id for r in results if not r.passed]
    if bad:
        fail(f"{len(bad)} of {len(results)} prompt(s) did not complete: {', '.join(bad)}")
        return 1
    ok(f"All {len(results)} prompt(s) completed. Compare the answers with ground_truth.json.")
    return 0

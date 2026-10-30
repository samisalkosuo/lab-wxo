"""deploy, undeploy and status for scenarios and standalone agents.

A deploy or undeploy is first turned into a list of `Action`s (pure, easy to test), then run.
Anything that fails stops the run at once with the failing step named, including promoting an
agent to LIVE.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from wxodemo.adk import AdkError, login, run_orchestrate
from wxodemo.config import Config, UsageError
from wxodemo.discovery import StandaloneAgent, Target, ToolTarget
from wxodemo.logging_setup import info, ok, plain, warn
from wxodemo.manifest import DeployStep, Scenario, deploy_plan, load_scenarios, teardown_plan


@dataclass(frozen=True)
class Action:
    """One orchestrate command."""

    label: str  # shown to the user
    args: list[str]
    resource: tuple[str, str] | None = None  # (agent|tool|kb, name) for removals


@dataclass(frozen=True)
class Snapshot:
    """Names of what exists in the active WXO environment."""

    agents: frozenset[str]
    tools: frozenset[str]  # python tools and flows
    kbs: frozenset[str]

    def has(self, kind: str, name: str) -> bool:
        return name in {"agent": self.agents, "tool": self.tools, "kb": self.kbs}[kind]


@dataclass(frozen=True)
class Expected:
    """Names a target owns (what `deploy` creates)."""

    agents: list[str]
    tools: list[str]  # python tools and flows
    kbs: list[str]


# ---------------------------------------------------------------------------
# Building actions
# ---------------------------------------------------------------------------


def _step_actions(step: DeployStep) -> list[Action]:
    path, name = str(step.path), step.path.name
    if step.kind == "tool_py":
        return [Action(f"Tool {name}", ["tools", "import", "-k", "python", "-f", path])]
    if step.kind == "tool_openapi":
        return [Action(f"OpenAPI tool {name}", ["tools", "import", "-k", "openapi", "-f", path])]
    if step.kind == "tool_pkg":
        args = ["tools", "import", "-k", "python", "-p", path]
        args += ["-f", str(step.entry), "-r", str(step.requirements)]
        return [Action(f"Tool package {name}", args)]
    if step.kind == "kb":
        return [Action(f"Knowledge base {name}", ["knowledge-bases", "import", "-f", path])]
    if step.kind == "flow":
        return [Action(f"Flow {name}", ["tools", "import", "-k", "flow", "-f", path])]
    if step.kind == "agent":
        return _agent_actions(step.name or name, step.path)
    raise ValueError(f"unknown deploy step kind '{step.kind}'")


def _agent_actions(name: str, yaml_path: Path) -> list[Action]:
    return [
        Action(f"Agent {name}", ["agents", "import", "-f", str(yaml_path)]),
        # 'agents import' creates a DRAFT; the chat UI lists only LIVE agents.
        Action(f"Agent {name} live", ["agents", "deploy", "--name", name]),
    ]


def connection_actions(root: Path) -> list[Action]:
    folder = root / "connections"
    files = sorted(folder.rglob("*.yaml")) if folder.is_dir() else []
    return [Action(f"Connection {f.name}", ["connections", "import", "-f", str(f)]) for f in files]


def scenario_deploy_actions(scenario: Scenario, everything: dict[str, Scenario]) -> list[Action]:
    actions: list[Action] = []
    for step in deploy_plan(everything, [scenario]):
        actions += _step_actions(step)
    return actions


def tool_deploy_actions(tool: ToolTarget) -> list[Action]:
    """Import a tool package or single-file tool."""
    if tool.is_package:
        args = ["tools", "import", "-k", "python", "-p", str(tool.path), "-f", str(tool.entry)]
        if tool.requirements:
            args += ["-r", str(tool.requirements)]
        return [Action(f"Tool package {tool.name}", args)]
    return [Action(f"Tool {tool.name}", ["tools", "import", "-k", "python", "-f", str(tool.path)])]


def tool_remove_actions(tool: ToolTarget) -> list[Action]:
    """Remove all @tool functions owned by a tool target."""
    actions: list[Action] = []
    for name in tool.names:
        actions.append(
            Action(f"Tool {name}", ["tools", "remove", "--name", name], resource=("tool", name))
        )
    return actions


def standalone_deploy_actions(agent: StandaloneAgent) -> list[Action]:
    """Tools first (the agent references them), then the agent. KBs are not managed here."""
    actions = [
        Action(f"Tool {t.path.name}", ["tools", "import", "-k", "python", "-f", str(t.path)])
        for t in agent.tools
    ]
    return actions + _agent_actions(agent.name, agent.yaml_path)


def scenario_remove_actions(scenario: Scenario) -> list[Action]:
    actions: list[Action] = []
    for step in teardown_plan([scenario]):
        if step.kind == "agent":
            args = ["agents", "remove", "--name", step.name, "--kind", step.agent_kind]
            actions.append(Action(f"Agent {step.name}", args, resource=("agent", step.name)))
        elif step.kind in ("flow", "tool"):
            label = f"{'Flow' if step.kind == 'flow' else 'Tool'} {step.name}"
            args = ["tools", "remove", "--name", step.name]
            actions.append(Action(label, args, resource=("tool", step.name)))
        else:
            args = ["knowledge-bases", "remove", "--name", step.name]
            actions.append(Action(f"Knowledge base {step.name}", args, resource=("kb", step.name)))
    return actions


def standalone_remove_actions(agent: StandaloneAgent) -> list[Action]:
    actions = [
        Action(
            f"Agent {agent.name}",
            ["agents", "remove", "--name", agent.name, "--kind", agent.kind],
            resource=("agent", agent.name),
        )
    ]
    for tool_file in agent.tools:
        for name in tool_file.names:
            actions.append(
                Action(f"Tool {name}", ["tools", "remove", "--name", name], resource=("tool", name))
            )
    return actions


def expected_resources(target: Target) -> Expected:
    if target.scenario is not None:
        s = target.scenario
        return Expected(
            agents=[a["name"] for a in s.get("agents") or []],
            tools=[n for t in s.get("tools") or [] for n in t.get("names") or []]
            + [f["name"] for f in s.get("flows") or []],
            kbs=[k["name"] for k in s.get("knowledge_bases") or []],
        )
    if target.agent is not None:
        agent = target.agent
        return Expected(agents=[agent.name], tools=[n for t in agent.tools for n in t.names], kbs=[])
    if target.tool is not None:
        return Expected(agents=[], tools=list(target.tool.names), kbs=[])
    return Expected(agents=[], tools=[], kbs=[])


def target_test_cases(root: Path, target: Target) -> list[Path]:
    """Find test case files for a scenario or standalone agent."""
    if target.scenario is not None:
        ev = target.scenario.get("evaluation")
        if ev and ev.get("path"):
            tc_dir = root / ev["path"] / "test_cases"
            if tc_dir.is_dir():
                return sorted(tc_dir.glob("*.json"))
    elif target.agent is not None:
        tc_dir = target.agent.dir / "test_cases"
        if tc_dir.is_dir():
            return sorted(tc_dir.glob("*.json"))
    return []


def _scenarios_first(targets: list[Target]) -> list[Target]:
    """Tools first, then scenarios (own KBs), then standalone agents."""
    kind_order = {"tool": 0, "scenario": 1, "standalone": 2}
    return sorted(targets, key=lambda t: kind_order.get(t.kind, 99))


# ---------------------------------------------------------------------------
# Talking to WXO
# ---------------------------------------------------------------------------


def _json_from(text: str, what: str) -> Any:
    """Parse JSON output, tolerating banner text before the first bracket.

    strict=False because the CLI wraps long descriptions with raw newlines inside strings
    (knowledge-bases list --verbose), which strict JSON rejects.
    """
    starts = [i for i in (text.find("["), text.find("{")) if i >= 0]
    try:
        return json.loads(text[min(starts) :] if starts else text, strict=False)
    except ValueError as exc:
        raise AdkError(f"Could not read the {what} list from orchestrate (see the log).") from exc


def _names(args: list[str], what: str) -> frozenset[str]:
    data = _json_from(run_orchestrate(args).stdout, what)
    if isinstance(data, dict):  # agents are grouped by kind
        items = [x for group in data.values() if isinstance(group, list) for x in group]
    else:
        items = data
    return frozenset(x["name"] for x in items if isinstance(x, dict) and x.get("name"))


def take_snapshot() -> Snapshot:
    return Snapshot(
        agents=_names(["agents", "list", "--verbose"], "agent"),
        tools=_names(["tools", "list", "--verbose"], "tool"),
        kbs=_names(["knowledge-bases", "list", "--verbose"], "knowledge base"),
    )


def _display(args: list[str], root: Path) -> str:
    return " ".join(args).replace(str(root) + os.sep, "")


def _execute(actions: list[Action], root: Path, dry_run: bool) -> None:
    for action in actions:
        if dry_run:
            plain(f"  [dry-run] {action.label}: orchestrate {_display(action.args, root)}")
            continue
        try:
            run_orchestrate(action.args)
        except AdkError as exc:
            raise AdkError(f"{action.label} failed.\n{exc}", exc.returncode) from exc
        ok(action.label)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def run_deploy(targets: list[Target], cfg: Config | None, root: Path, dry_run: bool) -> int:
    """Deploy each target in order (scenarios first). `cfg` may be None only for a dry run."""
    everything = load_scenarios(root)
    ordered = _scenarios_first(targets)

    groups: list[tuple[str, list[Action], Target | None]] = []
    connections = connection_actions(root) if any(t.scenario for t in ordered) else []
    if connections:
        groups.append(("Connections", connections, None))
    for t in ordered:
        if t.scenario is not None:
            actions = scenario_deploy_actions(t.scenario, everything)
        elif t.agent is not None:
            actions = standalone_deploy_actions(t.agent)
        elif t.tool is not None:
            actions = tool_deploy_actions(t.tool)
        else:
            actions = []
        groups.append((f"{t.name} ({t.kind})", actions, t))

    if not dry_run:
        start_t = time.monotonic()
        start_dt = datetime.now()
        login(cfg)
        ok(f"Logged in to '{cfg.env_name}'")

    for title, actions, target in groups:
        plain(f"Deploying {title}")
        if target and target.agent and target.agent.knowledge_bases and not dry_run:
            missing = sorted(set(target.agent.knowledge_bases) - take_snapshot().kbs)
            if missing:
                warn(
                    f"Knowledge base(s) not found: {', '.join(missing)}. The agent will not "
                    f"answer from documents until they exist (deploy the scenario that owns them)."
                )
        if target:
            tests = target_test_cases(root, target)
            if tests:
                plain(f"  Test suite: {len(tests)} test case(s) ready in {tests[0].parent.relative_to(root).as_posix()}")
        _execute(actions, root, dry_run)

    if dry_run:
        plain("Dry run only: nothing was changed.")
    else:
        end_dt = datetime.now()
        secs = round(time.monotonic() - start_t)
        elapsed = f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
        ok(f"Deployed {len(ordered)} target(s)")
        plain(f"  Started:  {start_dt.strftime('%H:%M:%S')}")
        plain(f"  Finished: {end_dt.strftime('%H:%M:%S')}")
        plain(f"  Elapsed:  {elapsed}")
    return 0


def _confirm(question: str) -> bool:
    answer = input(f"{question} [y/N] ").strip().lower()
    return answer in ("y", "yes")


def run_undeploy(
    targets: list[Target], cfg: Config | None, root: Path, dry_run: bool, assume_yes: bool
) -> int:
    """Remove each target's resources, newest dependencies first. Asks first unless --yes."""
    if not dry_run and not assume_yes and not sys.stdin.isatty():
        raise UsageError(
            "undeploy needs confirmation, but this is not an interactive terminal.\n"
            "Re-run with --yes to confirm, or with --dry-run to preview."
        )

    # Standalone agents use the scenarios' knowledge bases, so they go first.
    ordered = list(reversed(_scenarios_first(targets)))
    groups: list[tuple[Target, list[Action]]] = []
    for t in ordered:
        if t.scenario is not None:
            actions = scenario_remove_actions(t.scenario)
        elif t.agent is not None:
            actions = standalone_remove_actions(t.agent)
        elif t.tool is not None:
            actions = tool_remove_actions(t.tool)
        else:
            actions = []
        groups.append((t, actions))

    if dry_run:
        for t, actions in groups:
            plain(f"Would undeploy {t.name} ({t.kind})")
            _execute(actions, root, dry_run=True)
        plain("Dry run only: nothing was changed.")
        return 0

    login(cfg)
    ok(f"Logged in to '{cfg.env_name}'")
    snapshot = take_snapshot()

    plan: list[tuple[Target, list[Action]]] = []
    absent = 0
    for t, actions in groups:
        present = [a for a in actions if snapshot.has(*a.resource)]
        absent += len(actions) - len(present)
        if present:
            plan.append((t, present))
    if absent:
        info(f"{absent} resource(s) are already absent and will be skipped")
    if not plan:
        ok("Nothing to remove")
        return 0

    plain("This will remove from the active WXO environment:")
    for t, actions in plan:
        plain(f"  {t.name} ({t.kind}): " + ", ".join(a.label.lower() for a in actions))
    if not assume_yes and not _confirm("Continue?"):
        plain("Cancelled. Nothing was removed.")
        return 1

    for t, actions in plan:
        plain(f"Undeploying {t.name}")
        _execute(actions, root, dry_run=False)
    ok(f"Removed resources of {len(plan)} target(s)")
    return 0


def run_status(targets: list[Target], cfg: Config) -> int:
    """Compare what the repo defines with what exists in the active environment."""
    login(cfg)
    snapshot = take_snapshot()

    rows: list[tuple[str, str, str, str, list[str]]] = []
    for t in targets:
        exp = expected_resources(t)
        groups = (("agent", exp.agents), ("tool", exp.tools), ("kb", exp.kbs))
        total = sum(len(names) for _, names in groups)
        missing = [
            f"{kind} {n}" for kind, names in groups for n in names if not snapshot.has(kind, n)
        ]
        if not missing:
            state = "deployed"
        else:
            state = "not deployed" if len(missing) == total else "partial"
        detail = ", ".join(
            f"{kind}s {sum(snapshot.has(kind, n) for n in names)}/{len(names)}"
            for kind, names in groups
            if names
        )
        rows.append((t.name, t.kind, state, detail, missing if state == "partial" else []))

    width = max(len(r[0]) for r in rows)
    plain(f"{'NAME':<{width}}  {'KIND':<10}  {'STATE':<12}  DETAIL")
    for name, kind, state, detail, missing in rows:
        plain(f"{name:<{width}}  {kind:<10}  {state:<12}  {detail}")
        if missing:
            plain(f"{'':<{width}}  missing: {', '.join(missing)}")
    return 0

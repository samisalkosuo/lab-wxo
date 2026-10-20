"""Scenario manifests (scenarios/<id>/scenario.yaml): load, resolve, plan, validate.

Needs PyYAML (installed with ibm-watsonx-orchestrate), imported lazily so commands that do
not read manifests work before `setup`. Only reads files. Never reads env.cfg or local/.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wxodemo.config import UsageError

STATUSES = ("live", "soon")
TIERS = ("core", "full")
REQUIRED = ("id", "name", "description", "status")
# @tool, optionally with arguments that do not rename the tool (name= is not supported here)
TOOL_RE = re.compile(r"^@tool(?:\([^)]*\))?\s*\r?\n\s*def (\w+)", re.M)


class ManifestError(Exception):
    """A manifest or a file it points to is broken. Exit code 1."""


@dataclass(frozen=True)
class Scenario:
    id: str  # folder name under scenarios/
    data: dict[str, Any]
    root: Path

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


@dataclass(frozen=True)
class DeployStep:
    """One import. kind: tool_py | tool_openapi | tool_pkg | kb | flow | agent."""

    kind: str
    path: Path  # file to import (package directory for tool_pkg)
    entry: Path | None = None  # tool_pkg only
    requirements: Path | None = None  # tool_pkg only
    name: str | None = None  # agent only


@dataclass(frozen=True)
class RemoveStep:
    """One removal. kind: agent | flow | tool | kb."""

    kind: str
    name: str
    agent_kind: str = "native"  # agent only


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError as exc:
        raise UsageError(
            "PyYAML is not installed for this Python. Run: python wxodemo.py setup"
        ) from exc
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path.name}: invalid YAML: {exc}") from exc


def load_scenarios(root: Path) -> dict[str, Scenario]:
    """{id: Scenario} for every scenarios/*/scenario.yaml, sorted by id."""
    found: dict[str, Scenario] = {}
    base = root / "scenarios"
    if base.is_dir():
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            manifest = folder / "scenario.yaml"
            if manifest.is_file():
                data = load_yaml(manifest)
                if not isinstance(data, dict):
                    raise ManifestError(f"{rel(root, manifest)}: not a YAML mapping")
                found[folder.name] = Scenario(folder.name, data, root)
    return found


# ---------------------------------------------------------------------------
# Resolving manifest entries to files
# ---------------------------------------------------------------------------


def kb_file(root: Path, kb: dict) -> Path:
    folder = root / kb["path"]
    if not folder.is_dir():
        raise ManifestError(f"knowledge base '{kb['name']}': folder {kb['path']} not found")
    for candidate in sorted(folder.glob("*.yaml")):
        data = load_yaml(candidate)
        if isinstance(data, dict) and data.get("name") == kb["name"]:
            return candidate
    raise ManifestError(f"knowledge base '{kb['name']}': no *.yaml with that name in {kb['path']}")


def flow_file(root: Path, flow: dict) -> Path:
    folder = root / flow["path"]
    if not folder.is_dir():
        raise ManifestError(f"flow '{flow['name']}': folder {flow['path']} not found")
    if flow.get("file"):
        target = folder / flow["file"]
        if not target.is_file():
            raise ManifestError(f"flow '{flow['name']}': {flow['path']}/{flow['file']} not found")
        return target
    candidates = [p for p in sorted(folder.glob("*.py")) if p.name != "__init__.py"]
    if len(candidates) != 1:
        raise ManifestError(
            f"flow '{flow['name']}': {flow['path']} has {len(candidates)} .py files; "
            f"set 'file:' in the manifest"
        )
    return candidates[0]


def agent_file(root: Path, agent: dict) -> Path:
    target = root / agent["path"] / "agent.yaml"
    if not target.is_file():
        raise ManifestError(f"agent '{agent['name']}': {agent['path']}/agent.yaml not found")
    return target


def tool_step(root: Path, tool: dict) -> DeployStep:
    path = root / tool["path"]
    if path.is_file():
        if path.suffix == ".py":
            return DeployStep("tool_py", path)
        if path.suffix in (".yaml", ".yml", ".json"):
            return DeployStep("tool_openapi", path)
        raise ManifestError(f"tool path {tool['path']}: unsupported file type")
    if path.is_dir():
        if not tool.get("entry"):
            raise ManifestError(f"tool package {tool['path']}: 'entry' is required")
        entry, requirements = path / tool["entry"], path / "requirements.txt"
        if not entry.is_file():
            raise ManifestError(f"tool package {tool['path']}: entry {tool['entry']} not found")
        if not requirements.is_file():
            raise ManifestError(f"tool package {tool['path']}: requirements.txt not found")
        return DeployStep("tool_pkg", path, entry=entry, requirements=requirements)
    raise ManifestError(f"tool path {tool['path']} not found")


# ---------------------------------------------------------------------------
# Cross-scenario checks
# ---------------------------------------------------------------------------


def owned_names(m: Scenario) -> dict[str, list[str]]:
    """{kind: [names]} owned by one scenario."""
    return {
        "agent": [a["name"] for a in m.get("agents") or []],
        "tool": [n for t in m.get("tools") or [] for n in t.get("names") or []],
        "flow": [f["name"] for f in m.get("flows") or []],
        "knowledge base": [k["name"] for k in m.get("knowledge_bases") or []],
    }


def name_clashes(scenarios: dict[str, Scenario]) -> list[str]:
    """Tool, flow, agent and KB names are resources of the whole WXO instance."""
    seen: dict[tuple[str, str], str] = {}
    problems: list[str] = []
    for sid, m in scenarios.items():
        for kind, names in owned_names(m).items():
            for name in names:
                # tools and flows share the tool namespace in WXO (flows are imported as tools)
                namespace = "tool" if kind in ("tool", "flow") else kind
                key = (namespace, name)
                if key in seen and seen[key] != sid:
                    problems.append(
                        f"{namespace} name '{name}' is used by both '{seen[key]}' and '{sid}'"
                    )
                seen.setdefault(key, sid)
    return problems


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


def deploy_plan(scenarios: dict[str, Scenario], chosen: list[Scenario]) -> list[DeployStep]:
    """Import order: tools, knowledge bases, flows, agents (each phase across all chosen)."""
    clashes = name_clashes(scenarios)
    if clashes:
        raise ManifestError("name clash between scenarios:\n  " + "\n  ".join(clashes))
    tools: list[DeployStep] = []
    kbs: list[DeployStep] = []
    flows: list[DeployStep] = []
    agents: list[DeployStep] = []
    for m in chosen:
        for t in m.get("tools") or []:
            tools.append(tool_step(m.root, t))
        for k in m.get("knowledge_bases") or []:
            kbs.append(DeployStep("kb", kb_file(m.root, k)))
        for f in m.get("flows") or []:
            flows.append(DeployStep("flow", flow_file(m.root, f)))
        for a in m.get("agents") or []:
            agents.append(DeployStep("agent", agent_file(m.root, a), name=a["name"]))
    return tools + kbs + flows + agents


def teardown_plan(chosen: list[Scenario]) -> list[RemoveStep]:
    """Removal order: agents (reversed), flows, tools, knowledge bases."""
    agents: list[RemoveStep] = []
    flows: list[RemoveStep] = []
    tools: list[RemoveStep] = []
    kbs: list[RemoveStep] = []
    for m in chosen:
        for a in m.get("agents") or []:
            agents.append(RemoveStep("agent", a["name"], a.get("kind", "native")))
        flows += [RemoveStep("flow", f["name"]) for f in m.get("flows") or []]
        tools += [RemoveStep("tool", n) for t in m.get("tools") or [] for n in t.get("names") or []]
        kbs += [RemoveStep("kb", k["name"]) for k in m.get("knowledge_bases") or []]
    return list(reversed(agents)) + flows + tools + kbs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_scenario(m: Scenario) -> list[str]:
    """Problems found in one scenario (empty list = valid)."""
    root, sid = m.root, m.id
    errs: list[str] = []
    err = errs.append

    for key in REQUIRED:
        if not m.get(key):
            err(f"missing required field '{key}'")
    if m.get("id") != sid:
        err(f"id '{m.get('id')}' must equal the folder name '{sid}'")
    if m.get("status") not in STATUSES:
        err(f"status must be one of {STATUSES}")

    ev = m.get("evaluation")
    truth = root / ev["path"] / "ground_truth.json" if ev else None
    if ev:
        if ev.get("tier") not in TIERS:
            err(f"evaluation.tier must be one of {TIERS}")
        if not truth.is_file():
            err(f"{ev['path']}/ground_truth.json not found (the core evaluation tier is required)")
    elif m.get("status") == "live":
        err("evaluation section missing (ground_truth.json is required for a live scenario)")
    if ev and m.get("status") == "live" and truth.is_file():
        try:
            gt = json.loads(truth.read_text(encoding="utf-8-sig"))
        except ValueError as exc:
            gt = None
            err(f"{ev['path']}/ground_truth.json is not valid JSON: {exc}")
        if gt is not None:
            prompts = gt.get("smoke_prompts")
            if not (
                isinstance(prompts, list)
                and prompts
                and all(isinstance(x, dict) and x.get("id") and x.get("prompt") for x in prompts)
            ):
                err(
                    f"{ev['path']}/ground_truth.json needs a non-empty 'smoke_prompts' list "
                    f"of {{id, prompt}} objects (used by 'wxodemo smoke')"
                )

    demo = (m.get("demo") or {}).get("script")
    if m.get("status") == "live":
        if not demo or not (root / demo).is_file():
            err(f"live scenario needs demo.script that exists (got {demo!r})")
        if not (root / "docs" / "demo" / "scenarios" / f"{sid}.js").is_file():
            err(f"live scenario needs docs/demo/scenarios/{sid}.js")

    own_tools: set[str] = set()
    for t in m.get("tools") or []:
        names = t.get("names") or []
        own_tools.update(names)
        try:
            step = tool_step(root, t)
        except ManifestError as exc:
            err(str(exc))
            continue
        if step.kind in ("tool_py", "tool_pkg"):
            source = step.path if step.kind == "tool_py" else step.entry
            found = TOOL_RE.findall(source.read_text(encoding="utf-8-sig"))
            if sorted(found) != sorted(names):
                err(
                    f"@tool functions in {rel(root, source)} {sorted(found)} "
                    f"!= manifest names {sorted(names)}"
                )
        attached = set(t.get("attached") or [])
        if not attached <= set(names):
            err(f"tool 'attached' not subset of 'names': {sorted(attached - set(names))}")

    flow_names: set[str] = set()
    for f in m.get("flows") or []:
        flow_names.add(f["name"])
        try:
            source_file = flow_file(root, f)
            source = source_file.read_text(encoding="utf-8-sig")
            pattern = r"name\s*=\s*[\"']" + re.escape(f["name"]) + r"[\"']"
            if not re.search(pattern, source):
                err(f"flow name '{f['name']}' not found as name=... in {rel(root, source_file)}")
        except ManifestError as exc:
            err(str(exc))

    kb_names: set[str] = set()
    for k in m.get("knowledge_bases") or []:
        kb_names.add(k["name"])
        try:
            kb_file(root, k)
        except ManifestError as exc:
            err(str(exc))

    attached_all = {n for t in m.get("tools") or [] for n in (t.get("attached") or [])}
    unattached = own_tools - attached_all
    for a in m.get("agents") or []:
        try:
            spec = load_yaml(agent_file(root, a))
        except ManifestError as exc:
            err(str(exc))
            continue
        if spec.get("name") != a["name"]:
            err(f"agent yaml name '{spec.get('name')}' != manifest '{a['name']}'")
        agent_tools = set(spec.get("tools") or [])
        leaked = sorted(agent_tools & unattached)
        if leaked:
            err(f"agent '{a['name']}' lists tools the manifest marks as not attached: {leaked}")
        missing = sorted(attached_all - agent_tools)
        if missing and len(m.get("agents") or []) == 1:
            err(f"agent '{a['name']}' does not list attached tools: {missing}")
        unknown = sorted(agent_tools - own_tools - flow_names)
        if unknown:
            err(
                f"agent '{a['name']}' lists tools this scenario does not own: {unknown} "
                f"(own: tools + flows; shared tools are not supported)"
            )
        kb_unknown = sorted(set(spec.get("knowledge_base") or []) - kb_names)
        if kb_unknown:
            err(
                f"agent '{a['name']}' lists knowledge bases this scenario does not own: "
                f"{kb_unknown}"
            )
    return errs

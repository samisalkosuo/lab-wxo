"""Everything deployable in the repo: scenarios and standalone agents, and name resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wxodemo.config import UsageError
from wxodemo.manifest import TOOL_RE, Scenario, load_scenarios, load_yaml

KINDS = ("scenario", "standalone", "tool")


@dataclass(frozen=True)
class ToolFile:
    path: Path
    names: list[str]  # @tool functions defined in the file


@dataclass(frozen=True)
class ToolTarget:
    name: str
    path: Path
    entry: Path
    is_package: bool
    names: list[str]
    requirements: Path | None = None


@dataclass(frozen=True)
class StandaloneAgent:
    name: str  # from agent.yaml
    dir: Path
    yaml_path: Path
    description: str
    tools: list[ToolFile]
    kind: str = "native"  # agent kind for `agents remove --kind`
    knowledge_bases: tuple[str, ...] = ()  # names the agent.yaml expects to exist


@dataclass(frozen=True)
class Target:
    """Something `deploy` / `undeploy` / `validate` can act on."""

    kind: str  # "scenario" | "standalone" | "tool"
    name: str  # scenario id, standalone agent name, or tool name
    status: str  # "live" | "soon" for scenarios; "-" for standalone/tool
    summary: str
    scenario: Scenario | None = None
    agent: StandaloneAgent | None = None
    tool: ToolTarget | None = None

    def matches(self, name: str) -> bool:
        if self.name == name:
            return True
        # standalone agents are also addressable by directory name (hello-world)
        if self.agent is not None and self.agent.dir.name == name:
            return True
        if self.tool is not None:
            if self.tool.path.name == name:
                return True
            if self.name.replace("_", "-") == name.replace("_", "-"):
                return True
        return False


def discover_standalone(root: Path) -> tuple[list[StandaloneAgent], list[str]]:
    """Every standalone/*/agent.yaml. Returns (agents, problems for skipped directories)."""
    agents: list[StandaloneAgent] = []
    problems: list[str] = []
    base = root / "standalone"
    if not base.is_dir():
        return agents, problems
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        yaml_path = folder / "agent.yaml"
        if not yaml_path.is_file():
            continue
        data = load_yaml(yaml_path)
        if not isinstance(data, dict) or not data.get("name"):
            problems.append(f"standalone/{folder.name}/agent.yaml has no 'name' field")
            continue
        tools = []
        for py in sorted(folder.glob("*.py")):
            names = TOOL_RE.findall(py.read_text(encoding="utf-8-sig"))
            if names:
                tools.append(ToolFile(py, names))
        agents.append(
            StandaloneAgent(
                name=data["name"],
                dir=folder,
                yaml_path=yaml_path,
                description=" ".join(str(data.get("description") or "").split()),
                tools=tools,
                kind=str(data.get("kind") or "native"),
                knowledge_bases=tuple(data.get("knowledge_base") or ()),
            )
        )
    return agents, problems


def _scenario_tool_paths(root: Path) -> set[Path]:
    """Resolved file and folder paths of tools owned by scenario manifests."""
    paths: set[Path] = set()
    for s in load_scenarios(root).values():
        for t in s.get("tools") or []:
            p_str = t.get("path")
            if p_str:
                paths.add((root / p_str).resolve())
    return paths


def discover_tools(root: Path) -> tuple[list[ToolTarget], list[str]]:
    """Every standalone tool package and tool file under tools/ not owned by a scenario."""
    tools: list[ToolTarget] = []
    problems: list[str] = []
    base = root / "tools"
    if not base.is_dir():
        return tools, problems

    scenario_tools = _scenario_tool_paths(root)

    for folder in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if folder.resolve() in scenario_tools:
            continue
        entry = folder / f"{folder.name}.py"
        if not entry.is_file():
            candidates = [py for py in sorted(folder.glob("*.py")) if TOOL_RE.findall(py.read_text(encoding="utf-8-sig"))]
            if candidates:
                entry = candidates[0]
            else:
                continue

        names = TOOL_RE.findall(entry.read_text(encoding="utf-8-sig"))
        if not names:
            continue

        req = folder / "requirements.txt"
        tools.append(
            ToolTarget(
                name=folder.name,
                path=folder,
                entry=entry,
                is_package=True,
                names=names,
                requirements=req if req.is_file() else None,
            )
        )

    for py in sorted(p for p in base.iterdir() if p.is_file() and p.suffix == ".py"):
        if py.resolve() in scenario_tools:
            continue
        names = TOOL_RE.findall(py.read_text(encoding="utf-8-sig"))
        if names:
            tools.append(
                ToolTarget(
                    name=py.stem,
                    path=py,
                    entry=py,
                    is_package=False,
                    names=names,
                    requirements=None,
                )
            )

    return tools, problems


def all_targets(root: Path) -> tuple[list[Target], list[str]]:
    """Scenarios (sorted by id), standalone agents, and tools. Second item: discovery problems."""
    targets = [
        Target("scenario", s.id, str(s.get("status") or "?"), str(s.get("name") or ""), scenario=s)
        for s in load_scenarios(root).values()
    ]
    agents, agent_problems = discover_standalone(root)
    targets += [Target("standalone", a.name, "-", a.description, agent=a) for a in agents]
    tool_targets, tool_problems = discover_tools(root)
    targets += [
        Target(
            "tool",
            t.name,
            "-",
            f"Tools: {', '.join(t.names)}",
            tool=t,
        )
        for t in tool_targets
    ]
    return targets, agent_problems + tool_problems


def resolve_targets(
    targets: list[Target],
    names: list[str],
    *,
    select_all: bool = False,
    kind: str | None = None,
    live_only: bool = False,
) -> list[Target]:
    """Pick targets by name or all of them, optionally restricted to one kind.

    live_only drops scenarios with status 'soon' when selecting all (used by deploy);
    explicitly named targets are always kept.
    """
    if names and select_all:
        raise UsageError("Give target names or --all, not both.")
    if not names and not select_all:
        raise UsageError("Name at least one target, or use --all. See: python wxodemo.py list")

    pool = [t for t in targets if kind is None or t.kind == kind]

    if select_all:
        everything = [
            t for t in pool if not (live_only and t.kind == "scenario" and t.status != "live")
        ]
        if not everything:
            scope = f" of kind '{kind}'" if kind else ""
            raise UsageError(f"No targets{scope} to select. See: python wxodemo.py list")
        return everything

    chosen: list[Target] = []
    for name in names:
        hits = [t for t in pool if t.matches(name)]
        if not hits:
            known = ", ".join(t.name for t in pool) or "(none)"
            raise UsageError(f"Unknown target '{name}'. Known: {known}")
        if len(hits) > 1:
            kinds = " and ".join(t.kind for t in hits)
            choices_str = "|".join(KINDS)
            raise UsageError(f"'{name}' matches both a {kinds}. Add --kind {choices_str}.")
        if hits[0] not in chosen:
            chosen.append(hits[0])
    return chosen

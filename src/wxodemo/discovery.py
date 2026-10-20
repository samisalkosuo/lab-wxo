"""Everything deployable in the repo: scenarios and standalone agents, and name resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wxodemo.config import UsageError
from wxodemo.manifest import TOOL_RE, Scenario, load_scenarios, load_yaml

KINDS = ("scenario", "standalone")


@dataclass(frozen=True)
class ToolFile:
    path: Path
    names: list[str]  # @tool functions defined in the file


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

    kind: str  # "scenario" | "standalone"
    name: str  # scenario id, or standalone agent name
    status: str  # "live" | "soon" for scenarios; "-" for standalone agents
    summary: str
    scenario: Scenario | None = None
    agent: StandaloneAgent | None = None

    def matches(self, name: str) -> bool:
        if self.name == name:
            return True
        # standalone agents are also addressable by directory name (hello-world)
        return self.agent is not None and self.agent.dir.name == name


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


def all_targets(root: Path) -> tuple[list[Target], list[str]]:
    """Scenarios (sorted by id) then standalone agents. Second item: discovery problems."""
    targets = [
        Target("scenario", s.id, str(s.get("status") or "?"), str(s.get("name") or ""), scenario=s)
        for s in load_scenarios(root).values()
    ]
    agents, problems = discover_standalone(root)
    targets += [Target("standalone", a.name, "-", a.description, agent=a) for a in agents]
    return targets, problems


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
            raise UsageError(f"'{name}' matches both a {kinds}. Add --kind scenario|standalone.")
        if hits[0] not in chosen:
            chosen.append(hits[0])
    return chosen

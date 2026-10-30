"""Builders for a throwaway repo layout, shared by the tests."""

import json
from pathlib import Path

from wxodemo.adk import AdkError

TOOL_SRC = "from x import tool\n\n@tool\ndef do_it():\n    pass\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def make_scenario(root: Path, sid: str, *, status: str = "live", tool: str = "do_it") -> None:
    write(
        root / "scenarios" / sid / "scenario.yaml",
        f"""id: {sid}
name: Scenario {sid}
description: test
status: {status}
agents:
  - name: agent_{sid}
    path: agents/{sid}
    kind: native
tools:
  - path: tools/{sid}.py
    names: [{tool}]
    attached: [{tool}]
knowledge_bases:
  - name: kb_{sid}
    path: knowledge/{sid}
flows: []
evaluation:
  path: evaluation/{sid}
  tier: core
demo:
  script: docs/demo/{sid}-demo.md
""",
    )
    write(
        root / "agents" / sid / "agent.yaml",
        f"name: agent_{sid}\ntools: [{tool}]\nknowledge_base: [kb_{sid}]\n",
    )
    write(root / "tools" / f"{sid}.py", TOOL_SRC.replace("do_it", tool))
    write(root / "knowledge" / sid / "kb.yaml", f"name: kb_{sid}\n")
    truth = {"smoke_prompts": [{"id": "p1", "prompt": "hi"}]}
    write(root / "evaluation" / sid / "ground_truth.json", json.dumps(truth))
    write(root / "docs" / "demo" / f"{sid}-demo.md", "demo")
    write(root / "docs" / "demo" / "scenarios" / f"{sid}.js", "//")


def make_standalone(root: Path, folder: str, name: str, tool: str | None = None) -> None:
    write(root / "standalone" / folder / "agent.yaml", f"name: {name}\ndescription: some  agent\n")
    if tool:
        write(root / "standalone" / folder / "tools.py", TOOL_SRC.replace("do_it", tool))


def make_tool_pkg(root: Path, name: str, tools: list[str] = ("tool_func",), reqs: bool = True) -> None:
    src_lines = ["from x import tool\n"]
    for t in tools:
        src_lines.append(f"@tool\ndef {t}():\n    pass\n")
    write(root / "tools" / name / f"{name}.py", "\n".join(src_lines))
    if reqs:
        write(root / "tools" / name / "requirements.txt", "# deps\n")


class FakeOrchestrate:
    """Stands in for run_orchestrate. Records calls; `existing` is what `... list --verbose`
    reports; any call whose text contains an entry of `fail_on` raises AdkError."""

    def __init__(self, existing=None, fail_on=None):
        self.calls: list[list[str]] = []
        self.existing = existing or {"agents": [], "tools": [], "knowledge-bases": []}
        self.fail_on = fail_on or []

    def __call__(self, args, **kwargs):
        self.calls.append(list(args))
        for needle in self.fail_on:
            if needle in " ".join(args):
                raise AdkError(f"boom: {needle}", 1)
        if args[1:3] == ["list", "--verbose"]:
            items = [{"name": n} for n in self.existing[args[0]]]
            payload = {"native": items} if args[0] == "agents" else items

            class Result:
                stdout = json.dumps(payload)

            return Result()
        return None

    def commands(self) -> list[str]:
        return [" ".join(c) for c in self.calls if c[1:3] != ["list", "--verbose"]]

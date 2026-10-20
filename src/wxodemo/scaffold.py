"""Scaffold a new demo scenario: folders, manifest, agent stub, ground-truth stub, demo script
from the template, and the slides file plus its <script> tag in presentation.html.

Creates (never overwrites; stops if scenarios/<id>/ already exists):
    scenarios/<id>/scenario.yaml        manifest, status: soon, empty tool/KB/flow lists
    agents/<id>/agent.yaml              agent stub (name = id with underscores; no tools yet)
    evaluation/<id>/ground_truth.json   core evaluation stub (empty smoke_prompts)
    docs/demo/<id>-demo.md              copy of the demo-script template ({{ID}}, {{NAME}},
                                        {{AGENT_NAME}} filled in; every other placeholder is yours)
    docs/demo/scenarios/<id>.js         "soon" placeholder slide, only if the file does not exist
    docs/demo/presentation.html         one <script src="scenarios/<id>.js"> line, only if absent

It does NOT create tools, knowledge documents, flows or real prompts: that is the work of the
scenario. Status stays `soon`, so `deploy --all` skips it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from wxodemo.config import UsageError
from wxodemo.logging_setup import ok, plain, warn
from wxodemo.manifest import load_scenarios, name_clashes, owned_names, validate_scenario

TEMPLATE = Path(".bob") / "skills" / "scenario-demo-docs" / "templates" / "demo-script.template.md"
PRESENTATION = Path("docs") / "demo" / "presentation.html"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
AGENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SCRIPT_TAG_RE = re.compile(r'^([ \t]*)<script src="scenarios/[^"]+\.js"></script>[ \t]*\r?$', re.M)


def _js_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def manifest_text(sid: str, name: str, desc: str, agent: str) -> str:
    snake = sid.replace("-", "_")
    return f"""# scenario.yaml - manifest for the {name} scenario.
# Field reference and a complete example: scenarios/incident-triage/scenario.yaml
# Status stays `soon` until the scenario is deployed and its demo script is written.

id: {sid}
name: {name}
description: {desc}
status: soon

agents:
  - name: {agent}
    path: agents/{sid}
    kind: native

# Add each tool package. Example (names = every @tool function, attached = what the agent may call):
#   - path: tools/{snake}
#     entry: {snake}.py
#     names: [tool_one, tool_two]
#     attached: [tool_one]
tools: []

# Example:
#   - name: {snake}_docs
#     path: knowledge/{sid}
knowledge_bases: []

# Example (only when a write action needs human approval):
#   - name: request_something
#     path: flows/{snake}
flows: []

evaluation:
  path: evaluation/{sid}
  tier: core

demo:
  script: docs/demo/{sid}-demo.md
"""


def agent_text(agent: str, desc: str) -> str:
    return f"""spec_version: v1
kind: native
name: {agent}
description: >
  TODO: {desc}
instructions: >
  TODO: write the agent's instructions. Name each tool and say when to use it.
llm: groq/openai/gpt-oss-120b
style: react_core
collaborators: []
tools: []
"""


def ground_truth_text(name: str) -> str:
    return f"""{{
  "version": "1.0",
  "description": "Ground truth for the {name} scenario (core evaluation tier).",
  "smoke_prompts": [],
  "cases": {{}}
}}
"""


def placeholder_js(sid: str, name: str, desc: str, position: int) -> str:
    blurb = (
        f"This scenario template is ready for your team's upcoming {_js_escape(name)} "
        f"agent workflows and demo scripts."
    )

    return f"""// Scenario: {name} (placeholder). Registers itself on window.SCENARIOS.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {{
        id: "{sid}",
        name: "{_js_escape(name)} Agent",
        label: "{_js_escape(name)}",
        description: "{_js_escape(desc)}",
        status: "soon",
        slides: [
          {{
            title: "{_js_escape(name)}",
            tag: "Scenario {position} \u2022 Overview",
            subtitle: "{_js_escape(desc)}",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">\U0001f680</div>
                <div>
                  <div class="callout-title">Scenario Under Development</div>
                  <div class="callout-text">{blurb}</div>
                </div>
              </div>
            `
          }}
        ]
      }}
);
"""


@dataclass(frozen=True)
class ScaffoldPlan:
    sid: str
    agent: str
    position: int  # 1-based sidebar position
    writes: list[tuple[Path, str]]
    js_exists: bool
    has_tag: bool
    tag_line: str


def build_plan(root: Path, sid: str, name: str, desc: str, agent_name: str | None) -> ScaffoldPlan:
    """Validate the request and work out every file to write. Touches nothing on disk."""
    if not ID_RE.match(sid):
        raise UsageError(
            f"id '{sid}' must be kebab-case (lowercase letters, digits, single hyphens)"
        )
    if sid == "hello-world":
        raise UsageError("'hello-world' is reserved")
    agent = agent_name or sid.replace("-", "_")
    if not AGENT_RE.match(agent):
        raise UsageError(f"agent name '{agent}' must be snake_case")

    if (root / "scenarios" / sid).exists():
        raise UsageError(f"scenarios/{sid}/ already exists; nothing was changed")
    for path in (
        root / "agents" / sid,
        root / "evaluation" / sid,
        root / "docs" / "demo" / f"{sid}-demo.md",
    ):
        if path.exists():
            raise UsageError(
                f"{path.relative_to(root).as_posix()} already exists; nothing was changed"
            )
    template = root / TEMPLATE
    if not template.is_file():
        raise UsageError(f"template not found: {TEMPLATE.as_posix()}")
    presentation = root / PRESENTATION
    if not presentation.is_file():
        raise UsageError(f"{PRESENTATION.as_posix()} not found")

    # Tool, flow, KB and agent names are instance-wide, so a clashing agent name breaks deploys.
    for other_id, other in load_scenarios(root).items():
        if agent in owned_names(other)["agent"]:
            raise UsageError(
                f"agent name '{agent}' is already used by scenario '{other_id}'. Pass --agent-name."
            )

    text = presentation.read_bytes().decode("utf-8")
    tags = list(SCRIPT_TAG_RE.finditer(text))
    if not tags:
        raise UsageError('no <script src="scenarios/...js"> lines found in presentation.html')
    tag_line = f'<script src="scenarios/{sid}.js"></script>'
    existing = [m.group(0).strip() for m in tags]
    has_tag = tag_line in existing
    position = existing.index(tag_line) + 1 if has_tag else len(tags) + 1

    js_path = root / "docs" / "demo" / "scenarios" / f"{sid}.js"
    demo = (
        template.read_text(encoding="utf-8-sig")
        .replace("{{ID}}", sid)
        .replace("{{NAME}}", name)
        .replace("{{AGENT_NAME}}", agent)
    )
    writes = [
        (root / "scenarios" / sid / "scenario.yaml", manifest_text(sid, name, desc, agent)),
        (root / "agents" / sid / "agent.yaml", agent_text(agent, desc)),
        (root / "evaluation" / sid / "ground_truth.json", ground_truth_text(name)),
        (root / "docs" / "demo" / f"{sid}-demo.md", demo),
    ]
    if not js_path.exists():
        writes.append((js_path, placeholder_js(sid, name, desc, position)))
    return ScaffoldPlan(sid, agent, position, writes, js_path.exists(), has_tag, tag_line)


def add_script_tag(path: Path, tag_line: str) -> None:
    """Insert the tag after the last scenario tag, keeping the file's line endings."""
    text = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    last = list(SCRIPT_TAG_RE.finditer(text))[-1]
    # The match ends before the line's own "\n" (after its "\r", if any). Add a new line
    # that carries its own "\r" so the original "\n" ends it.
    insert = "\n" + last.group(1) + tag_line + ("\r" if crlf else "")
    updated = text[: last.end()] + insert + text[last.end() :]
    path.write_bytes(updated.encode("utf-8"))


def run_new_scenario(
    root: Path, sid: str, name: str, desc: str, agent_name: str | None, dry_run: bool
) -> int:
    plan = build_plan(root, sid, name, desc, agent_name)

    plain(f"Scaffolding scenario '{sid}' (agent '{plan.agent}', sidebar position {plan.position})")
    prefix = "[dry-run] " if dry_run else ""
    for path, _ in plan.writes:
        plain(f"  {prefix}+ {path.relative_to(root).as_posix()}")
    if plan.js_exists:
        plain(f"  = docs/demo/scenarios/{sid}.js exists already: left unchanged")
    if plan.has_tag:
        plain("  = presentation.html already has the script tag: left unchanged")
    else:
        plain(f"  {prefix}~ docs/demo/presentation.html: add {plan.tag_line}")
    if dry_run:
        plain("Dry run only: nothing was written.")
        return 0

    for path, text in plan.writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    if not plan.has_tag:
        add_script_tag(root / PRESENTATION, plan.tag_line)
    ok(f"Scenario '{sid}' created")

    scenarios = load_scenarios(root)
    problems = validate_scenario(scenarios[sid]) + name_clashes(scenarios)
    if problems:
        warn("The new scenario does not validate yet:")
        for line in problems:
            plain(f"    {line}")
    plain(
        f"""
Next steps (the scenario stays `soon` until you finish them):
  1. Build the mock data, tools, knowledge documents and flow; list them in
     scenarios/{sid}/scenario.yaml.
  2. Fill in agents/{sid}/agent.yaml (instructions, tools, knowledge_base).
  3. Add real smoke_prompts and cases to evaluation/{sid}/ground_truth.json.
  4. python wxodemo.py validate {sid}
  5. python wxodemo.py deploy {sid}, then python wxodemo.py smoke {sid}
  6. Write docs/demo/{sid}-demo.md and docs/demo/scenarios/{sid}.js from what you observed;
     set status: live in the manifest and in the .js file.
  7. python wxodemo.py validate {sid}   (also checks that the demo script and slides agree)"""
    )
    return 0

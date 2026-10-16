#!/usr/bin/env python3
"""Scaffold a new demo scenario: folders, manifest, agent stub, ground-truth stub, demo
script from the template, and the slides file plus its <script> tag in presentation.html.

Usage:
    python scripts/new-scenario.py customer-returns \
        --name "Customer Returns" --description "Messy input, return policy & deterministic refund rules"
    python scripts/new-scenario.py my-scenario --name "My Scenario" --description "One line" --dry-run

Creates (never overwrites; stops if scenarios/<id>/ already exists):
    scenarios/<id>/scenario.yaml          manifest, status: soon, empty tool/KB/flow lists
    agents/<id>/agent.yaml                agent stub (name = <id> with underscores; no tools yet)
    evaluation/<id>/ground_truth.json     core evaluation stub (empty smoke_prompts)
    docs/demo/<id>-demo.md                copy of the demo-script template ({{ID}}, {{NAME}},
                                          {{AGENT_NAME}} filled in; every other placeholder is yours)
    docs/demo/scenarios/<id>.js           "soon" placeholder slide, only if the file does not exist
    docs/demo/presentation.html           one <script src="scenarios/<id>.js"> line, only if absent

Does NOT create tools, knowledge base documents, flows or real prompts: that is the work of the
scenario (see the wxo-scenario-authoring and scenario-demo-docs skills). Status stays `soon`, so
`deploy-all` without --scenario skips it. After scaffolding it runs the manifest validator and the
name-clash check and prints what is still missing.

Needs PyYAML (same Python environment as the orchestrate CLI). Never reads env.cfg or local/.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenario_manifest as sm  # noqa: E402

ROOT = sm.ROOT
TEMPLATE_MD = ROOT / ".bob" / "skills" / "scenario-demo-docs" / "templates" / "demo-script.template.md"
PRESENTATION = ROOT / "docs" / "demo" / "presentation.html"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SCRIPT_TAG_RE = re.compile(r'^([ \t]*)<script src="scenarios/[^"]+\.js"></script>[ \t]*\r?$', re.M)


def js_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def manifest_text(sid: str, name: str, desc: str, agent: str) -> str:
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
#   - path: tools/{sid.replace('-', '_')}
#     entry: {sid.replace('-', '_')}.py
#     names: [tool_one, tool_two]
#     attached: [tool_one]
tools: []

# Example:
#   - name: {sid.replace('-', '_')}_docs
#     path: knowledge/{sid}
knowledge_bases: []

# Example (only when a write action needs human approval):
#   - name: request_something
#     path: flows/{sid.replace('-', '_')}
flows: []

evaluation:
  path: evaluation/{sid}
  tier: core
  package_include: []

demo:
  script: docs/demo/{sid}-demo.md

package:
  zip_prefix: {sid}
"""


def agent_text(agent: str, name: str, desc: str) -> str:
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


def placeholder_js(sid: str, name: str, desc: str, n: int) -> str:
    return f"""// Scenario: {name} (placeholder). Registers itself on window.SCENARIOS.
window.SCENARIOS = window.SCENARIOS || [];
window.SCENARIOS.push(
      {{
        id: "{sid}",
        name: "{js_escape(name)} Agent",
        label: "{js_escape(name)}",
        description: "{js_escape(desc)}",
        status: "soon",
        slides: [
          {{
            title: "{js_escape(name)}",
            tag: "Scenario {n} \u2022 Overview",
            subtitle: "{js_escape(desc)}",
            render: () => `
              <div class="callout-banner">
                <div class="callout-icon">\U0001F680</div>
                <div>
                  <div class="callout-title">Scenario Under Development</div>
                  <div class="callout-text">This scenario template is ready for your team's upcoming {js_escape(name)} agent workflows and demo scripts.</div>
                </div>
              </div>
            `
          }}
        ]
      }}
);
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", help="kebab-case scenario id, e.g. customer-returns")
    ap.add_argument("--name", required=True, help='display name, e.g. "Customer Returns"')
    ap.add_argument("--description", required=True, help="one line for the sidebar")
    ap.add_argument("--agent-name", default=None, help="WXO agent name (default: id with underscores)")
    ap.add_argument("--dry-run", action="store_true", help="print what would be created; write nothing")
    a = ap.parse_args()

    sid = a.id
    if not ID_RE.match(sid):
        sys.exit(f"ERROR: id '{sid}' must be kebab-case (lowercase letters, digits, single hyphens)")
    if sid == "hello-world":
        sys.exit("ERROR: 'hello-world' is reserved")
    agent = a.agent_name or sid.replace("-", "_")
    if not re.match(r"^[a-z][a-z0-9_]*$", agent):
        sys.exit(f"ERROR: agent name '{agent}' must be snake_case")

    if (ROOT / "scenarios" / sid).exists():
        sys.exit(f"ERROR: scenarios/{sid}/ already exists; nothing was changed")
    for p in (ROOT / "agents" / sid, ROOT / "evaluation" / sid, ROOT / "docs" / "demo" / f"{sid}-demo.md"):
        if p.exists():
            sys.exit(f"ERROR: {p.relative_to(ROOT).as_posix()} already exists; nothing was changed")
    if not TEMPLATE_MD.is_file():
        sys.exit(f"ERROR: template not found: {TEMPLATE_MD.relative_to(ROOT).as_posix()}")
    if not PRESENTATION.is_file():
        sys.exit("ERROR: docs/demo/presentation.html not found")

    # Name clashes: tool/flow/KB/agent names are instance-wide. Check the agent name now.
    for other_id, m in sm.load_all().items():
        if agent in sm.owned_names(m)["agent"]:
            sys.exit(f"ERROR: agent name '{agent}' is already used by scenario '{other_id}'. "
                     f"Pass --agent-name.")

    pres_bytes = PRESENTATION.read_bytes()
    pres = pres_bytes.decode("utf-8")
    nl = "\r\n" if "\r\n" in pres else "\n"
    tags = list(SCRIPT_TAG_RE.finditer(pres))
    if not tags:
        sys.exit('ERROR: no <script src="scenarios/...js"> lines found in presentation.html')
    js_path = ROOT / "docs" / "demo" / "scenarios" / f"{sid}.js"
    tag_line = f'<script src="scenarios/{sid}.js"></script>'
    has_tag = tag_line in pres
    if has_tag:  # sidebar position = position of its existing <script> tag
        n = [m.group(0).strip() for m in tags].index(tag_line) + 1
    else:
        n = len(tags) + 1

    writes = [
        (ROOT / "scenarios" / sid / "scenario.yaml", manifest_text(sid, a.name, a.description, agent)),
        (ROOT / "agents" / sid / "agent.yaml", agent_text(agent, a.name, a.description)),
        (ROOT / "evaluation" / sid / "ground_truth.json", ground_truth_text(a.name)),
    ]
    md = (TEMPLATE_MD.read_text(encoding="utf-8-sig")
          .replace("{{ID}}", sid).replace("{{NAME}}", a.name).replace("{{AGENT_NAME}}", agent))
    writes.append((ROOT / "docs" / "demo" / f"{sid}-demo.md", md))
    if not js_path.exists():
        writes.append((js_path, placeholder_js(sid, a.name, a.description, n)))

    print(f"Scaffolding scenario '{sid}' (agent '{agent}', sidebar position {n})"
          + ("  [DRY RUN: nothing is written]" if a.dry_run else ""))
    for path, _ in writes:
        print(f"  + {path.relative_to(ROOT).as_posix()}")
    if js_path.exists():
        print(f"  = docs/demo/scenarios/{sid}.js exists already: left unchanged")
    if has_tag:
        print(f"  = presentation.html already has {tag_line}: left unchanged")
    else:
        print(f"  ~ docs/demo/presentation.html: add {tag_line}")
    if a.dry_run:
        return 0

    for path, text in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    if not has_tag:
        last = tags[-1]
        insert = nl + last.group(1) + tag_line
        new = pres[: last.end()].rstrip("\r") + insert + pres[last.end():]
        PRESENTATION.write_bytes(new.encode("utf-8"))

    manifests = sm.load_all()
    problems = sm.validate(manifests, sid)
    print("\nManifest validation: " + ("OK" if not problems else ""))
    for p in problems:
        print("  PROBLEM: " + p)
    print(f"""
Next (scenario still `soon`; see the wxo-scenario-authoring and scenario-demo-docs skills):
  1. Build the mock data, tools, knowledge base documents and flow; list them in scenarios/{sid}/scenario.yaml.
  2. Fill in agents/{sid}/agent.yaml (instructions, tools, knowledge_base).
  3. Add real smoke_prompts and cases to evaluation/{sid}/ground_truth.json.
  4. python scripts/scenario_manifest.py validate --scenario {sid}
  5. scripts/deploy-all --scenario {sid}; run the scenario; then write docs/demo/{sid}-demo.md and
     docs/demo/scenarios/{sid}.js from what you observed; set status: live in both places.
  6. python .bob/skills/scenario-demo-docs/check_demo_consistency.py {sid}""")
    return 0


if __name__ == "__main__":
    sys.exit(main())

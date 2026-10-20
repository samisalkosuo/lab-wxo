"""Validation of scenarios: the manifest against its files, and the demo script against the slides.

Demo checks, per scenario id (docs/demo/scenarios/<id>.js):
  1. presentation.html has a <script src="scenarios/<id>.js"> tag.
  2. Every slide tag "Scenario N" has N equal to the scenario's 1-based position among those tags.
  3. No template leftovers ({{...}} or "AUTHOR NOTE") in the .js or the demo .md.
  4. Prompts: the "Prompt (type exactly...)" code blocks in docs/demo/<id>-demo.md equal, in order
     and word for word, the prompt-box texts in the .js. Skipped when there is no demo .md and the
     scenario is not live and the slides hold no prompts.
  5. copyPrompt('prompt-N') ids match their prompt-box ids and are unique.
  6. Every tool-chip in the .js is a real tool, flow or knowledge base name from the manifest.

Only reads files; never changes anything.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from wxodemo.logging_setup import fail, get_logger, ok, plain
from wxodemo.manifest import Scenario, load_scenarios, name_clashes, owned_names, validate_scenario

PRESENTATION = Path("docs") / "demo" / "presentation.html"
SCRIPT_RE = re.compile(r'<script src="scenarios/([^"]+)\.js"></script>')
PROMPT_BOX_RE = re.compile(r'<div class="prompt-box" id="(prompt-\d+)">(.*?)</div>', re.S)


@dataclass
class DemoReport:
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def script_order(root: Path) -> list[str]:
    """Scenario ids in the order of the <script> tags in presentation.html (the sidebar order)."""
    path = root / PRESENTATION
    if not path.is_file():
        return []
    return SCRIPT_RE.findall(path.read_text(encoding="utf-8"))


def md_prompts(md_text: str) -> list[str]:
    """Code blocks that follow a '**Prompt (type exactly' line, in document order."""
    prompts: list[str] = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("**Prompt (type exactly"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            k = j + 1
            body: list[str] = []
            while k < len(lines) and not lines[k].startswith("```"):
                body.append(lines[k])
                k += 1
            prompts.append("\n".join(body).strip())
            i = k
        i += 1
    return prompts


def js_prompts(js_text: str) -> list[tuple[str, str]]:
    return [(pid, html.unescape(text).strip()) for pid, text in PROMPT_BOX_RE.findall(js_text)]


def check_demo(root: Path, scenario: Scenario, order: list[str]) -> DemoReport:
    """Consistency of one scenario's demo script (.md) and slides (.js)."""
    sid = scenario.id
    report = DemoReport()
    problem, note = report.problems.append, report.notes.append

    js_path = root / "docs" / "demo" / "scenarios" / f"{sid}.js"
    md_path = root / "docs" / "demo" / f"{sid}-demo.md"
    if not js_path.is_file():
        # A live scenario without slides is already reported by the manifest check.
        note(f"no docs/demo/scenarios/{sid}.js: demo checks skipped")
        return report
    js = js_path.read_text(encoding="utf-8")
    md = md_path.read_text(encoding="utf-8-sig") if md_path.is_file() else None

    # 1 + 2: registration and slide tag numbers
    if sid not in order:
        problem(f'presentation.html has no <script src="scenarios/{sid}.js"> tag')
    else:
        position = order.index(sid) + 1
        for number in re.findall(r'tag:\s*"Scenario (\d+)', js):
            if int(number) != position:
                problem(f"slide tag says Scenario {number} but sidebar position is {position}")

    # 3: template leftovers
    for label, text in (("slides (.js)", js), ("demo script (.md)", md or "")):
        if "{{" in text:
            problem(f"{label} still contains a {{{{PLACEHOLDER}}}}")
        if "AUTHOR NOTE" in text:
            problem(f"{label} still contains an AUTHOR NOTE")

    # 4: prompts
    found = re.search(r'status:\s*"(\w+)"', js)
    status = found.group(1) if found else "?"
    boxes = js_prompts(js)
    if md is None:
        if status == "live" or boxes:
            problem(
                f"no docs/demo/{sid}-demo.md (status {status}, {len(boxes)} prompt(s) in slides)"
            )
        else:
            note(f"status {status}, no demo script yet: prompt check skipped")
    else:
        from_md = md_prompts(md)
        from_js = [text for _, text in boxes]
        if len(from_md) != len(from_js):
            problem(
                f"prompt count differs: demo script has {len(from_md)}, slides have {len(from_js)}"
            )
        for n, (a, b) in enumerate(zip(from_md, from_js, strict=False), 1):
            if a != b:
                problem(
                    f"prompt {n} differs between script and slides:\n"
                    f"      script: {a!r}\n      slide : {b!r}"
                )
        note(f"{min(len(from_md), len(from_js))} prompt(s) compared")

    # 5: copy-button ids
    ids = [pid for pid, _ in boxes]
    calls = re.findall(r"copyPrompt\('(prompt-\d+)'", js)
    if len(set(ids)) != len(ids):
        problem(f"duplicate prompt-box ids: {ids}")
    if sorted(calls) != sorted(ids):
        problem(f"copyPrompt ids {calls} do not match prompt-box ids {ids}")

    # 6: tool chips against the manifest
    owned = owned_names(scenario)
    names = set(owned["tool"]) | set(owned["flow"]) | set(owned["knowledge base"])
    chips = set(re.findall(r'<span class="tool-chip">([^<]+)</span>', js))
    unknown = sorted(chip for chip in chips if chip not in names)
    if unknown:
        problem(f"tool-chip names not in scenario.yaml: {unknown}")
    note(f"{len(chips)} tool chip(s) checked against the manifest")
    return report


def validate_all(root: Path, chosen: list[Scenario]) -> tuple[dict[str, list[str]], list[str]]:
    """({scenario id: problems}, instance-wide name clashes) for the chosen scenarios."""
    order = script_order(root)
    results: dict[str, list[str]] = {}
    for scenario in chosen:
        problems = validate_scenario(scenario)
        report = check_demo(root, scenario, order)
        for line in report.notes:
            get_logger().debug("%s: %s", scenario.id, line)
        results[scenario.id] = problems + [f"demo: {p}" for p in report.problems]
    # Names are shared by the whole WXO instance, so always check across every scenario.
    return results, name_clashes(load_scenarios(root))


def run_validate(root: Path, chosen: list[Scenario], other_problems: list[str]) -> int:
    """Print one line per scenario. 0 when everything is consistent, else 1."""
    results, clashes = validate_all(root, chosen)
    failed = 0
    for sid, problems in results.items():
        if problems:
            failed += 1
            fail(f"{sid}: {len(problems)} problem(s)")
            for line in problems:
                plain(f"    {line}")
        else:
            ok(sid)
    for clash in clashes:
        fail(clash)
    return 1 if failed or clashes or other_problems else 0

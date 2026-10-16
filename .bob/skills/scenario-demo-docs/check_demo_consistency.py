#!/usr/bin/env python3
"""Consistency check for a scenario's demo script and presentation file.

Usage (from anywhere):
    python .bob/skills/scenario-demo-docs/check_demo_consistency.py            # all scenarios
    python .bob/skills/scenario-demo-docs/check_demo_consistency.py customer-returns

Checks, per scenario id (docs/demo/scenarios/<id>.js):
  1. presentation.html has a <script src="scenarios/<id>.js"> tag.
  2. Every slide tag "Scenario N" has N equal to the scenario's 1-based position among those tags.
  3. No template leftovers ({{...}} or "AUTHOR NOTE") in the .js or the demo .md.
  4. Prompts: the "Prompt (type exactly...)" code blocks in docs/demo/<id>-demo.md equal, in order and
     word for word, the prompt-box texts in the .js. Skipped when status is "soon" and no demo .md exists.
  5. copyPrompt('prompt-N') ids match their prompt-box ids and are unique.
  6. If scenarios/<id>/scenario.yaml exists and PyYAML is installed: every tool-chip in the .js is a real
     tool, flow or knowledge base name from the manifest.

Exit code 0 = all checks passed, 1 = at least one failure. Only reads files; never changes anything.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "docs" / "demo"
PRESENTATION = DEMO / "presentation.html"


def script_order():
    text = PRESENTATION.read_text(encoding="utf-8")
    return re.findall(r'<script src="scenarios/([^"]+)\.js"></script>', text)


def md_prompts(md_text):
    """Code blocks that follow a '**Prompt (type exactly' line, in document order."""
    prompts = []
    lines = md_text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("**Prompt (type exactly"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            k = j + 1
            body = []
            while k < len(lines) and not lines[k].startswith("```"):
                body.append(lines[k])
                k += 1
            prompts.append("\n".join(body).strip())
            i = k
        i += 1
    return prompts


def js_prompts(js_text):
    boxes = re.findall(r'<div class="prompt-box" id="(prompt-\d+)">(.*?)</div>', js_text, flags=re.S)
    return [(pid, html.unescape(t).strip()) for pid, t in boxes]


def manifest_names(sid):
    path = ROOT / "scenarios" / sid / "scenario.yaml"
    if not path.exists():
        return None, "no scenarios/%s/scenario.yaml" % sid
    try:
        import yaml  # PyYAML, present in the repo .venv
    except ImportError:
        return None, "PyYAML not installed, manifest check skipped"
    m = yaml.safe_load(path.read_text(encoding="utf-8"))
    names = set()
    for t in m.get("tools") or []:
        names.update(t.get("names") or [])
    names.update(f["name"] for f in m.get("flows") or [])
    names.update(k["name"] for k in m.get("knowledge_bases") or [])
    return names, None


def check(sid, order):
    problems, notes = [], []
    js_path = DEMO / "scenarios" / (sid + ".js")
    md_path = DEMO / (sid + "-demo.md")
    if not js_path.exists():
        return ["missing %s" % js_path.relative_to(ROOT)], notes
    js = js_path.read_text(encoding="utf-8")
    md = md_path.read_text(encoding="utf-8-sig") if md_path.exists() else None

    # 1 + 2: registration and slide tag numbers
    if sid not in order:
        problems.append("presentation.html has no <script src=\"scenarios/%s.js\"> tag" % sid)
    else:
        pos = order.index(sid) + 1
        for n in re.findall(r'tag:\s*"Scenario (\d+)', js):
            if int(n) != pos:
                problems.append("slide tag says Scenario %s but sidebar position is %d" % (n, pos))

    # 3: leftovers
    for label, text in (("js", js), ("md", md or "")):
        if "{{" in text:
            problems.append("%s still contains a {{PLACEHOLDER}}" % label)
        if "AUTHOR NOTE" in text:
            problems.append("%s still contains an AUTHOR NOTE" % label)

    # 4: prompts
    status = re.search(r'status:\s*"(\w+)"', js)
    status = status.group(1) if status else "?"
    boxes = js_prompts(js)
    if md is None:
        if status == "live" or boxes:
            problems.append("no docs/demo/%s-demo.md (status %s, %d prompts in slides)" % (sid, status, len(boxes)))
        else:
            notes.append("status %s, no demo script yet: prompt check skipped" % status)
    else:
        mdp = md_prompts(md)
        jsp = [t for _, t in boxes]
        if len(mdp) != len(jsp):
            problems.append("prompt count differs: demo md has %d, slides have %d" % (len(mdp), len(jsp)))
        for i, (a, b) in enumerate(zip(mdp, jsp), 1):
            if a != b:
                problems.append("prompt %d differs between md and slides:\n    md   : %r\n    slide: %r" % (i, a, b))
        notes.append("%d prompts compared" % min(len(mdp), len(jsp)))

    # 5: copy button ids
    ids = [pid for pid, _ in boxes]
    calls = re.findall(r"copyPrompt\('(prompt-\d+)'", js)
    if len(set(ids)) != len(ids):
        problems.append("duplicate prompt-box ids: %s" % ids)
    if sorted(calls) != sorted(ids):
        problems.append("copyPrompt ids %s do not match prompt-box ids %s" % (calls, ids))

    # 6: tool chips vs manifest
    names, why = manifest_names(sid)
    chips = set(re.findall(r'<span class="tool-chip">([^<]+)</span>', js))
    if names is None:
        notes.append(why)
    else:
        unknown = sorted(c for c in chips if c not in names)
        if unknown:
            problems.append("tool-chip names not in scenario.yaml: %s" % unknown)
        notes.append("%d tool chips checked against manifest" % len(chips))
    return problems, notes


def main():
    order = script_order()
    ids = sys.argv[1:] or order
    failed = False
    for sid in ids:
        problems, notes = check(sid, order)
        print("[%s] %s" % ("FAIL" if problems else "ok", sid))
        for n in notes:
            print("    note: " + n)
        for p in problems:
            print("    PROBLEM: " + p)
        failed = failed or bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

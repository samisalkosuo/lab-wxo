#!/usr/bin/env python3
"""
Build script: reads every docs/demo/<id>-demo.md and writes
docs/demo/demo-scripts-bundle.js containing window.DEMO_SCRIPTS.

Run from the repo root:
    python docs/demo/build-demo-scripts-bundle.py

Re-run it whenever a demo script (.md) changes. presentation.html loads the
bundle so the "Show full script" view works from file:// (no fetch needed).

Per scene the bundle keeps: intro text, the prompt(s) and the expected
behaviour. The "Point out", "Fallback" and "Be straight" blocks are dropped.

Shape:
    window.DEMO_SCRIPTS = {
      "<id>": {"scenes": [
        {"title": "Vague opening", "num": "1",
         "items": [
           {"t": "note", "text": "..."},
           {"t": "prompt", "card": 1, "note": "", "text": "..."},
           {"t": "prompt", "card": null, "label": "Sample document", "note": "...", "text": "..."},
           {"t": "expected", "status": "observed", "tone": "ok", "text": "..."},
           {"t": "form", "status": "...", "tone": "warn", "text": "..."},
           {"t": "path", "title": "Approve path", "status": "", "tone": "info",
            "same_prompt": false, "text": "..."}]}]}}

"card" is the 1-based position among the "**Prompt (" blocks of the md, i.e.
the N of prompt-N on the Live Demo Prompts slide. Prompts under a different
label (for example "**What to type") have card null: they get a Copy button
but no slide card.

Item types: note (any other text), expected ("**Expected behaviour (...)**"),
form ("**What the form shows**"), path ("### 3a. Approve path" sub-sections).
"status" is the text in the brackets; "tone" is ok / warn / info and drives the
colour of the status chip. "same_prompt" is true when the text says to send
"the same prompt": the viewer then repeats the scene's prompt with a Copy button.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "demo-scripts-bundle.js"

SCENE_RE = re.compile(r"^##\s+Scene\s+(\S+?)\s+[-\u2013\u2014]\s+(.*\S)\s*$")
H2_RE = re.compile(r"^##\s")
LABEL_RE = re.compile(r"^\*\*[^*\n]+\*\*")
PROMPT_LABEL_RE = re.compile(r"^\*\*(Prompt|What to type)\s*(?:\((.*?)\))?\s*:?\s*\*\*")
# "**Sample document (note):** hr-tk-sample/file.txt" -> copyable block with the file's text.
# The path is relative to docs/demo/, so the .txt stays the single source of the text.
SAMPLE_DOC_RE = re.compile(r"^\*\*Sample document\s*(?:\((.*?)\))?\s*:?\s*\*\*\s*(\S+)\s*$")
DROP_LABELS = ("**Point out", "**Fallback", "**Be straight")
EXPECTED_RE = re.compile(r"^Expected behaviour\s*(?:\((.*)\))?\s*:?$")
PAREN_RE = re.compile(r"^\s*\((.*?)\)\s*:\s*(.*)$|^\s*\((.*?)\)\s*(.*)$", re.S)
PATH_NUM_RE = re.compile(r"^\d+[a-z]\.\s*")


def _tone(status: str) -> str:
    low = status.lower()
    if not low:
        return "info"
    warn = ("not verified", "not yet", "not browser", "based on mock", "from the flow")
    if any(k in low for k in warn):
        return "warn"
    if "observed" in low or "browser-verified" in low:
        return "ok"
    return "info"


def _clean(status: str) -> str:
    status = status.replace("**", "").strip()
    return status[:1].upper() + status[1:]


def _classify(lines: list[str]) -> dict | None:
    """One block (starts at a bold label or a ### heading) -> typed item."""
    first = lines[0]
    rest_lines = lines[1:]
    if first.startswith("### "):
        title = PATH_NUM_RE.sub("", first[4:].strip())
        status = ""
        pm = re.match(r"^(.*?)\s*\((.*)\)\s*$", title)
        if pm:
            title, status = pm.group(1), pm.group(2)
        text = "\n".join(rest_lines).strip()
        same = "same prompt" in "\n".join(lines).lower()
        return {"t": "path", "title": title, "status": _clean(status), "tone": _tone(status),
                "same_prompt": same, "text": text}
    m = re.match(r"^\*\*(.+?)\*\*(.*)$", first)
    if not m:
        text = "\n".join(lines).strip()
        return {"t": "note", "text": text} if text else None
    label, rest = m.group(1).strip().rstrip(":").strip(), m.group(2)
    em = EXPECTED_RE.match(label)
    if em:
        status = em.group(1) or ""
        body = "\n".join(([rest.strip()] if rest.strip() else []) + rest_lines).strip()
        if not body:
            return None
        return {"t": "expected", "status": _clean(status), "tone": _tone(status), "text": body}
    if label.startswith("What the form shows"):
        status = ""
        lm = re.match(r"^What the form shows\s*\((.*)\)$", label)
        if lm:
            status = lm.group(1)
        else:
            rm = PAREN_RE.match(rest)
            if rm:
                if rm.group(1) is not None:
                    status, rest = rm.group(1), rm.group(2)
                else:
                    status, rest = rm.group(3), rm.group(4)
        body = "\n".join(([rest.strip()] if rest.strip() else []) + rest_lines).strip()
        if not body:
            return None
        return {"t": "form", "status": _clean(status), "tone": _tone(status), "text": body}
    return {"t": "note", "text": "\n".join(lines).strip()}


def split_blocks(text: str) -> list[dict]:
    """Split a markdown chunk at bold labels / ### headings (outside fences) into typed items."""
    blocks: list[list[str]] = []
    cur: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        is_fence = line.startswith("```")
        if is_fence:
            in_fence = not in_fence
        elif not in_fence and (LABEL_RE.match(line) or line.startswith("### ")):
            if cur:
                blocks.append(cur)
            cur = []
        cur.append(line)
    if cur:
        blocks.append(cur)
    items = []
    for block in blocks:
        item = _classify(block)
        if item:
            items.append(item)
    return items


def expand_items(items: list[dict]) -> list[dict]:
    out: list[dict] = []
    for item in items:
        if item["t"] == "md":
            out.extend(split_blocks(item["text"]))
        else:
            out.append(item)
    return out


def _prompt_note(raw: str | None) -> str:
    if not raw:
        return ""
    note = raw.strip()
    if note.lower().startswith("type exactly"):
        note = note[len("type exactly"):].lstrip(" ;,")
    return note


def parse_scene(lines: list[str], card_start: int) -> tuple[list[dict], int]:
    """Items for one scene's body lines. Returns (items, next card number)."""
    items: list[dict] = []
    md: list[str] = []
    card = card_start
    dropping = False
    in_fence = False
    pending: tuple[str, str] | None = None  # (label, note) waiting for its code fence
    prompt_lines: list[str] | None = None
    prompt_card: int | None = None
    prompt_note = ""

    def flush_md() -> None:
        text = "\n".join(md).strip("\n")
        md.clear()
        if text.strip():
            items.append({"t": "md", "text": text})

    for line in lines:
        if prompt_lines is not None:  # inside a prompt fence
            if line.startswith("```"):
                items.append({"t": "prompt", "card": prompt_card, "note": prompt_note,
                              "text": "\n".join(prompt_lines).strip()})
                prompt_lines = None
            else:
                prompt_lines.append(line)
            continue
        fence = line.startswith("```")
        if not in_fence and not fence:
            if line.strip() == "---":
                dropping = False
                continue
            if LABEL_RE.match(line) or line.startswith("### "):
                dropping = line.startswith(DROP_LABELS)
                sm = SAMPLE_DOC_RE.match(line)
                if sm:
                    flush_md()
                    doc = (SCRIPT_DIR / sm.group(2)).read_text(encoding="utf-8-sig")
                    items.append({"t": "prompt", "card": None, "label": "Sample document",
                                  "note": sm.group(1) or "", "text": doc.strip()})
                    continue
                pm = PROMPT_LABEL_RE.match(line)
                if pm:
                    flush_md()
                    pending = (pm.group(1), _prompt_note(pm.group(2)))
                    continue
        if dropping:
            if fence:
                in_fence = not in_fence
            continue
        if fence and pending is not None and not in_fence:
            flush_md()
            label, prompt_note = pending
            pending = None
            prompt_card = None
            if label == "Prompt":
                prompt_card = card
                card += 1
            prompt_lines = []
            continue
        if fence:
            in_fence = not in_fence
        md.append(line)
    flush_md()
    return items, card


def parse_md(text: str) -> dict:
    scenes: list[dict] = []
    current: dict | None = None
    body: list[str] = []
    card = 1

    def close() -> None:
        nonlocal card
        if current is not None:
            items, card = parse_scene(body, card)
            current["items"] = expand_items(items)
            scenes.append(current)

    for line in text.splitlines():
        m = SCENE_RE.match(line)
        if m:
            close()
            current = {"num": m.group(1), "title": m.group(2), "items": []}
            body = []
        elif H2_RE.match(line):
            close()
            current = None
            body = []
        elif current is not None:
            body.append(line)
    close()
    return {"scenes": scenes}


def build_bundle() -> None:
    md_files = sorted(SCRIPT_DIR.glob("*-demo.md"))
    if not md_files:
        print(f"No *-demo.md files found in {SCRIPT_DIR}", file=sys.stderr)
        sys.exit(1)

    scripts: dict[str, dict] = {}
    for md_path in md_files:
        sid = md_path.name[: -len("-demo.md")]
        scripts[sid] = parse_md(md_path.read_text(encoding="utf-8-sig"))

    lines = [
        "// AUTO-GENERATED \u2014 do not edit by hand.",
        "// Re-generate with: python docs/demo/build-demo-scripts-bundle.py",
        "//",
        "// Provides window.DEMO_SCRIPTS (prompt + expected behaviour per scene) for the",
        "// 'Show full script' view in presentation.html \u2014 works from file:// origins.",
        "window.DEMO_SCRIPTS = " + json.dumps(scripts, ensure_ascii=False, indent=1) + ";",
        "",
    ]
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    for sid, script in scripts.items():
        cards = sum(
            1 for s in script["scenes"] for i in s["items"] if i["t"] == "prompt" and i["card"]
        )
        print(f"{sid}: {len(script['scenes'])} scenes, {cards} prompt card(s)")
    print(f"Wrote {len(scripts)} scripts to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_bundle()

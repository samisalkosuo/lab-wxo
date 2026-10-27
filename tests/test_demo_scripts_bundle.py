"""Tests for docs/demo/build-demo-scripts-bundle.py (the full-script bundle generator)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from wxodemo import validate

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "build_demo_scripts_bundle", ROOT / "docs" / "demo" / "build-demo-scripts-bundle.py"
)
bundle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bundle)

SAMPLE = """# Title

## 1. Audience

text

## Scene 1 - First

Intro line.

**Prompt (type exactly):**

```
Hello?
```

**Expected behaviour (observed):**

- Calls `a`.
  - nested

```
code in expected
```

**Point out:**

- dropped

**Fallback:**

- dropped too

---

## Scene 2 \u2014 Second

**Prompt (type exactly; same as scene 1):**

```
One
```

**Expected behaviour:**

- first

**Prompt (type exactly):**

```
Two
```

**Expected behaviour:**

- second

**Be straight:** dropped

### 2a. Approve path

1. step

## 7. If it goes wrong

noise
"""


def test_scenes_and_prompt_cards():
    scenes = bundle.parse_md(SAMPLE)["scenes"]
    assert [s["title"] for s in scenes] == ["First", "Second"]
    prompts = [i for s in scenes for i in s["items"] if i["t"] == "prompt"]
    assert [(p["card"], p["text"]) for p in prompts] == [(1, "Hello?"), (2, "One"), (3, "Two")]
    assert prompts[1]["note"] == "same as scene 1"


def test_dropped_blocks_and_intro_kept():
    scenes = bundle.parse_md(SAMPLE)["scenes"]
    text = "\n".join(i["text"] for s in scenes for i in s["items"])
    assert "Intro line." in text
    assert "code in expected" in text
    assert "dropped" not in text
    assert "noise" not in text


def test_typed_items_and_status_tone():
    items = bundle.parse_md(SAMPLE)["scenes"][0]["items"]
    assert [i["t"] for i in items] == ["note", "prompt", "expected"]
    assert items[2]["status"] == "Observed" and items[2]["tone"] == "ok"
    second = bundle.parse_md(SAMPLE)["scenes"][1]["items"]
    assert [i["t"] for i in second] == ["prompt", "expected", "prompt", "expected", "path"]
    assert second[4]["title"] == "Approve path" and second[4]["same_prompt"] is False


def test_path_status_and_same_prompt():
    md = (
        "## Scene 1 - X\n\n**Prompt (type exactly):**\n\n```\nGo\n```\n\n"
        "**What the form shows** (not browser-verified): a card.\n\n"
        "### 1b. Reject path (new conversation)\n\n1. Send the same prompt.\n"
    )
    items = bundle.parse_md(md)["scenes"][0]["items"]
    form, path = items[1], items[2]
    assert form["t"] == "form" and form["tone"] == "warn" and form["text"] == "a card."
    assert path["title"] == "Reject path" and path["status"] == "New conversation"
    assert path["same_prompt"] is True


def test_other_label_prompt_has_no_card():
    md = (
        "## Scene 5 - X\n\n**What to type (same thread):**\n\n```\nGo\n```\n\n"
        "**Expected behaviour:**\n\n- ok\n"
    )
    prompt = bundle.parse_md(md)["scenes"][0]["items"][0]
    assert prompt["t"] == "prompt" and prompt["card"] is None


def test_repo_prompts_match_validator_extraction():
    """For every real demo md, bundle prompts with a card equal md_prompts() used by validate."""
    for md_path in sorted((ROOT / "docs" / "demo").glob("*-demo.md")):
        text = md_path.read_text(encoding="utf-8-sig")
        from_bundle = [
            i["text"]
            for s in bundle.parse_md(text)["scenes"]
            for i in s["items"]
            if i["t"] == "prompt" and i["card"]
        ]
        assert from_bundle == validate.md_prompts(text), md_path.name

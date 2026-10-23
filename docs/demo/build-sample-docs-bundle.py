#!/usr/bin/env python3
"""
Build script: reads every .md file in sample-docs/ and writes
docs/demo/sample-docs-bundle.js containing window.SAMPLE_DOCS —
a plain JS object keyed by "sample-docs/<filename>".

Run from the repo root:
    python docs/demo/build-sample-docs-bundle.py

Or from the docs/demo directory:
    python build-sample-docs-bundle.py

The generated bundle is loaded by presentation.html before
standalone-agents.js so that the async loader can resolve documents
without needing a web server (avoids CORS errors with file:// URLs).
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SAMPLE_DOCS_DIR = SCRIPT_DIR / "sample-docs"
OUTPUT_FILE = SCRIPT_DIR / "sample-docs-bundle.js"


def build_bundle() -> None:
    md_files = sorted(SAMPLE_DOCS_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {SAMPLE_DOCS_DIR}", file=sys.stderr)
        sys.exit(1)

    docs: dict[str, str] = {}
    for md_path in md_files:
        key = f"sample-docs/{md_path.name}"
        docs[key] = md_path.read_text(encoding="utf-8")

    lines = [
        "// AUTO-GENERATED — do not edit by hand.",
        "// Re-generate with: python docs/demo/build-sample-docs-bundle.py",
        "//",
        "// Provides window.SAMPLE_DOCS so that standalone-agents.js can resolve",
        "// sample document content without fetch() — required for file:// origins.",
        "window.SAMPLE_DOCS = " + json.dumps(docs, ensure_ascii=False, indent=2) + ";",
        "",
    ]
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(docs)} documents to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_bundle()

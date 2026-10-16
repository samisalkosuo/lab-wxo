"""Build dist/wxo-<zip_prefix>-<version>.zip for external users, for ONE scenario.

Usage:
    python scripts/package.py --scenario incident-triage [--version 1.0.0]

Needs the Python environment that has PyYAML (the one with ibm-watsonx-orchestrate; it depends on
PyYAML), because the scenario manifest is YAML.

The zip contains everything an external user needs to deploy that scenario into their own
watsonx Orchestrate instance. What goes in comes from the manifest scenarios/<id>/scenario.yaml.
The build uses an ALLOW-LIST (only listed paths are added) and then a DENY-LIST post-build check
(fails with a non-zero exit code and deletes the zip if any denied path or secret-bearing pattern
is found).

What ships (all derived from the manifest):
    agents/, tools/, knowledge/, flows/ folders the manifest lists
    evaluation/<id>/ground_truth.json plus the files in evaluation.package_include
                                      (never results/ or eval_run.log)
    the demo markdown (demo.script)
    docs/demo/presentation.html       a COPY with <script> tags of other scenarios removed
    docs/demo/scenarios/<id>.js       only when the scenario has slides
    scenarios/<id>/scenario.yaml      the manifest; the deploy scripts read it
    scripts/deploy-all.ps1 .sh, scripts/teardown.ps1 .sh, scripts/scenario_manifest.py,
    scripts/smoke_test.py             (smoke test only when the scenario has an evaluation)
    env.cfg.example, requirements.txt
    INSTALL.md                        generated at the zip root from the manifest, plus the optional
                                      scenarios/<id>/install-notes.md (known issues of this scenario)

What does NOT ship (by design):
    everything that belongs to another scenario (checked by the deny-list below)
    env.cfg, local/                   secrets
    .venv/ .bob/ .orchestrate/ .git/ dist/ __pycache__/ *.pyc *.pyo
    evaluation/<id>/results/, eval_run.log

The post-build security check scans every entry name against the deny-list and scans every TEXT
entry for the literal string WXO_API_KEY= followed by a non-empty value, and for long token-like
strings (>= 40 chars of base64/hex chars without whitespace). If any check fails the zip is
deleted and the script exits non-zero.

NEVER reads, prints, or modifies env.cfg or local/notes.md.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenario_manifest as sm  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VERSION_DEFAULT = "1.0.0"

# Patterns of zip-entry names (after normalisation to forward slashes) that must
# NEVER appear in the zip.  Checked after the build.  The paths owned by OTHER
# scenarios are added at run time (see other_scenarios_deny()).
DENY_PATTERNS: list[str] = [
    r"(^|/)env\.cfg$",           # real secrets file (not .example)
    r"(^|/)local/",              # local/ directory and its contents
    r"(^|/)\.venv/",             # Python virtual environment
    r"(^|/)\.git(/|$)",          # git repository
    r"(^|/)dist/",               # build output
    r"(^|/)__pycache__/",        # compiled Python cache
    r"\.pyc$",                   # compiled Python bytecode
    r"\.pyo$",                   # optimised bytecode
    r"(^|/)\.bob/",              # Bob AI assistant state
    r"(^|/)\.orchestrate/",      # orchestrate CLI state
    r"(^|/)results/",            # evaluation result dumps (large, instance-specific)
    r"eval_run\.log$",           # evaluation log (instance-specific)
]

# Secret-value patterns to scan inside text entries.
# Pattern 1: WXO_API_KEY= followed by a value that is not:
#   - empty / end-of-line
#   - a placeholder string (your-api-key-here, <...>, $..., "$...", "")
#   - a shell variable reference ($VALUE, "$VALUE", '""', etc.)
SECRET_VALUE_PATTERN = re.compile(
    r'WXO_API_KEY='           # key name
    r'(?!'                    # negative lookahead — safe values:
        r'your-api-key-here'  # our standard placeholder
        r'|<[^>]+>'           # angle-bracket placeholders like <your IBM Cloud API key>
        r'|\$[A-Za-z_]'       # shell variable $value
        r'|"\$[A-Za-z_]'     # quoted shell variable "$value"
        r'|""'                # empty string assignment
        r'|\s*$'              # end of line / whitespace only
    r')'
    r'(.+)',
    re.IGNORECASE
)
# Pattern 2: long token-like strings.
# Real API keys / tokens are random base64 or hex — they do NOT contain
# underscores (Python identifiers) or forward slashes used as path separators.
# We use a character class that does include the base64 slash (+/=) but then
# filter out any token that also contains an underscore or a slash, which
# distinguishes file paths and identifiers from actual secret tokens.
LONG_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+/=]{40,}")

# File extensions we decode and scan for secrets (text files only)
TEXT_EXTENSIONS = {
    ".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".txt", ".md",
    ".cfg", ".env", ".example", ".ini", ".toml", ".conf", ".js", ".html",
}

REPO_ROOT = sm.ROOT


def other_scenarios_deny(manifests: dict, scenario_id: str) -> list[str]:
    """Deny patterns for every path owned by a scenario other than scenario_id."""
    patterns = []
    for sid, m in manifests.items():
        if sid == scenario_id:
            continue
        for p in sm.owned_paths(m):
            patterns.append(r"^" + re.escape(p) + r"(/|$)")
    return patterns


# ---------------------------------------------------------------------------
# Allow-list: built from the manifest.
# For directories the entire tree is added except __pycache__ and .pyc files.
# ---------------------------------------------------------------------------

def build_allow_list(m: dict) -> tuple[list[tuple[Path, str]], list[str]]:
    """Return ([(absolute_src_path, zip_entry_name), ...], [missing repo-relative paths]).

    zip_entry_name uses forward slashes (POSIX) regardless of OS.
    """
    pairs: list[tuple[Path, str]] = []
    missing: list[str] = []
    sid = m["_dir"]

    def add_tree(rel_dir: str) -> None:
        src_dir = REPO_ROOT / rel_dir
        for abs_path in sorted(src_dir.rglob("*")):
            if not abs_path.is_file():
                continue
            parts = abs_path.relative_to(src_dir).parts
            if any(p == "__pycache__" for p in parts):
                continue
            if abs_path.suffix in (".pyc", ".pyo"):
                continue
            pairs.append((abs_path, rel_dir + "/" + "/".join(parts)))

    def add_path(rel: str) -> None:
        p = REPO_ROOT / rel
        if p.is_dir():
            add_tree(rel)
        elif p.is_file():
            pairs.append((p, rel))
        else:
            missing.append(rel)

    for a in m.get("agents") or []:
        add_path(a["path"])
    for t in m.get("tools") or []:
        add_path(t["path"])
    for k in m.get("knowledge_bases") or []:
        add_path(k["path"])
    for f in m.get("flows") or []:
        add_path(f["path"])

    ev = m.get("evaluation")
    if ev:
        # ground_truth.json is the core tier and the smoke test needs it: always ship it
        for item in dict.fromkeys(["ground_truth.json"] + list(ev.get("package_include") or [])):
            add_path(ev["path"] + "/" + item)

    demo = (m.get("demo") or {}).get("script")
    if demo:
        add_path(demo)
    # presentation.html and the scenario's slides: see build_zip() (a trimmed copy is written)
    if (REPO_ROOT / "docs" / "demo" / "scenarios" / f"{sid}.js").is_file():
        add_path(f"docs/demo/scenarios/{sid}.js")

    add_path(f"scenarios/{sid}/scenario.yaml")

    for s in ("deploy-all.ps1", "deploy-all.sh", "teardown.ps1", "teardown.sh", "scenario_manifest.py"):
        add_path(f"scripts/{s}")
    if ev:
        add_path("scripts/smoke_test.py")

    add_path("env.cfg.example")
    add_path("requirements.txt")
    return pairs, missing


def trimmed_presentation(scenario_id: str) -> str | None:
    """docs/demo/presentation.html with the <script src="scenarios/X.js"> tags of other
    scenarios removed, or None when this scenario has no slides."""
    if not (REPO_ROOT / "docs" / "demo" / "scenarios" / f"{scenario_id}.js").is_file():
        return None
    src = (REPO_ROOT / "docs" / "demo" / "presentation.html").read_bytes().decode("utf-8")
    keep = f'scenarios/{scenario_id}.js'
    tag = re.compile(r'^[ \t]*<script src="(scenarios/[^"]+\.js)"></script>[ \t]*\r?\n', re.M)
    out = tag.sub(lambda mo: mo.group(0) if mo.group(1) == keep else "", src)
    if f'<script src="{keep}"></script>' not in out:
        raise RuntimeError(f'docs/demo/presentation.html has no <script src="{keep}"> tag; '
                           f"register the scenario there (see the scenario-demo-docs skill).")
    return out


# ---------------------------------------------------------------------------
# Post-build security check
# ---------------------------------------------------------------------------

def check_zip(zip_path: Path, extra_deny: list[str]) -> list[str]:
    """Return a list of violation strings.  Empty list = clean."""
    violations: list[str] = []
    deny_compiled = [re.compile(p) for p in DENY_PATTERNS + extra_deny]

    with zipfile.ZipFile(zip_path, "r") as zf:
        entries = sorted(zf.namelist())
        print("\n--- Zip entry list ---")
        for name in entries:
            print(" ", name)
        print(f"--- Total: {len(entries)} entries ---\n")

        for name in entries:
            # 1. Deny-list check on entry name
            for pattern in deny_compiled:
                if pattern.search(name):
                    violations.append(f"DENY-LIST MATCH: '{name}' matches /{pattern.pattern}/")

            # 2. Scan text entries for secret patterns
            ext = Path(name).suffix.lower()
            if ext in TEXT_EXTENSIONS:
                try:
                    raw = zf.read(name)
                    text = raw.decode("utf-8", errors="replace")
                    lines = text.splitlines()
                    for lineno, line in enumerate(lines, 1):
                        m = SECRET_VALUE_PATTERN.search(line)
                        if m:
                            violations.append(
                                f"SECRET PATTERN in {name}:{lineno}: "
                                f"WXO_API_KEY= with non-placeholder value"
                            )
                        # Long-token check: look for tokens >= 40 chars that look
                        # like random secrets.  Skip additional safe contexts below.
                        if "http" not in line and "github.com" not in line:
                            tokens = LONG_TOKEN_PATTERN.findall(line)
                            for tok in tokens:
                                # Paths and Python identifiers contain _ or /
                                if "_" in tok or "/" in tok:
                                    continue
                                # All-uppercase = env var name or constant
                                if re.match(r"^[A-Z]+$", tok):
                                    continue
                                # All-lowercase = word or identifier
                                if re.match(r"^[a-z]+$", tok):
                                    continue
                                # Skip known placeholder text
                                if "your-api-key-here" in tok or "instance-id" in tok:
                                    continue
                                violations.append(
                                    f"LONG TOKEN in {name}:{lineno}: "
                                    f"'{tok[:20]}...' ({len(tok)} chars) — review manually"
                                )
                except Exception as exc:
                    violations.append(f"SCAN ERROR reading {name}: {exc}")

    return violations


# ---------------------------------------------------------------------------
# INSTALL.md (generated)
# ---------------------------------------------------------------------------

def _agent_llms(m: dict) -> list[tuple[str, str]]:
    out = []
    for a in m.get("agents") or []:
        y = sm.load_yaml(sm.agent_file(a)) or {}
        if y.get("llm"):
            out.append((a["name"], y["llm"]))
    return out


def build_install_md(m: dict, entries: list[str]) -> str:
    """Write INSTALL.md for one scenario. Generic text is the text that shipped for incident
    triage before the manifest existed; scenario-specific facts come from the manifest."""
    sid, name = m["_dir"], m["name"]
    ev = m.get("evaluation") or {}
    includes = set(ev.get("package_include") or [])
    agents = m.get("agents") or []
    kbs = m.get("knowledge_bases") or []
    flows = m.get("flows") or []
    has_eval_cfg = "eval_config.yaml" in includes
    has_baseline = "baseline.py" in includes
    has_slides = f"docs/demo/scenarios/{sid}.js" in entries
    notes_file = REPO_ROOT / "scenarios" / sid / "install-notes.md"
    L: list[str] = []

    def w(*lines: str) -> None:
        L.extend(lines)

    w(f"# {name} — Installation Guide", "",
      "## What this package contains", "",
      f"A self-contained watsonx Orchestrate (WXO) demo scenario: {m['description']}.",
      "It uses a fixed mock dataset and calls no external service. Everything in this zip is an",
      "export from the development repo.", "",
      "Included:")
    for a in agents:
        w(f"- `{a['path']}/` — agent definition")
    for t in m.get("tools") or []:
        n = len(t.get("names") or [])
        w(f"- `{t['path']}` — Python tool{'s' if n != 1 else ''} ({n} tool{'s' if n != 1 else ''})")
    for k in kbs:
        w(f"- `{k['path']}/` — knowledge base definition and its documents")
    for f in flows:
        w(f"- `{f['path']}/` — flow ({f['name']})")
    if ev:
        w(f"- `{ev['path']}/` — " + ", ".join(sorted(includes | {'ground_truth.json'})) + " (results not included)")
    if m.get("demo", {}).get("script"):
        w(f"- `{m['demo']['script']}` — human-readable demo script")
    if has_slides:
        w("- `docs/demo/presentation.html` — slide deck (open it in a browser; it needs the neighbouring `scenarios/` folder)")
    w(f"- `scenarios/{sid}/scenario.yaml` — manifest listing every resource of the scenario; the scripts read it",
      "- `scripts/deploy-all.ps1`, `scripts/deploy-all.sh` — deployment",
      "- `scripts/teardown.ps1`, `scripts/teardown.sh` — removal")
    if ev:
        w("- `scripts/smoke_test.py` — sends the scenario's prompts to the deployed agent")
    w("- `scripts/scenario_manifest.py` — helper the scripts above use to read the manifest",
      "- `env.cfg.example` — configuration template",
      "- `requirements.txt` — `ibm-watsonx-orchestrate==2.18.2`", "",
      "**Not included (by design):**",
      "- other demo scenarios of the repository",
      "- `evaluation/*/results/` — large, instance-specific result data",
      "- `env.cfg` and `local/` — secrets", "",
      "---", "",
      "## Prerequisites", "",
      "### 1. Python", "",
      "**Python 3.11 or later**, per the ADK docs (no upper bound is stated there).",
      "This project was developed and deployed on Python 3.14 and deployment worked.",
      "On 3.14 the evaluation framework's `pandas~=2.2.3` pin could not be satisfied",
      "(no pre-built wheel), so the evaluation dependencies were installed by hand.",
      "Whether the evaluation framework installs cleanly on Python 3.11-3.13 was NOT",
      "tested here.  See the ADK docs:",
      "https://developer.watson-orchestrate.ibm.com/getting_started/installing", "",
      "### 2. IBM watsonx Orchestrate ADK CLI", "",
      "Install into your active Python environment:", "",
      "```bash", "pip install ibm-watsonx-orchestrate==2.18.2", "```", "",
      "Verify:", "", "```bash", "orchestrate --version", "```", "",
      "The ADK depends on PyYAML, which the deploy scripts use to read",
      f"`scenarios/{sid}/scenario.yaml`. Run the scripts from the same environment.", "",
      "### 3. Required model" + (" and embedding model" if kbs else ""), "")
    llms = _agent_llms(m)
    if llms:
        uses = "; ".join(f"agent `{a}` uses `{llm}`" for a, llm in llms)
        if kbs:
            w(f"The {uses}. The knowledge base uses the default embedding model "
              "`ibm/slate-125m-english-rtrvr-v2`. Both must be available in your WXO instance.")
        else:
            w(f"The {uses}. It must be available in your WXO instance.")
        first = agents[0]
        w(f"If the LLM is unavailable, edit `{first['path']}/agent.yaml` and replace the `llm:` value",
          "with a model your instance offers.", "")
    w("---", "", "## Configuration", "",
      "1. Copy the example config file and fill in your credentials:", "",
      "   ```bash", "   cp env.cfg.example env.cfg", "   ```", "",
      "2. Edit `env.cfg`:", "",
      "   ```ini",
      "   WXO_API_KEY=<your IBM Cloud API key>",
      "   WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>",
      "   WXO_ENV_NAME=<a short name for your environment, e.g. my-env>",
      "   # Optional: authentication type.  Default is ibm_iam (IBM Cloud IAM).",
      "   # Use mcsp for AWS-hosted WXO instances.",
      "   WXO_ENV_TYPE=ibm_iam",
      "   ```", "",
      "   - `WXO_API_KEY` — IBM Cloud API key with access to your WXO instance.",
      "   - `WXO_URL` — the API base URL for your instance (from the WXO web UI, under",
      "     Settings, not the browser URL).",
      "   - `WXO_ENV_NAME` — any short alphanumeric name; used locally by the CLI.",
      "   - `WXO_ENV_TYPE` — `ibm_iam` (default, IBM Cloud) or `mcsp` (AWS).", "",
      "   **Keep `env.cfg` private.** Never commit it to version control.", "",
      "---", "", "## Deployment", "",
      "### Windows (PowerShell)", "",
      "```powershell",
      '$env:PYTHONUTF8 = "1"   # avoids cp1252 encoding errors on Windows',
      r".\scripts\deploy-all.ps1",
      "```", "",
      "### Linux / macOS (bash)", "",
      "```bash", "bash scripts/deploy-all.sh", "```", "",
      "The script reads `env.cfg`, registers the WXO environment non-interactively,",
      "then imports the resources listed in the manifest in dependency order:",
      "tools → knowledge base → flow → agent → deploy.", "",
      "Re-running is safe: existing resources are updated in place.", "",
      "**Auth expiry:** the remote authentication token expires after **2 hours**.",
      "If you are deploying in multiple sessions or running the demo after a gap,",
      "re-run the deploy script (or just the activate step) before starting.", "",
      "---", "", "## Opening the agent in the chat UI", "",
      "1. Log in to your WXO instance in the browser.",
      f"2. Go to the chat, and in the agent picker select the agent (`{agents[0]['name']}`).",
      f"3. If the agent is not listed: `orchestrate agents deploy --name {agents[0]['name']}`",
      "   and reload the page.  Imported agents start as drafts; the deploy step",
      "   promotes them to live.  The deploy scripts do this automatically.", "",
      "---", "")
    if kbs:
        w("## Knowledge base indexing", "",
          "The knowledge base is embedded and indexed server-side after import. Check it",
          "with `orchestrate knowledge-bases status` and wait until it reads `ready` before",
          "using the agent. (Indexing time was not measured here.)", "",
          "---", "")
    if ev:
        w("## Smoke test (optional)", "",
          "```bash", f"python scripts/smoke_test.py --scenario {sid}", "```", "",
          "Sends the diagnosis-only prompts from `ground_truth.json` (`smoke_prompts`) to the",
          "deployed agent through the ADK run API and prints the tools it called and the start of",
          "its answer. It does not grade the answer: compare it with `ground_truth.json` yourself.",
          "Use `--dry-run` to print the prompts without calling the instance.", "",
          "---", "")
    if has_eval_cfg or has_baseline:
        w("## Running the evaluation (optional)", "",
          "> **Dependency warning:** the evaluation framework",
          "> `ibm-watsonx-orchestrate-evaluation-framework==1.5.2` and its transitive",
          "> dependencies (`agentops`, `langchain`, `fuzzywuzzy`, `portkey-ai`,",
          "> `openinference-*`, `jsonargparse`) are NOT installed automatically.  On",
          "> Python 3.14 the `pandas~=2.2.3` pin cannot be satisfied.  On other Python",
          "> versions you can try (untested here):",
          ">", "> ```bash",
          "> pip install ibm-watsonx-orchestrate-evaluation-framework==1.5.2",
          "> ```", ">",
          "> If pip fails on the pandas pin, use `--no-deps` and install pandas separately:",
          ">", "> ```bash",
          "> pip install --no-deps ibm-watsonx-orchestrate-evaluation-framework==1.5.2",
          "> pip install pandas",
          "> ```", ">",
          "> A clean-instance install of the evaluation framework was not tested in this",
          "> project.  The dependency issue was resolved manually on the development machine.",
          "> Do not assume it installs cleanly.", "")
        if has_eval_cfg:
            w("Once dependencies are installed:", "", "```bash",
              f"orchestrate evaluations evaluate --config {ev['path']}/eval_config.yaml", "```", "",
              "Note: the command exits with code 1 when its output is piped or redirected (a",
              "progress-rendering issue).  The result files are still written to",
              f"`{ev['path']}/results/<timestamp>/`.", "")
        if has_baseline:
            w("The plain-code baseline needs no WXO connection:", "", "```bash",
              f"python {ev['path']}/baseline.py", "```", "")
        w(f"The evaluation results folder (`results/`) was not included in this zip because",
          "it is large and specific to one instance.", "", "---", "")

    w("## Removing everything", "",
      "Use the included teardown scripts to remove the scenario's resources in the correct order",
      "(agents first, then flows, then tools, then knowledge bases):", "",
      "### Windows (PowerShell)", "", "```powershell", '$env:PYTHONUTF8 = "1"',
      r".\scripts\teardown.ps1 -DryRun   # preview -- prints commands, makes no changes",
      r".\scripts\teardown.ps1            # real deletion (see warning below)", "```", "",
      "### Linux / macOS (bash)", "", "```bash",
      "bash scripts/teardown.sh --dry-run   # preview",
      "bash scripts/teardown.sh             # real deletion (see warning below)", "```", "",
      "**IMPORTANT -- real deletion was never tested during development.** The `-DryRun`",
      "/ `--dry-run` output shows the exact CLI commands that would run:", "", "```")
    for step in sm.teardown_plan({sid: m}, sid):
        if step[0] == "agent":
            w(f"orchestrate agents remove --name {step[1]} --kind {step[2]}")
        elif step[0] in ("flow", "tool"):
            w(f"orchestrate tools remove --name {step[1]}")
        else:
            w(f"orchestrate knowledge-bases remove --name {step[1]}")
    w("```", "",
      "The scripts read `env.cfg` and never print secrets. Run `--dry-run` first, then",
      "check `orchestrate agents remove --help`, `orchestrate tools remove --help`, and",
      "`orchestrate knowledge-bases remove --help` for any confirmation-prompt flags",
      "before executing for real (none were found in `--help` output, but interactive",
      "prompts at runtime were not tested).", "",
      "---", "", "## Known issues and honest notes", "",
      "- **A clean-instance install was not tested.** The only tested deploy was a",
      "  re-install over an existing environment (`techzone1`) that already had all",
      "  resources.  Re-import is idempotent (existing resources are updated), but",
      "  first-import on a fresh instance was not verified.",
      "- **The bash deploy script was run only via Git Bash on Windows** and has not",
      "  been tested on native Linux or macOS.")
    if notes_file.is_file():
        w(*notes_file.read_text(encoding="utf-8-sig").rstrip().splitlines())
    w("- **Auth expiry:** the WXO remote token lasts 2 hours.  Re-run the deploy script",
      "  or `orchestrate env activate <env name> --api-key <key>` before the demo.", "")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_zip(m: dict, manifests: dict, version: str) -> tuple[Path, list[str]]:
    sid = m["_dir"]
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    prefix = (m.get("package") or {}).get("zip_prefix") or sid
    zip_path = dist_dir / f"wxo-{prefix}-{version}.zip"

    extra_deny = other_scenarios_deny(manifests, sid)
    pairs, missing = build_allow_list(m)
    if missing:
        raise RuntimeError("manifest lists paths that do not exist: " + ", ".join(missing))
    presentation = trimmed_presentation(sid)

    print(f"Building {zip_path} ...")
    all_entries = [e for _, e in pairs] + (["docs/demo/presentation.html"] if presentation else [])
    install_md = build_install_md(m, all_entries)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("INSTALL.md", install_md)
        print("  + INSTALL.md  (generated)")

        for abs_path, entry_name in pairs:
            # Safety: reject any pair whose entry name would be denied
            for pattern in DENY_PATTERNS + extra_deny:
                if re.search(pattern, entry_name):
                    raise RuntimeError(
                        f"Allow-list/deny-list conflict: "
                        f"'{entry_name}' matches deny pattern /{pattern}/. "
                        f"Fix the manifest."
                    )
            zf.write(abs_path, entry_name)
            print(f"  + {entry_name}")

        if presentation is not None:
            zf.writestr("docs/demo/presentation.html", presentation)
            print("  + docs/demo/presentation.html  (copy without other scenarios' script tags)")

    print(f"\nZip written: {zip_path} ({zip_path.stat().st_size:,} bytes)")
    return zip_path, extra_deny


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the external zip for one scenario.")
    parser.add_argument("--scenario", required=True, help="scenario id (folder under scenarios/)")
    parser.add_argument("--version", default=VERSION_DEFAULT, help="Version string")
    args = parser.parse_args()

    try:
        manifests = sm.load_all()
        if args.scenario not in manifests:
            sys.exit(f"ERROR: unknown scenario '{args.scenario}'. Known: {', '.join(manifests)}")
        problems = sm.validate(manifests, args.scenario)
        if problems:
            print("Manifest problems (fix them first):", file=sys.stderr)
            for p in problems:
                print("  " + p, file=sys.stderr)
            sys.exit(1)
        zip_path, extra_deny = build_zip(manifests[args.scenario], manifests, args.version)
    except (sm.ManifestError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")

    print("\nRunning post-build security check ...")
    violations = check_zip(zip_path, extra_deny)

    if violations:
        print("\n*** SECURITY CHECK FAILED ***", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(f"\nDeleting {zip_path}", file=sys.stderr)
        zip_path.unlink(missing_ok=True)
        sys.exit(1)
    else:
        print("Security check passed. No denied paths or secret patterns found.")
        print(f"\nPackage ready: {zip_path}")


if __name__ == "__main__":
    main()

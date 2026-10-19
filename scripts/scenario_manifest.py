#!/usr/bin/env python3
"""Read scenario manifests (scenarios/<id>/scenario.yaml) for the deploy, teardown
and smoke-test scripts, and validate them.

Usage:
    python scripts/scenario_manifest.py list
    python scripts/scenario_manifest.py deploy-plan   [--scenario ID]
    python scripts/scenario_manifest.py teardown-plan [--scenario ID]
    python scripts/scenario_manifest.py validate      [--scenario ID]

Output of the *-plan commands is tab-separated lines, paths relative to the repo root
with forward slashes:

    deploy-plan:    tool_py<TAB>path
                    tool_openapi<TAB>path
                    tool_pkg<TAB>package_dir<TAB>entry_file<TAB>requirements_file
                    kb<TAB>yaml_file
                    flow<TAB>py_file
                    agent<TAB>agent_yaml<TAB>agent_name
    teardown-plan:  agent<TAB>name<TAB>kind
                    flow<TAB>name
                    tool<TAB>name
                    kb<TAB>name

Without --scenario:
    deploy-plan    uses every scenario whose manifest says status: live
    teardown-plan  uses every scenario (a resource that was never deployed only gives a
                   non-fatal warning when removed)
    validate       checks every scenario

Within a phase the order is: scenarios sorted by id, resources in manifest order. Teardown
reverses the agent order so that an agent listed after its collaborators is removed first.

Needs PyYAML, which ibm-watsonx-orchestrate already depends on (same Python environment).
Only reads files. Never reads env.cfg or local/.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("ERROR: PyYAML is not installed in this Python. Activate the virtual environment "
             "that has ibm-watsonx-orchestrate installed (it depends on PyYAML).")

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = ROOT / "scenarios"
STATUSES = ("live", "soon")
TIERS = ("core", "full")
REQUIRED = ("id", "name", "description", "status")
# @tool, optionally with arguments that do not rename the tool (name= is not supported here)
TOOL_RE = re.compile(r"^@tool(?:\([^)]*\))?\s*\r?\n\s*def (\w+)", re.M)


class ManifestError(Exception):
    pass


def rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all() -> dict:
    """{id: manifest} for every scenarios/*/scenario.yaml, sorted by id."""
    out = {}
    if SCENARIOS_DIR.is_dir():
        for d in sorted(p for p in SCENARIOS_DIR.iterdir() if p.is_dir()):
            f = d / "scenario.yaml"
            if f.is_file():
                m = load_yaml(f)
                if not isinstance(m, dict):
                    raise ManifestError(f"{rel(f)}: not a YAML mapping")
                m["_dir"] = d.name
                out[d.name] = m
    return out


def select(manifests: dict, scenario: str | None, live_only: bool) -> list:
    if scenario:
        if scenario not in manifests:
            raise ManifestError(f"unknown scenario '{scenario}'. Known: {', '.join(manifests) or '(none)'}")
        return [manifests[scenario]]
    chosen = [m for m in manifests.values() if not live_only or m.get("status") == "live"]
    if not chosen:
        raise ManifestError("no scenarios selected (is any manifest status: live?)")
    return chosen


# ---------------------------------------------------------------------------
# Resolving manifest entries to files
# ---------------------------------------------------------------------------

def kb_file(kb: dict) -> Path:
    folder = ROOT / kb["path"]
    if not folder.is_dir():
        raise ManifestError(f"knowledge base '{kb['name']}': folder {kb['path']} not found")
    for y in sorted(folder.glob("*.yaml")):
        data = load_yaml(y)
        if isinstance(data, dict) and data.get("name") == kb["name"]:
            return y
    raise ManifestError(f"knowledge base '{kb['name']}': no *.yaml with that name in {kb['path']}")


def flow_file(fl: dict) -> Path:
    folder = ROOT / fl["path"]
    if not folder.is_dir():
        raise ManifestError(f"flow '{fl['name']}': folder {fl['path']} not found")
    if fl.get("file"):
        f = folder / fl["file"]
        if not f.is_file():
            raise ManifestError(f"flow '{fl['name']}': {rel(f) if f.exists() else fl['path'] + '/' + fl['file']} not found")
        return f
    cands = [p for p in sorted(folder.glob("*.py")) if p.name != "__init__.py"]
    if len(cands) != 1:
        raise ManifestError(f"flow '{fl['name']}': {fl['path']} has {len(cands)} .py files; "
                            f"set 'file:' in the manifest")
    return cands[0]


def agent_file(a: dict) -> Path:
    f = ROOT / a["path"] / "agent.yaml"
    if not f.is_file():
        raise ManifestError(f"agent '{a['name']}': {a['path']}/agent.yaml not found")
    return f


def tool_steps(t: dict) -> tuple:
    p = ROOT / t["path"]
    if p.is_file():
        if p.suffix == ".py":
            return ("tool_py", rel(p))
        if p.suffix in (".yaml", ".yml", ".json"):
            return ("tool_openapi", rel(p))
        raise ManifestError(f"tool path {t['path']}: unsupported file type")
    if p.is_dir():
        if not t.get("entry"):
            raise ManifestError(f"tool package {t['path']}: 'entry' is required")
        entry, req = p / t["entry"], p / "requirements.txt"
        if not entry.is_file():
            raise ManifestError(f"tool package {t['path']}: entry {t['entry']} not found")
        if not req.is_file():
            raise ManifestError(f"tool package {t['path']}: requirements.txt not found")
        return ("tool_pkg", rel(p), rel(entry), rel(req))
    raise ManifestError(f"tool path {t['path']} not found")


# ---------------------------------------------------------------------------
# Cross-scenario checks
# ---------------------------------------------------------------------------

def owned_names(m: dict) -> dict:
    """{kind: [names]} owned by one manifest."""
    return {
        "agent": [a["name"] for a in m.get("agents") or []],
        "tool": [n for t in m.get("tools") or [] for n in t.get("names") or []],
        "flow": [f["name"] for f in m.get("flows") or []],
        "knowledge base": [k["name"] for k in m.get("knowledge_bases") or []],
    }


def owned_paths(m: dict) -> list:
    """Repo-relative paths (files or folders) that belong only to this scenario."""
    sid = m["_dir"]
    paths = [f"scenarios/{sid}", f"docs/demo/scenarios/{sid}.js"]
    paths += [a["path"] for a in m.get("agents") or []]
    paths += [t["path"] for t in m.get("tools") or []]
    paths += [k["path"] for k in m.get("knowledge_bases") or []]
    paths += [f["path"] for f in m.get("flows") or []]
    if (m.get("evaluation") or {}).get("path"):
        paths.append(m["evaluation"]["path"])
    if (m.get("demo") or {}).get("script"):
        paths.append(m["demo"]["script"])
    return paths


def name_clashes(manifests: dict) -> list:
    """Tool, flow, agent and KB names are resources of the whole WXO instance."""
    seen, problems = {}, []
    for sid, m in manifests.items():
        for kind, names in owned_names(m).items():
            for n in names:
                # tools and flows share the tool namespace in WXO (flows are imported as tools)
                ns = "tool" if kind in ("tool", "flow") else kind
                key = (ns, n)
                if key in seen and seen[key] != sid:
                    problems.append(f"{ns} name '{n}' is used by both '{seen[key]}' and '{sid}'")
                seen.setdefault(key, sid)
    return problems


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------

def deploy_plan(manifests: dict, scenario: str | None) -> list:
    clashes = name_clashes(manifests)
    if clashes:
        raise ManifestError("name clash between scenarios:\n  " + "\n  ".join(clashes))
    chosen = select(manifests, scenario, live_only=True)
    steps = {"tool": [], "kb": [], "flow": [], "agent": []}
    for m in chosen:
        for t in m.get("tools") or []:
            steps["tool"].append(tool_steps(t))
        for k in m.get("knowledge_bases") or []:
            steps["kb"].append(("kb", rel(kb_file(k))))
        for f in m.get("flows") or []:
            steps["flow"].append(("flow", rel(flow_file(f))))
        for a in m.get("agents") or []:
            steps["agent"].append(("agent", rel(agent_file(a)), a["name"]))
    return steps["tool"] + steps["kb"] + steps["flow"] + steps["agent"]


def teardown_plan(manifests: dict, scenario: str | None) -> list:
    chosen = select(manifests, scenario, live_only=False)
    agents, flows, tools, kbs = [], [], [], []
    for m in chosen:
        for a in m.get("agents") or []:
            agents.append(("agent", a["name"], a.get("kind", "native")))
        flows += [("flow", f["name"]) for f in m.get("flows") or []]
        tools += [("tool", n) for t in m.get("tools") or [] for n in t.get("names") or []]
        kbs += [("kb", k["name"]) for k in m.get("knowledge_bases") or []]
    return list(reversed(agents)) + flows + tools + kbs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_one(m: dict) -> list:
    sid, errs = m["_dir"], []

    def err(msg):
        errs.append(f"[{sid}] {msg}")

    for k in REQUIRED:
        if not m.get(k):
            err(f"missing required field '{k}'")
    if m.get("id") != sid:
        err(f"id '{m.get('id')}' must equal the folder name '{sid}'")
    if m.get("status") not in STATUSES:
        err(f"status must be one of {STATUSES}")
    ev = m.get("evaluation")
    if ev:
        if ev.get("tier") not in TIERS:
            err(f"evaluation.tier must be one of {TIERS}")
        if not (ROOT / ev["path"] / "ground_truth.json").is_file():
            err(f"{ev['path']}/ground_truth.json not found (the core evaluation tier is required)")
    elif m.get("status") == "live" and sid != "hello-world":
        err("evaluation section missing (ground_truth.json is required for a live scenario)")
    if ev and m.get("status") == "live" and (ROOT / ev["path"] / "ground_truth.json").is_file():
        try:
            gt = json.loads((ROOT / ev["path"] / "ground_truth.json").read_text(encoding="utf-8-sig"))
        except ValueError as e:
            gt = None
            err(f"{ev['path']}/ground_truth.json is not valid JSON: {e}")
        if gt is not None:
            sp = gt.get("smoke_prompts")
            if not (isinstance(sp, list) and sp and all(
                    isinstance(x, dict) and x.get("id") and x.get("prompt") for x in sp)):
                err(f"{ev['path']}/ground_truth.json needs a non-empty 'smoke_prompts' list "
                    f"of {{id, prompt}} objects (used by scripts/smoke_test.py)")
    demo = (m.get("demo") or {}).get("script")
    if m.get("status") == "live" and sid != "hello-world":
        if not demo or not (ROOT / demo).is_file():
            err(f"live scenario needs demo.script that exists (got {demo!r})")
        if not (ROOT / "docs" / "demo" / "scenarios" / f"{sid}.js").is_file():
            err(f"live scenario needs docs/demo/scenarios/{sid}.js")

    own_tools = set()
    for t in m.get("tools") or []:
        own_tools.update(t.get("names") or [])
        try:
            step = tool_steps(t)
        except ManifestError as e:
            err(str(e))
            continue
        if step[0] in ("tool_py", "tool_pkg"):
            src_path = ROOT / (step[1] if step[0] == "tool_py" else step[2])
            found = TOOL_RE.findall(src_path.read_text(encoding="utf-8-sig"))
            if sorted(found) != sorted(t.get("names") or []):
                err(f"@tool functions in {rel(src_path)} {sorted(found)} != manifest names {sorted(t.get('names') or [])}")
        attached = set(t.get("attached") or [])
        if not attached <= set(t.get("names") or []):
            err(f"tool 'attached' not subset of 'names': {sorted(attached - set(t.get('names') or []))}")

    flow_names = set()
    for f in m.get("flows") or []:
        flow_names.add(f["name"])
        try:
            src = flow_file(f).read_text(encoding="utf-8-sig")
            if not re.search(r'name\s*=\s*["\']%s["\']' % re.escape(f["name"]), src):
                err(f"flow name '{f['name']}' not found as name=... in {rel(flow_file(f))}")
        except ManifestError as e:
            err(str(e))

    kb_names = set()
    for k in m.get("knowledge_bases") or []:
        kb_names.add(k["name"])
        try:
            kb_file(k)
        except ManifestError as e:
            err(str(e))

    attached_all = {n for t in m.get("tools") or [] for n in (t.get("attached") or [])}
    unattached = own_tools - attached_all
    for a in m.get("agents") or []:
        try:
            y = load_yaml(agent_file(a))
        except ManifestError as e:
            err(str(e))
            continue
        if y.get("name") != a["name"]:
            err(f"agent yaml name '{y.get('name')}' != manifest '{a['name']}'")
        agent_tools = set(y.get("tools") or [])
        leaked = sorted(agent_tools & unattached)
        if leaked:
            err(f"agent '{a['name']}' lists tools the manifest marks as not attached: {leaked}")
        missing = sorted(attached_all - agent_tools)
        if missing and len(m.get("agents") or []) == 1:
            err(f"agent '{a['name']}' does not list attached tools: {missing}")
        unknown = sorted(agent_tools - own_tools - flow_names)
        if unknown:
            err(f"agent '{a['name']}' lists tools this scenario does not own: {unknown} "
                f"(own: tools + flows; shared tools are not supported)")
        kb_unknown = sorted(set(y.get("knowledge_base") or []) - kb_names)
        if kb_unknown:
            err(f"agent '{a['name']}' lists knowledge bases this scenario does not own: {kb_unknown}")
    return errs


def validate(manifests: dict, scenario: str | None) -> list:
    chosen = select(manifests, scenario, live_only=False)
    errs = []
    for m in chosen:
        errs += validate_one(m)
    errs += name_clashes(manifests)
    return errs


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("list", "deploy-plan", "teardown-plan", "validate"))
    ap.add_argument("--scenario", default=None)
    args = ap.parse_args()
    try:
        manifests = load_all()
        if args.command == "list":
            for m in manifests.values():
                print(f"{m['_dir']}\t{m.get('status')}\t{m.get('name')}")
        elif args.command == "deploy-plan":
            for s in deploy_plan(manifests, args.scenario):
                print("\t".join(s))
        elif args.command == "teardown-plan":
            for s in teardown_plan(manifests, args.scenario):
                print("\t".join(s))
        else:
            errs = validate(manifests, args.scenario)
            for e in errs:
                print("PROBLEM: " + e)
            print("OK" if not errs else f"{len(errs)} problem(s)")
            return 1 if errs else 0
    except ManifestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

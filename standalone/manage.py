#!/usr/bin/env python3
"""Deploy or undeploy standalone agents to/from a WXO instance.

Standalone agents live in subdirectories of this directory. Every subdirectory that
contains an agent.yaml file is treated as a standalone agent. No manifest or scenario
registration is needed — just add a subdirectory and run this script.

Knowledge bases are NOT managed by this script. KBs used by standalone agents are
typically shared with scenario deployments (managed by scripts/deploy-all.ps1 /
teardown.ps1). Import or remove KBs manually, or via those scripts. See each
agent's README.md for the exact KB dependency commands.

Usage:
    python standalone/manage.py list
    python standalone/manage.py deploy
    python standalone/manage.py deploy --agent travel_rules_qa
    python standalone/manage.py deploy --dry-run
    python standalone/manage.py undeploy
    python standalone/manage.py undeploy --agent travel_rules_qa
    python standalone/manage.py undeploy --dry-run

Prerequisites:
    - Copy env.cfg.example to env.cfg in the repo root and fill in WXO_API_KEY,
      WXO_URL, and WXO_ENV_NAME.
    - Activate the virtual environment that has ibm-watsonx-orchestrate installed
      (the 'orchestrate' CLI must be on PATH and PyYAML must be importable).
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ── Encoding: same fix as deploy-all.ps1 / teardown.ps1 ────────────────────
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    sys.exit(
        "ERROR: PyYAML is not installed. Activate the virtual environment that has "
        "ibm-watsonx-orchestrate installed (it depends on PyYAML)."
    )

STANDALONE_DIR = Path(__file__).resolve().parent
ROOT = STANDALONE_DIR.parent


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_agents() -> list[dict]:
    """Return a list of {name, yaml_path, dir} for every agent.yaml found."""
    agents = []
    for subdir in sorted(p for p in STANDALONE_DIR.iterdir() if p.is_dir()):
        yaml_path = subdir / "agent.yaml"
        if not yaml_path.is_file():
            continue
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or not data.get("name"):
            print(f"WARNING: {yaml_path.relative_to(ROOT)} has no 'name' field — skipping",
                  file=sys.stderr)
            continue
        agents.append({
            "name": data["name"],
            "yaml_path": yaml_path,
            "dir": subdir,
        })
    return agents


def select_agents(agents: list[dict], agent_filter: str | None) -> list[dict]:
    if agent_filter is None:
        return agents
    matched = [a for a in agents if a["name"] == agent_filter]
    if not matched:
        known = ", ".join(a["name"] for a in agents) or "(none found)"
        sys.exit(f"ERROR: agent '{agent_filter}' not found. Known: {known}")
    return matched


# ---------------------------------------------------------------------------
# env.cfg loading
# ---------------------------------------------------------------------------

def load_env_cfg() -> dict:
    """Parse env.cfg from the repo root. Returns {key: value}."""
    cfg_path = ROOT / "env.cfg"
    if not cfg_path.is_file():
        sys.exit(
            f"ERROR: env.cfg not found at '{cfg_path}'. "
            "Copy env.cfg.example and fill in your credentials."
        )
    env = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        idx = line.index("=") if "=" in line else -1
        if idx < 1:
            continue
        env[line[:idx].strip()] = line[idx + 1:].strip()
    for required in ("WXO_API_KEY", "WXO_URL", "WXO_ENV_NAME"):
        if not env.get(required):
            sys.exit(f"ERROR: env.cfg must define {required}.")
    return env


# ---------------------------------------------------------------------------
# orchestrate CLI helpers
# ---------------------------------------------------------------------------

def _check_orchestrate():
    if not shutil.which("orchestrate"):
        sys.exit(
            "ERROR: 'orchestrate' not found on PATH. "
            "Activate the virtual environment that has ibm-watsonx-orchestrate installed."
        )


def run_orchestrate(args: list[str], *, dry_run: bool, description: str,
                    fatal: bool = True) -> bool:
    """Run `orchestrate <args>`. Returns True on success.

    dry_run=True  → print the command, do nothing.
    fatal=True    → exit non-zero on failure.
    fatal=False   → print a warning and return False on failure.
    """
    if dry_run:
        print(f"  [DRY-RUN] orchestrate {' '.join(args)}")
        return True
    print(f"  orchestrate {' '.join(args)}")
    result = subprocess.run(["orchestrate"] + args)
    if result.returncode != 0:
        msg = f"WARNING: orchestrate {' '.join(args)} exited with code {result.returncode}"
        if fatal:
            print(f"ERROR: {msg.removeprefix('WARNING: ')}. Aborting.", file=sys.stderr)
            sys.exit(result.returncode)
        else:
            print(msg, file=sys.stderr)
            return False
    return True


def activate_environment(env: dict, *, dry_run: bool):
    """Register and activate the WXO environment."""
    env_name = env["WXO_ENV_NAME"]
    url = env["WXO_URL"]
    env_type = env.get("WXO_ENV_TYPE") or "ibm_iam"
    api_key = env["WXO_API_KEY"]

    print(f"\n[setup] Registering and activating environment '{env_name}' ...")

    if dry_run:
        print(f"  [DRY-RUN] orchestrate env add -n {env_name} -u <url> --type {env_type}")
        print(f"  [DRY-RUN] orchestrate env activate {env_name} --api-key ***")
        return

    # 'env add' asks "update the environment?" when the name already exists; pipe Y.
    add = subprocess.run(
        ["orchestrate", "env", "add", "-n", env_name, "-u", url, "--type", env_type],
        input="Y\n",
        text=True,
    )
    if add.returncode != 0:
        print(
            f"WARNING: env add exited {add.returncode} "
            "(may be expected if the environment already exists)",
            file=sys.stderr,
        )

    activate = subprocess.run(
        ["orchestrate", "env", "activate", env_name, "--api-key", api_key]
    )
    if activate.returncode != 0:
        print(
            f"ERROR: env activate failed (exit {activate.returncode}). Cannot proceed.",
            file=sys.stderr,
        )
        sys.exit(activate.returncode)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_list(agents: list[dict], _args):
    if not agents:
        print("(no standalone agents found)")
        return
    print(f"{'AGENT NAME':<30}  PATH")
    print("-" * 60)
    for a in agents:
        rel = a["yaml_path"].relative_to(ROOT)
        print(f"{a['name']:<30}  {rel}")


def cmd_deploy(agents: list[dict], args):
    selected = select_agents(agents, args.agent)
    if not selected:
        print("No agents to deploy.")
        return

    env = {} if args.dry_run else load_env_cfg()
    _check_orchestrate()

    if not args.dry_run:
        activate_environment(env, dry_run=False)
    else:
        print("\n[DRY-RUN] Skipping environment activation.")

    print(f"\nDeploying {len(selected)} agent(s)...")
    for a in selected:
        print(f"\n  -> {a['name']}  ({a['yaml_path'].relative_to(ROOT)})")
        rel_yaml = str(a["yaml_path"].relative_to(ROOT))

        # import (fatal — a failed import means the agent isn't there)
        run_orchestrate(
            ["agents", "import", "--file", str(a["yaml_path"])],
            dry_run=args.dry_run,
            description=f"agents import --file {rel_yaml}",
            fatal=True,
        )

        # deploy (non-fatal — Developer Edition only supports draft agents)
        ok = run_orchestrate(
            ["agents", "deploy", "--name", a["name"]],
            dry_run=args.dry_run,
            description=f"agents deploy --name {a['name']}",
            fatal=False,
        )
        if not ok:
            print(
                f"  NOTE: '{a['name']}' exists as a draft. "
                "It may not appear in the chat UI (Developer Edition limitation).",
                file=sys.stderr,
            )

    print("\n=== Deploy complete ===" if not args.dry_run else "\n=== Dry run complete ===")


def cmd_undeploy(agents: list[dict], args):
    selected = select_agents(agents, args.agent)
    if not selected:
        print("No agents to undeploy.")
        return

    env = {} if args.dry_run else load_env_cfg()
    _check_orchestrate()

    if not args.dry_run:
        activate_environment(env, dry_run=False)
    else:
        print("\n[DRY-RUN] Skipping environment activation.")

    print(f"\nUndeploying {len(selected)} agent(s)...")
    for a in selected:
        print(f"\n  -> {a['name']}")
        # non-fatal: a resource that was never deployed only gives a warning
        run_orchestrate(
            ["agents", "remove", "--name", a["name"], "--kind", "native"],
            dry_run=args.dry_run,
            description=f"agents remove --name {a['name']} --kind native",
            fatal=False,
        )

    if args.dry_run:
        print("\n=== Dry run complete ===")
    else:
        print("\n=== Undeploy complete ===")
        print(
            "NOTE: Knowledge bases were NOT removed. "
            "Remove them manually if they are no longer needed and not shared with a scenario."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "command",
        choices=("list", "deploy", "undeploy"),
        help="list: show discovered agents; deploy: import and deploy; undeploy: remove",
    )
    ap.add_argument(
        "--agent",
        default=None,
        metavar="NAME",
        help="act on one named agent only (default: all discovered agents)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print every orchestrate command without executing it",
    )
    args = ap.parse_args()

    agents = discover_agents()

    if args.command == "list":
        cmd_list(agents, args)
    elif args.command == "deploy":
        cmd_deploy(agents, args)
    elif args.command == "undeploy":
        cmd_undeploy(agents, args)


if __name__ == "__main__":
    main()

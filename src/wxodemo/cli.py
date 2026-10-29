"""Command-line interface for wxodemo."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from wxodemo import __version__
from wxodemo.adk import AdkError, login
from wxodemo.api_eval import run_test_upload
from wxodemo.chats import ExportError, run_export_chats
from wxodemo.config import UsageError, load_config, log_path, repo_root
from wxodemo.deploy import run_deploy, run_status, run_undeploy
from wxodemo.discovery import Target, all_targets, resolve_targets
from wxodemo.doctor import in_virtualenv, run_doctor
from wxodemo.evaluate import run_eval
from wxodemo.logging_setup import fail, get_logger, ok, plain, register_secret, setup_logging, warn
from wxodemo.manifest import ManifestError
from wxodemo.scaffold import run_new_scenario
from wxodemo.smoke import run_smoke
from wxodemo.validate import run_validate


def cmd_setup(args: argparse.Namespace) -> int:
    """pip install -r requirements.txt with the interpreter running this tool, then doctor."""
    requirements = repo_root() / "requirements.txt"
    if not requirements.is_file():
        fail(f"requirements.txt not found at {requirements}")
        return 1

    if not in_virtualenv():
        warn("Not running in a virtual environment. Continuing, but a venv is recommended.")

    command = [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
    if args.dry_run:
        plain(f"[dry-run] would run: {' '.join(command)}")
        return 0

    plain("Installing dependencies (this can take a minute) ...")
    proc = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    get_logger().debug("pip exit %d\n%s\n%s", proc.returncode, proc.stdout, proc.stderr)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr.strip() or proc.stdout.strip()).splitlines()[-5:])
        fail(f"pip install failed (exit {proc.returncode}):\n{tail}")
        return 1
    ok("Dependencies installed")
    return run_doctor()


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor()


def cmd_login(args: argparse.Namespace) -> int:
    """Register the environment from env.cfg and activate it. Safe to repeat."""
    cfg = load_config()
    register_secret(cfg.api_key)

    if args.dry_run:
        plain(f"[dry-run] would register '{cfg.env_name}' ({cfg.url}, type {cfg.env_type})")
        plain(f"[dry-run] would activate '{cfg.env_name}' with the API key from env.cfg")
        return 0

    login(cfg)
    ok(f"Environment '{cfg.env_name}' is active")
    return 0


def _select(args: argparse.Namespace, *, live_only: bool = False):
    """Resolve the target names / --all / --kind arguments shared by deploy-like commands."""
    root = repo_root()
    targets, problems = all_targets(root)
    for problem in problems:
        warn(problem)
    # Allow "all" as a magic positional name, equivalent to --all
    names = [n for n in args.targets if n != "all"]
    select_all = args.all or len(names) < len(args.targets)
    chosen = resolve_targets(
        targets, names, select_all=select_all, kind=args.kind, live_only=live_only
    )
    return root, chosen


def _config_for(args: argparse.Namespace):
    """env.cfg is required for real runs; a dry run previews without credentials."""
    if args.dry_run:
        return None
    cfg = load_config()
    register_secret(cfg.api_key)
    return cfg


def cmd_deploy(args: argparse.Namespace) -> int:
    root, chosen = _select(args, live_only=True)
    return run_deploy(chosen, _config_for(args), root, args.dry_run)


def cmd_undeploy(args: argparse.Namespace) -> int:
    root, chosen = _select(args)
    return run_undeploy(chosen, _config_for(args), root, args.dry_run, args.yes)


def cmd_status(args: argparse.Namespace) -> int:
    _, chosen = _select(args)
    cfg = load_config()
    register_secret(cfg.api_key)
    return run_status(chosen, cfg)


def _one_line(text: str, limit: int = 70) -> str:
    """First sentence of `text`, cut to `limit` characters."""
    first = text.split(". ")[0].rstrip(".")
    return first if len(first) <= limit else first[: limit - 3].rstrip() + "..."


def cmd_list(args: argparse.Namespace) -> int:
    """Show every scenario and standalone agent that deploy/undeploy/validate can address."""
    targets, problems = all_targets(repo_root())
    if args.kind:
        targets = [t for t in targets if t.kind == args.kind]
    for problem in problems:
        warn(problem)
    if not targets:
        plain("Nothing found.")
        return 0

    width = max(len(t.name) for t in targets)
    plain(f"{'NAME':<{width}}  {'KIND':<10}  {'STATUS':<6}  DESCRIPTION")
    for t in targets:
        plain(f"{t.name:<{width}}  {t.kind:<10}  {t.status:<6}  {_one_line(t.summary)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check scenario manifests and demo scripts. Standalone agents have nothing to validate."""
    root = repo_root()
    targets, problems = all_targets(root)
    for problem in problems:
        warn(problem)
    chosen = resolve_targets(targets, args.targets, select_all=not args.targets, kind=args.kind)
    scenarios = [t.scenario for t in chosen if t.scenario is not None]
    if not scenarios:
        plain("No scenarios selected. Standalone agents have no manifest to validate.")
        return 1 if problems else 0
    return run_validate(root, scenarios, problems)


def _one_scenario(name: str) -> tuple[Path, Target]:
    """Exactly one scenario by id, for commands that act on a single scenario."""
    root = repo_root()
    targets, problems = all_targets(root)
    for problem in problems:
        warn(problem)
    chosen = resolve_targets(targets, [name], kind="scenario")
    return root, chosen[0]


def cmd_smoke(args: argparse.Namespace) -> int:
    _, target = _one_scenario(args.scenario)
    return run_smoke(target.scenario, _config_for(args), args.only, args.dry_run)


def cmd_eval(args: argparse.Namespace) -> int:
    root, target = _one_scenario(args.scenario)
    return run_eval(root, target.scenario, _config_for(args), args.dry_run)


def cmd_test_upload(args: argparse.Namespace) -> int:
    root = repo_root()
    targets, problems = all_targets(root)
    for problem in problems:
        warn(problem)
    chosen = resolve_targets(targets, [args.target], kind=args.kind)
    return run_test_upload(
        root, chosen[0], _config_for(args), evaluate=args.eval, dry_run=args.dry_run
    )


def cmd_export_chats(args: argparse.Namespace) -> int:
    output = Path(args.output_dir) if args.output_dir else repo_root() / "export"
    return run_export_chats(
        _config_for(args),
        output_dir=output,
        agent=args.agent,
        last=args.last,
        raw_traces=args.raw_traces,
        workers=args.workers,
        dry_run=args.dry_run,
    )


def cmd_new_scenario(args: argparse.Namespace) -> int:
    return run_new_scenario(
        repo_root(), args.id, args.name, args.description, args.agent_name, args.dry_run
    )


def cmd_logs(args: argparse.Namespace) -> int:
    path = log_path()
    plain(f"Log file: {path}")
    if not path.is_file():
        plain("No log yet. Run any wxodemo command first.")
        return 0
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-args.tail :]:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wxodemo",
        description="Set up, deploy and manage the watsonx Orchestrate demos in this repo.",
    )
    parser.add_argument("--version", action="version", version=f"wxodemo {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output on screen")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser("setup", help="install requirements.txt with this Python, then run doctor")
    p.add_argument("--dry-run", action="store_true", help="show what would run")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("doctor", help="check Python, packages, orchestrate CLI and env.cfg")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser(
        "login", aliases=["activate"], help="register and activate the WXO environment from env.cfg"
    )
    p.add_argument("--dry-run", action="store_true", help="show what would run")
    p.set_defaults(func=cmd_login)

    def add_targets(p: argparse.ArgumentParser, verb: str) -> None:
        p.add_argument("targets", nargs="*", metavar="name", help=f"scenario or agent to {verb}")
        p.add_argument("--all", action="store_true", help=f"{verb} everything (see --kind)")
        p.add_argument(
            "--kind",
            choices=("scenario", "standalone"),
            help="limit --all to one kind, or pick one when a name matches both",
        )

    p = sub.add_parser("deploy", help="deploy scenarios and/or standalone agents")
    add_targets(p, "deploy")
    p.add_argument("--dry-run", action="store_true", help="show the commands without running them")
    p.set_defaults(func=cmd_deploy)

    p = sub.add_parser("undeploy", help="remove deployed scenarios and/or standalone agents")
    add_targets(p, "remove")
    p.add_argument("--dry-run", action="store_true", help="show the commands without running them")
    p.add_argument("-y", "--yes", action="store_true", help="do not ask for confirmation")
    p.set_defaults(func=cmd_undeploy)

    p = sub.add_parser("status", help="compare the repo with what is deployed in WXO")
    add_targets(p, "check")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="list scenarios and standalone agents")
    p.add_argument("--kind", choices=("scenario", "standalone"), help="show only one kind")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser(
        "validate", help="check scenario manifests and demo scripts (all, or the named ones)"
    )
    p.add_argument("targets", nargs="*", metavar="name", help="scenario ids (default: all)")
    p.add_argument("--kind", choices=("scenario", "standalone"), help="limit to one kind")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("smoke", help="send a scenario's smoke prompts to its deployed agent")
    p.add_argument("scenario", help="scenario id")
    p.add_argument(
        "--only", action="append", default=[], metavar="ID", help="run one prompt id (repeatable)"
    )
    p.add_argument("--dry-run", action="store_true", help="show the prompts; send nothing")
    p.set_defaults(func=cmd_smoke)

    p = sub.add_parser("eval", help="run the ADK evaluation for a scenario")
    p.add_argument("scenario", help="scenario id")
    p.add_argument("--dry-run", action="store_true", help="show the command; run nothing")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser(
        "test-upload",
        help="upload test cases to WXO Tests tab and optionally trigger evaluation in UI",
    )
    p.add_argument("target", help="scenario or agent name")
    p.add_argument("--kind", choices=("scenario", "standalone"), help="target kind")
    p.add_argument(
        "--eval", action="store_true", help="also trigger evaluation in WXO Evaluations tab"
    )
    p.add_argument("--dry-run", action="store_true", help="preview prompts without uploading")
    p.set_defaults(func=cmd_test_upload)

    p = sub.add_parser("export-chats", help="export agent conversations to Markdown and JSON")
    p.add_argument("--agent", help="only this agent (name or id)")
    p.add_argument(
        "--last", default="7d", help="window for Web UI chats: 90m, 24h, 7d (default 7d)"
    )
    p.add_argument("--raw-traces", action="store_true", help="also save raw trace JSON")
    p.add_argument("--workers", type=int, default=10, help="parallel downloads (default 10)")
    p.add_argument("--output-dir", help="base folder (default: export/ in the repo)")
    p.add_argument("--dry-run", action="store_true", help="show what would be exported")
    p.set_defaults(func=cmd_export_chats)

    p = sub.add_parser("new-scenario", help="scaffold a new demo scenario")
    p.add_argument("id", help="kebab-case scenario id, for example customer-returns")
    p.add_argument("--name", required=True, help='display name, for example "Customer Returns"')
    p.add_argument("--description", required=True, help="one line for the sidebar")
    p.add_argument("--agent-name", help="WXO agent name (default: the id with underscores)")
    p.add_argument("--dry-run", action="store_true", help="show what would be created")
    p.set_defaults(func=cmd_new_scenario)

    p = sub.add_parser("logs", help="show the log file path and its last lines")
    p.add_argument("-n", "--tail", type=int, default=20, help="number of lines (default 20)")
    p.set_defaults(func=cmd_logs)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Exit codes: 0 ok, 1 command failed, 2 configuration or usage error."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0

    logger = setup_logging(log_path(), verbose=args.verbose)
    raw_args = argv if argv is not None else sys.argv[1:]
    logger.debug("wxodemo %s: %s", __version__, " ".join(raw_args))

    try:
        return args.func(args)
    except UsageError as exc:
        fail(str(exc))
        return 2
    except (ManifestError, ExportError) as exc:
        fail(str(exc))
        return 1
    except AdkError as exc:
        fail(str(exc))
        plain(f"Details: {log_path()}")
        return exc.returncode if exc.returncode == 127 else 1
    except KeyboardInterrupt:
        plain("Cancelled.")
        return 130
    except Exception as exc:  # noqa: BLE001 - last-resort handler; full trace goes to the log
        # DEBUG: the console shows INFO and up (so no traceback on screen), the log file keeps it.
        logger.debug("unexpected error", exc_info=True)
        fail(f"Unexpected error: {exc}")
        plain(f"Details: {log_path()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

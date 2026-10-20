"""`wxodemo doctor`: check that this machine and repo are ready to use."""

from __future__ import annotations

import importlib.metadata
import sys

from wxodemo.adk import active_env_lines, find_orchestrate
from wxodemo.config import REQUIRED_KEYS, ConfigError, load_config
from wxodemo.logging_setup import fail, info, ok, plain, register_secret, warn

MIN_PYTHON = (3, 11)


def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_doctor() -> int:
    """Run all checks. Returns 0 if ready, 2 if env.cfg is the only problem, else 1."""
    failures = 0
    plain("wxodemo doctor")

    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info >= MIN_PYTHON:
        ok(f"Python {version} ({sys.executable})")
    else:
        fail(f"Python {version}; {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required")
        failures += 1

    if in_virtualenv():
        ok("Virtual environment in use")
    else:
        info("No virtual environment (optional, but recommended)")

    for package, required in (("ibm-watsonx-orchestrate", True), ("PyYAML", False)):
        installed = _package_version(package)
        if installed:
            ok(f"{package} {installed}")
        elif required:
            fail(f"{package} is not installed for this Python. Run: python wxodemo.py setup")
            failures += 1
        else:
            warn(f"{package} is not installed (needed for scenarios). Run: python wxodemo.py setup")

    exe = find_orchestrate()
    if exe:
        ok(f"orchestrate CLI found ({exe})")
    else:
        fail("orchestrate CLI not found. Run: python wxodemo.py setup")
        failures += 1

    config_problem = False
    cfg = None
    try:
        cfg = load_config()
    except ConfigError as exc:
        fail(f"env.cfg: {exc}")
        config_problem = True
    else:
        register_secret(cfg.api_key)
        ok(f"env.cfg is complete ({', '.join(REQUIRED_KEYS)})")

    if exe:
        active = active_env_lines()
        if cfg and any(cfg.env_name in line for line in active):
            ok(f"WXO environment '{cfg.env_name}' is active")
        elif active:
            info(f"Active WXO environment: {active[0]} (run 'python wxodemo.py login' to switch)")
        else:
            info("No active WXO environment yet. Run: python wxodemo.py login")

    if failures:
        return 1
    return 2 if config_problem else 0

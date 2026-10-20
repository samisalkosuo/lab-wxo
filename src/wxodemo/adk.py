"""Locate and run the `orchestrate` CLI. Standard library only."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from wxodemo.config import Config
from wxodemo.logging_setup import get_logger, mask


class AdkError(Exception):
    """An orchestrate command failed."""

    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


class AdkNotFoundError(AdkError):
    """The orchestrate executable could not be found."""


def find_orchestrate() -> Path | None:
    """Find `orchestrate` next to the running interpreter first, then on PATH.

    Looking next to sys.executable works for a venv, uv, conda or a system install alike,
    without the tool knowing or caring which one it is.
    """
    py_dir = Path(sys.executable).parent
    for name in ("orchestrate.exe", "orchestrate.cmd", "orchestrate"):
        candidate = py_dir / name
        if candidate.is_file():
            return candidate
    found = shutil.which("orchestrate")
    return Path(found) if found else None


def run_orchestrate(
    args: list[str],
    *,
    input_text: str | None = None,
    check: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `orchestrate <args>`, log the full exchange (secrets masked), return the result.

    Raises AdkNotFoundError if the CLI is missing and, when `check` is true, AdkError on a
    non-zero exit code.
    """
    log = get_logger()
    exe = find_orchestrate()
    if exe is None:
        raise AdkNotFoundError(
            "The 'orchestrate' CLI was not found for this Python "
            f"({sys.executable}).\n"
            "Install it with: python wxodemo.py setup   (or: pip install -r requirements.txt)",
            returncode=127,
        )

    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    shown = mask("orchestrate " + " ".join(args))
    log.debug("run: %s", shown)

    started = time.perf_counter()
    proc = subprocess.run(
        [str(exe), *args],
        input=input_text,
        # Never inherit our stdin: a CLI that unexpectedly prompts must fail, not hang.
        stdin=None if input_text is not None else subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=cwd,
        check=False,
    )
    elapsed = time.perf_counter() - started
    log.debug("exit %d in %.1fs: %s", proc.returncode, elapsed, shown)
    if proc.stdout.strip():
        log.debug("stdout:\n%s", proc.stdout.strip())
    if proc.stderr.strip():
        log.debug("stderr:\n%s", proc.stderr.strip())

    if check and proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip() or "no output").splitlines()
        tail = "\n".join(detail[-5:])
        raise AdkError(f"{shown} failed (exit {proc.returncode}):\n{mask(tail)}", proc.returncode)
    return proc


def login(cfg: Config) -> None:
    """Register the environment from env.cfg and activate it. Safe to repeat."""
    # 'env add' asks whether to update an existing environment; answering Y keeps this idempotent.
    run_orchestrate(
        ["env", "add", "-n", cfg.env_name, "-u", cfg.url, "--type", cfg.env_type],
        input_text="Y\n",
    )
    run_orchestrate(["env", "activate", cfg.env_name, "--api-key", cfg.api_key])


def active_env_lines() -> list[str]:
    """Lines of `orchestrate env list` marked as active. Empty if none or on any failure."""
    try:
        proc = run_orchestrate(["env", "list"], check=False)
    except AdkError:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if "(active)" in line.lower()]

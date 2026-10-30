"""Run the ADK evaluation framework for a scenario or standalone agent: `orchestrate evaluations evaluate`.

The evaluation extras (ibm-watsonx-orchestrate-evaluation-framework) are optional and are not in
requirements.txt; on Python 3.14 its pandas pin cannot be installed. See docs/wxodemo.md.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from wxodemo.adk import AdkError, AdkNotFoundError, find_orchestrate, login
from wxodemo.config import Config, UsageError
from wxodemo.discovery import Target
from wxodemo.logging_setup import fail, get_logger, mask, ok, plain
from wxodemo.manifest import ManifestError, rel

CONFIG_NAME = "eval_config.yaml"


def eval_config_path(root: Path, target: Target) -> Path:
    """The eval_config.yaml of a scenario (evaluation/<id>/) or standalone agent (its folder)."""
    if target.agent is not None:
        config = target.agent.dir / CONFIG_NAME
        if not config.is_file():
            raise UsageError(
                f"{rel(root, config)} not found. Standalone agent '{target.name}' has no "
                f"automated evaluation configured."
            )
        return config

    scenario = target.scenario
    evaluation = (scenario.get("evaluation") or {}).get("path")
    if not evaluation:
        raise ManifestError(f"scenario '{scenario.id}' has no evaluation.path in its manifest")
    config = root / evaluation / CONFIG_NAME
    if not config.is_file():
        raise UsageError(
            f"{evaluation}/{CONFIG_NAME} not found. '{scenario.id}' has no automated evaluation "
            f"configured (only ground_truth.json for the smoke test)."
        )
    return config


def run_eval(root: Path, target: Target, cfg: Config | None, dry_run: bool) -> int:
    """Log in, then run the evaluation attached to the terminal. Exit code is the CLI's."""
    config = eval_config_path(root, target)
    args = ["evaluations", "evaluate", "--config", rel(root, config)]
    plain(f"Evaluating '{target.name}' with {rel(root, config)}")
    if dry_run:
        plain(f"[dry-run] would run: orchestrate {' '.join(args)}")
        return 0

    exe = find_orchestrate()
    if exe is None:
        raise AdkNotFoundError(
            "The 'orchestrate' CLI was not found for this Python. Run: python wxodemo.py setup",
            returncode=127,
        )
    login(cfg)  # refresh the 2-hour token before a long run
    ok(f"Logged in to '{cfg.env_name}'")

    # The framework renders live progress and exits 1 when its output is piped, so it inherits
    # the terminal instead of being captured. Results are written under the config's output_dir.
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    command = [str(exe), *args]
    get_logger().debug("run: %s", mask(" ".join(command)))
    plain("This calls the LLM many times and can take several minutes ...")
    proc = subprocess.run(command, cwd=root, env=env, stdin=subprocess.DEVNULL, check=False)
    get_logger().debug("exit %d: orchestrate %s", proc.returncode, " ".join(args))

    if proc.returncode != 0:
        fail(f"Evaluation exited with code {proc.returncode}.")
        plain(
            "If it complains about a missing module, the optional evaluation framework is not "
            "installed (see docs/wxodemo.md, section Evaluation)."
        )
        raise AdkError("evaluation failed", proc.returncode)
    ok("Evaluation finished. Results are under the output_dir named in the config.")
    return 0

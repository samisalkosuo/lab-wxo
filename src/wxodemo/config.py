"""Repo paths and env.cfg loading/validation. Standard library only. Never prompts."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_KEYS = ("WXO_API_KEY", "WXO_URL", "WXO_ENV_NAME")
DEFAULT_ENV_TYPE = "ibm_iam"

_KEY_HELP = {
    "WXO_API_KEY": "your watsonx Orchestrate API key (Settings > API details in the UI)",
    "WXO_URL": "the service instance URL (https://api.<region>.watson-orchestrate.cloud.ibm.com/"
    "instances/<instance-id>)",
    "WXO_ENV_NAME": "a name for the environment in the ADK, for example my-env",
}


class UsageError(Exception):
    """The command cannot run as requested (bad target, missing dependency). Exit code 2."""


class ConfigError(UsageError):
    """env.cfg is missing or incomplete. Maps to exit code 2."""


def repo_root() -> Path:
    """Repo root: the nearest parent of this file holding pyproject.toml, else the CWD."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "requirements.txt").is_file():
            return parent
    return Path.cwd()


def env_cfg_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "env.cfg"


def log_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "local" / "wxodemo.log"


@dataclass(frozen=True)
class Config:
    api_key: str
    url: str
    env_name: str
    env_type: str = DEFAULT_ENV_TYPE


def parse_env_text(text: str) -> dict[str, str]:
    """Parse KEY=VALUE lines. Blank lines and # comments are skipped; split on the first '='."""
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _is_placeholder(key: str, value: str) -> bool:
    if key == "WXO_API_KEY":
        return value == "your-api-key-here"
    if key == "WXO_URL":
        return "<" in value or ">" in value
    return False


def _copy_hint() -> str:
    command = "copy" if sys.platform == "win32" else "cp"
    return f"{command} env.cfg.example env.cfg"


def load_config(path: Path | None = None) -> Config:
    """Load and validate env.cfg. Raises ConfigError with an actionable message."""
    path = path or env_cfg_path()
    if not path.is_file():
        raise ConfigError(
            f"env.cfg not found at {path}\n"
            f"Create it from the template and fill in the values:\n"
            f"  {_copy_hint()}\n"
            f"Required keys: {', '.join(REQUIRED_KEYS)}\n"
            f"Optional key:  WXO_ENV_TYPE (default {DEFAULT_ENV_TYPE}; use mcsp for AWS-hosted "
            f"instances)"
        )

    values = parse_env_text(path.read_text(encoding="utf-8-sig"))
    problems = [
        key for key in REQUIRED_KEYS if not values.get(key) or _is_placeholder(key, values[key])
    ]
    if problems:
        details = "\n".join(f"  {key}: set {_KEY_HELP[key]}" for key in problems)
        raise ConfigError(
            f"env.cfg at {path} is missing values for: {', '.join(problems)}\n"
            f"{details}\n"
            f"See env.cfg.example for the expected format."
        )

    return Config(
        api_key=values["WXO_API_KEY"],
        url=values["WXO_URL"],
        env_name=values["WXO_ENV_NAME"],
        env_type=values.get("WXO_ENV_TYPE") or DEFAULT_ENV_TYPE,
    )

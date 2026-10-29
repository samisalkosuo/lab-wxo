"""WXO Traffic Generator.

Periodically calls watsonx Orchestrate agents via the REST API to generate usage data.
One call fires per CALL_INTERVAL_MINUTES window, at a random second within that window.

Environment variables:
  WXO_API_KEY            required  IBM Cloud or MCSP API key
  WXO_URL                required  https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>
  WXO_ENV_TYPE           optional  ibm_iam (default) or mcsp
  CALL_INTERVAL_MINUTES  optional  window size in minutes, default 1
  AGENT_FILTER           optional  comma-separated agent names to restrict the pool
  WXO_ENVIRONMENT        optional  live (default) or draft; runs are sent to this agent environment.
                                   The Home dashboard counts live usage only.

Stdlib only — no third-party packages required.
"""

from __future__ import annotations

import http.client
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
MCSP_URL = "https://iam.platform.saas.ibm.com/saas/v1/auth/token"
USER_AGENT = "wxo-traffic-gen/1.0"
TOKEN_TTL = 50 * 60        # re-fetch token after 50 minutes (expires at ~60 min)
POLL_INTERVAL = 5          # seconds between run-status polls
POLL_TIMEOUT = 180         # seconds before giving up on a non-flow run
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "error", "stopped"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentSpec:
    """Agent discovered from local YAML manifests."""
    name: str
    flow_triggering: bool
    prompts: list[str]


@dataclass
class CatalogEntry:
    """Agent as registered in WXO: its ID and its environment IDs by name."""
    agent_id: str
    environments: dict[str, str]


@dataclass
class PoolEntry:
    """Agent that is both locally discovered and confirmed deployed in WXO."""
    name: str
    agent_id: str
    flow_triggering: bool
    prompts: list[str]
    environment_id: str | None = None  # None = omit from the run (WXO targets the draft agent)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _fetch_token(api_key: str, env_type: str) -> tuple[str, float]:
    """Exchange API key for an access token. Returns (token, fetched_at)."""
    url = MCSP_URL if env_type.lower() == "mcsp" else IAM_URL
    payload = urllib.parse.urlencode(
        {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            token = json.loads(resp.read().decode("utf-8")).get("access_token", "")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Token exchange failed HTTP {exc.code}: {body}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError(f"Token exchange failed: {exc}") from exc
    if not token:
        raise RuntimeError("Token response contained no access_token.")
    return token, time.monotonic()


class TokenManager:
    """Holds a Bearer token and refreshes it proactively or on 401."""

    def __init__(self, api_key: str, env_type: str) -> None:
        self._api_key = api_key
        self._env_type = env_type
        self._token = ""
        self._fetched_at = 0.0

    def get(self) -> str:
        if not self._token or (time.monotonic() - self._fetched_at) >= TOKEN_TTL:
            self._token, self._fetched_at = _fetch_token(self._api_key, self._env_type)
        return self._token

    def refresh(self) -> str:
        self._token, self._fetched_at = _fetch_token(self._api_key, self._env_type)
        return self._token


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class Api:
    """Thin authenticated HTTP client for the WXO REST API."""

    def __init__(self, tokens: TokenManager) -> None:
        self._tokens = tokens

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tokens.get()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        body: dict | None = None,
        retries: int = 3,
    ) -> Any:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        last_exc: Exception | None = None
        for attempt in range(retries):
            req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
                    content = resp.read().decode("utf-8")
                    return json.loads(content) if content else {}
            except urllib.error.HTTPError as exc:
                if exc.code == 401 and attempt == 0:
                    # Token expired mid-flight — refresh once and retry immediately.
                    self._tokens.refresh()
                    continue
                if exc.code == 429 and attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {exc.code} {method} {url}: {detail}") from exc
            except (urllib.error.URLError, http.client.HTTPException, OSError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    time.sleep(attempt + 1)
        raise RuntimeError(f"Request failed after {retries} attempts ({url}): {last_exc}")


# ---------------------------------------------------------------------------
# Minimal YAML reader (stdlib only)
# ---------------------------------------------------------------------------

def _read_yaml_simple(path: Path) -> dict[str, Any]:
    """Parse only the top-level scalar and list fields we need from agent/scenario YAMLs.

    Handles:
      key: scalar_value
      key:
        - item1
        - item2
      key: []
    Does NOT handle nested mappings beyond what is needed here.
    """
    result: dict[str, Any] = {}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Skip comments and blank lines.
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        # Top-level key: value  (no leading spaces)
        if not line.startswith(" ") and not line.startswith("\t") and ":" in stripped:
            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "":
                # Might be a list block — look ahead.
                items: list[str] = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped or next_stripped.startswith("#"):
                        j += 1
                        continue
                    if next_stripped.startswith("- "):
                        items.append(next_stripped[2:].strip().strip("'\""))
                        j += 1
                    else:
                        break
                result[key] = items
                i = j
            elif rest == "[]":
                result[key] = []
                i += 1
            else:
                # Strip inline comments and quotes.
                value = rest.split(" #")[0].strip().strip("'\"")
                result[key] = value
                i += 1
        else:
            i += 1
    return result


# ---------------------------------------------------------------------------
# Agent discovery from repo manifests
# ---------------------------------------------------------------------------

def _find_repo_root(app_file: Path) -> Path:
    """Locate repo root by probing for the scenarios/ directory."""
    # Inside container: app.py lives at /app/app.py; scenarios/ is at /app/scenarios/.
    candidate = app_file.parent
    if (candidate / "scenarios").is_dir():
        return candidate
    # Local dev: app.py lives at traffic-gen/app.py; scenarios/ is one level up.
    candidate = app_file.parent.parent
    if (candidate / "scenarios").is_dir():
        return candidate
    raise RuntimeError(
        f"Cannot find scenarios/ relative to {app_file}. "
        "Set REPO_ROOT env var to the repository root directory."
    )


def _load_standalone_prompts(repo_root: Path) -> dict[str, list[str]]:
    """Read traffic-gen/prompts.yaml.  Returns {agent_name: [prompt, ...]}."""
    # prompts.yaml lives alongside app.py inside the container, or in traffic-gen/ locally.
    for candidate in (
        Path(__file__).parent / "prompts.yaml",
        repo_root / "traffic-gen" / "prompts.yaml",
    ):
        if candidate.is_file():
            prompts_file = candidate
            break
    else:
        _warn("prompts.yaml not found; standalone agents will be skipped.")
        return {}

    result: dict[str, list[str]] = {}
    current_key: str | None = None
    for raw_line in prompts_file.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and not line.startswith("\t") and line.endswith(":"):
            current_key = line[:-1].strip()
            result[current_key] = []
        elif stripped.startswith("- ") and current_key is not None:
            prompt = stripped[2:].strip()
            # Strip wrapping quotes added by YAML.
            if len(prompt) >= 2 and prompt[0] == prompt[-1] and prompt[0] in ('"', "'"):
                prompt = prompt[1:-1]
            result[current_key].append(prompt)
    return result


def discover_agents(repo_root: Path, agent_filter: list[str]) -> list[AgentSpec]:
    """Build the list of callable agents from local manifests.

    Scenario agents: scenarios/*/scenario.yaml
    Standalone agents: standalone/*/agent.yaml + traffic-gen/prompts.yaml
    """
    specs: list[AgentSpec] = []

    # --- Scenario agents ---------------------------------------------------
    scenarios_dir = repo_root / "scenarios"
    evaluation_dir = repo_root / "evaluation"
    for scenario_dir in sorted(scenarios_dir.iterdir()):
        manifest = scenario_dir / "scenario.yaml"
        if not manifest.is_file():
            continue
        try:
            data = _read_yaml_simple(manifest)
        except Exception as exc:  # noqa: BLE001
            _warn(f"Skipping {manifest}: {exc}")
            continue

        agents_list = data.get("agents", [])
        smoke_agent = data.get("smoke_agent", "")
        flows = data.get("flows", [])
        scenario_id = scenario_dir.name

        # Determine callable agent name.
        if smoke_agent:
            callable_name = smoke_agent
        elif agents_list:
            # First item is the callable entry point.
            first = agents_list[0]
            # Items are "name: agent_name  path: ..." collapsed by simple parser; extract name.
            # The simple parser returns list items as raw stripped strings like "name: foo".
            callable_name = _extract_field(first, "name") or first
        else:
            _warn(f"Scenario {scenario_id}: no agents listed, skipping.")
            continue

        # Load smoke prompts from ground_truth.json.
        gt_path = evaluation_dir / scenario_id / "ground_truth.json"
        if not gt_path.is_file():
            _warn(f"Scenario {scenario_id}: {gt_path} not found, skipping agent '{callable_name}'.")
            continue
        try:
            gt = json.loads(gt_path.read_text(encoding="utf-8-sig"))
            prompts = [p["prompt"] for p in gt.get("smoke_prompts", []) if p.get("prompt")]
        except Exception as exc:  # noqa: BLE001
            _warn(f"Scenario {scenario_id}: failed to read ground_truth.json: {exc}")
            continue
        if not prompts:
            _warn(f"Scenario {scenario_id}: no smoke_prompts in ground_truth.json, skipping.")
            continue

        flow_triggering = bool(flows)  # non-empty flows list means fire-and-forget
        specs.append(AgentSpec(name=callable_name, flow_triggering=flow_triggering, prompts=prompts))

    # --- Standalone agents -------------------------------------------------
    standalone_prompts = _load_standalone_prompts(repo_root)
    standalone_dir = repo_root / "standalone"
    for agent_dir in sorted(standalone_dir.iterdir()):
        agent_yaml = agent_dir / "agent.yaml"
        if not agent_yaml.is_file():
            continue
        try:
            data = _read_yaml_simple(agent_yaml)
        except Exception as exc:  # noqa: BLE001
            _warn(f"Skipping {agent_yaml}: {exc}")
            continue
        name = data.get("name", "")
        if not name:
            _warn(f"{agent_yaml}: no 'name' field, skipping.")
            continue
        prompts = standalone_prompts.get(name, [])
        if not prompts:
            _warn(f"Standalone agent '{name}': no prompts in prompts.yaml, skipping.")
            continue
        specs.append(AgentSpec(name=name, flow_triggering=False, prompts=prompts))

    # --- Apply filter ------------------------------------------------------
    if agent_filter:
        filtered = [s for s in specs if s.name in agent_filter]
        removed = [s.name for s in specs if s.name not in agent_filter]
        if removed:
            _log(f"AGENT_FILTER active — excluded: {', '.join(removed)}")
        specs = filtered

    return specs


def _extract_field(item: str, field: str) -> str:
    """Extract 'field: value' from a YAML list item string like 'name: foo  path: bar'."""
    for part in item.replace("\t", " ").split("  "):
        part = part.strip()
        if part.startswith(f"{field}:"):
            return part[len(field) + 1:].strip().strip("'\"")
    return ""


# ---------------------------------------------------------------------------
# WXO catalog and pool resolution
# ---------------------------------------------------------------------------

def load_catalog(api: Api, base_url: str) -> dict[str, CatalogEntry]:
    """GET /v1/orchestrate/agents → {name: CatalogEntry(agent_id, {env_name: env_id})}."""
    url = f"{base_url.rstrip('/')}/v1/orchestrate/agents"
    try:
        result = api.request(url)
    except RuntimeError as exc:
        raise RuntimeError(f"Failed to list agents: {exc}") from exc
    items = result if isinstance(result, list) else (result or {}).get("data", [])
    if not isinstance(items, list):
        raise RuntimeError(f"Unexpected agent list response: {type(result)}")
    catalog: dict[str, CatalogEntry] = {}
    for item in items:
        if isinstance(item, dict) and item.get("id") and item.get("name"):
            envs = {
                e["name"]: e["id"]
                for e in (item.get("environments") or [])
                if isinstance(e, dict) and e.get("name") and e.get("id")
            }
            catalog[item["name"]] = CatalogEntry(agent_id=item["id"], environments=envs)
    return catalog


def resolve_pool(
    specs: list[AgentSpec], catalog: dict[str, CatalogEntry], environment: str
) -> list[PoolEntry]:
    """Match discovered specs against WXO agents. Warn about any not found or lacking the environment.

    environment 'draft' sends no environment_id; any other name must exist on the agent.
    """
    pool: list[PoolEntry] = []
    for spec in specs:
        found = catalog.get(spec.name)
        if not found:
            _warn(f"Agent '{spec.name}' not found in WXO (not deployed?), skipping.")
            continue
        environment_id: str | None = None
        if environment != "draft":
            environment_id = found.environments.get(environment)
            if not environment_id:
                _warn(
                    f"Agent '{spec.name}' has no '{environment}' environment "
                    f"(has: {', '.join(sorted(found.environments)) or 'none'}); skipping."
                )
                continue
        pool.append(
            PoolEntry(
                name=spec.name,
                agent_id=found.agent_id,
                flow_triggering=spec.flow_triggering,
                prompts=spec.prompts,
                environment_id=environment_id,
            )
        )
    return pool


# ---------------------------------------------------------------------------
# Sending a prompt
# ---------------------------------------------------------------------------

def send_prompt(api: Api, base_url: str, entry: PoolEntry) -> None:
    prompt = random.choice(entry.prompts)
    short = prompt[:80] + ("..." if len(prompt) > 80 else "")
    label = f"{entry.name:<30}  \"{short}\""

    url = f"{base_url.rstrip('/')}/v1/orchestrate/runs"
    body: dict[str, Any] = {
        "message": {"role": "user", "content": prompt},
        "agent_id": entry.agent_id,
    }
    if entry.environment_id:
        body["environment_id"] = entry.environment_id
    try:
        resp = api.request(url, method="POST", body=body)
    except RuntimeError as exc:
        _log(f"{label}  → ERROR: {exc}")
        return

    run_id = resp.get("run_id") if isinstance(resp, dict) else None

    if entry.flow_triggering or not run_id:
        _log(f"{label}  → sent (fire-and-forget)")
        return

    # Poll for completion.
    poll_url = f"{base_url.rstrip('/')}/v1/orchestrate/runs/{run_id}"
    start = time.monotonic()
    while True:
        elapsed = time.monotonic() - start
        if elapsed >= POLL_TIMEOUT:
            _log(f"{label}  → timeout after {int(elapsed)}s")
            return
        time.sleep(POLL_INTERVAL)
        try:
            status_resp = api.request(poll_url)
        except RuntimeError as exc:
            _log(f"{label}  → ERROR polling: {exc}")
            return
        status = (status_resp.get("status") or "").lower() if isinstance(status_resp, dict) else ""
        if status in TERMINAL_STATUSES:
            elapsed_total = int(time.monotonic() - start)
            _log(f"{label}  → {status} ({elapsed_total}s)")
            return


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    print(f"[{_now_iso()}] {msg}", flush=True)


def _warn(msg: str) -> None:
    print(f"[{_now_iso()}] WARNING: {msg}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = os.environ.get("WXO_API_KEY", "")
    base_url = os.environ.get("WXO_URL", "").rstrip("/")
    env_type = os.environ.get("WXO_ENV_TYPE", "ibm_iam")
    interval_minutes = int(os.environ.get("CALL_INTERVAL_MINUTES", "1"))
    environment = os.environ.get("WXO_ENVIRONMENT", "live").strip().lower() or "live"
    agent_filter_raw = os.environ.get("AGENT_FILTER", "")
    agent_filter = [n.strip() for n in agent_filter_raw.split(",") if n.strip()] if agent_filter_raw else []

    if not api_key:
        print("ERROR: WXO_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)
    if not base_url:
        print("ERROR: WXO_URL is not set.", file=sys.stderr)
        sys.exit(1)

    window_seconds = interval_minutes * 60

    # Locate repo root and discover agents.
    repo_root_env = os.environ.get("REPO_ROOT", "")
    if repo_root_env:
        repo_root = Path(repo_root_env)
    else:
        repo_root = _find_repo_root(Path(__file__).resolve())

    _log(f"Repo root: {repo_root}")
    _log(f"WXO URL:   {base_url}")
    _log(f"Interval:  {interval_minutes} min/window (random offset each window)")
    _log(f"Target environment: {environment}")

    specs = discover_agents(repo_root, agent_filter)
    if not specs:
        print("ERROR: No agents discovered. Check manifests and prompts.yaml.", file=sys.stderr)
        sys.exit(1)

    _log(f"Discovered {len(specs)} agent(s) from manifests.")

    # Authenticate.
    _log("Authenticating…")
    tokens = TokenManager(api_key, env_type)
    try:
        tokens.get()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    _log("Token obtained.")

    api = Api(tokens)

    # Resolve against live WXO agents.
    _log("Loading agent catalog from WXO…")
    try:
        catalog = load_catalog(api, base_url)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    _log(f"WXO catalog: {len(catalog)} agent(s) found.")

    pool = resolve_pool(specs, catalog, environment)
    if not pool:
        print(
            f"ERROR: No agents matched between manifests and WXO for environment '{environment}'. "
            "Check deployments.",
            file=sys.stderr,
        )
        sys.exit(1)

    _log(f"Active pool ({len(pool)} agent(s)):")
    for entry in pool:
        flag = " [fire-and-forget]" if entry.flow_triggering else ""
        _log(f"  {entry.name:<30}  id={entry.agent_id}{flag}  prompts={len(entry.prompts)}")

    _log("Starting scheduler loop.")

    # Scheduler loop: one call per window, fired at a random second within the window.
    while True:
        window_start = time.monotonic()
        offset = random.randint(0, max(0, window_seconds - 1))
        time.sleep(offset)

        entry = random.choice(pool)
        try:
            send_prompt(api, base_url, entry)
        except Exception as exc:  # noqa: BLE001
            _log(f"Unexpected error: {exc}")

        elapsed = time.monotonic() - window_start
        remainder = window_seconds - elapsed
        if remainder > 0:
            time.sleep(remainder)


if __name__ == "__main__":
    main()

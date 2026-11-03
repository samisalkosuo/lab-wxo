"""Traffic generator container lifecycle and pool management for wxodemo."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from wxodemo.config import Config, UsageError
from wxodemo.logging_setup import (
    fail,
    get_logger,
    info,
    ok,
    plain,
    register_secret,
    warn,
)
from wxodemo.manifest import load_yaml

DEFAULT_IMAGE = "wxo-traffic-gen"
DEFAULT_CONTAINER = "wxo-traffic-gen"
SUPPORTED_ENGINES = ("podman", "docker")


def find_container_engine(preferred: str | None = None) -> tuple[str, str]:
    """Find a container engine executable (podman or docker).

    Returns (engine_name, executable_path).
    Raises UsageError if no engine is found.
    """
    if preferred:
        pref = preferred.lower().strip()
        if pref not in SUPPORTED_ENGINES:
            engines_str = ", ".join(SUPPORTED_ENGINES)
            raise UsageError(
                f"Unsupported container engine '{preferred}'. Supported: {engines_str}"
            )
        exe = shutil.which(pref)
        if not exe:
            raise UsageError(f"Container engine '{pref}' was not found on PATH.")
        return pref, exe

    for name in SUPPORTED_ENGINES:
        exe = shutil.which(name)
        if exe:
            return name, exe

    raise UsageError(
        "No container engine ('podman' or 'docker') found on PATH.\n"
        "Install Podman or Docker to use traffic generator container commands."
    )


def get_container_engine_info(preferred: str | None = None) -> tuple[str, str] | None:
    """Return (engine_name, version_str) or None if not found."""
    try:
        name, exe = find_container_engine(preferred)
    except UsageError:
        return None

    try:
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            # e.g. "podman version 5.1.2" or "Docker version 27.2.0, build 3ab5250"
            ver_line = proc.stdout.strip().splitlines()[0]
            return name, ver_line
    except Exception:  # noqa: BLE001
        pass
    return name, name


def _run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command with debug logging."""
    logger = get_logger()
    logger.debug("Running container command: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Pool Discovery
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiscoveredAgent:
    name: str
    kind: str  # "scenario" or "standalone"
    source_id: str  # scenario id or standalone dir name
    flow_triggering: bool
    prompts: list[str]


def _load_standalone_prompts(root: Path) -> dict[str, list[str]]:
    """Load prompts from traffic-gen/prompts.yaml."""
    prompts_file = root / "traffic-gen" / "prompts.yaml"
    if not prompts_file.is_file():
        return {}

    try:
        data = load_yaml(prompts_file)
        if isinstance(data, dict):
            res: dict[str, list[str]] = {}
            for k, v in data.items():
                if isinstance(v, list):
                    res[k] = [str(item) for item in v if item]
            return res
    except Exception as exc:  # noqa: BLE001
        warn(f"Failed to read traffic-gen/prompts.yaml: {exc}")
    return {}


def discover_traffic_pool(
    root: Path, agent_filter: list[str] | None = None
) -> list[DiscoveredAgent]:
    """Discover all callable scenario and standalone agents and their prompt pool."""
    agents: list[DiscoveredAgent] = []

    # 1. Scenarios
    scenarios_dir = root / "scenarios"
    evaluation_dir = root / "evaluation"
    if scenarios_dir.is_dir():
        for scenario_dir in sorted(p for p in scenarios_dir.iterdir() if p.is_dir()):
            manifest = scenario_dir / "scenario.yaml"
            if not manifest.is_file():
                continue
            try:
                data = load_yaml(manifest)
            except Exception as exc:  # noqa: BLE001
                warn(f"Skipping {manifest}: {exc}")
                continue

            if not isinstance(data, dict):
                continue

            agents_list = data.get("agents", [])
            smoke_agent = data.get("smoke_agent", "")
            flows = data.get("flows", [])
            scenario_id = scenario_dir.name

            callable_name = ""
            if smoke_agent:
                callable_name = str(smoke_agent)
            elif agents_list:
                first = agents_list[0]
                if isinstance(first, dict):
                    callable_name = first.get("name", "")
                elif isinstance(first, str):
                    callable_name = first
            if not callable_name:
                continue

            gt_path = evaluation_dir / scenario_id / "ground_truth.json"
            prompts: list[str] = []
            if gt_path.is_file():
                try:
                    gt = json.loads(gt_path.read_text(encoding="utf-8-sig"))
                    prompts = [p["prompt"] for p in gt.get("smoke_prompts", []) if p.get("prompt")]
                except Exception as exc:  # noqa: BLE001
                    warn(f"Scenario {scenario_id}: failed to read ground_truth.json: {exc}")

            if not prompts:
                continue

            agents.append(
                DiscoveredAgent(
                    name=callable_name,
                    kind="scenario",
                    source_id=scenario_id,
                    flow_triggering=bool(flows),
                    prompts=prompts,
                )
            )

    # 2. Standalone agents
    standalone_prompts = _load_standalone_prompts(root)
    standalone_dir = root / "standalone"
    if standalone_dir.is_dir():
        for agent_dir in sorted(p for p in standalone_dir.iterdir() if p.is_dir()):
            agent_yaml = agent_dir / "agent.yaml"
            if not agent_yaml.is_file():
                continue
            try:
                data = load_yaml(agent_yaml)
            except Exception as exc:  # noqa: BLE001
                warn(f"Skipping {agent_yaml}: {exc}")
                continue

            if not isinstance(data, dict):
                continue
            name = data.get("name", "")
            if not name:
                continue
            prompts = standalone_prompts.get(name, [])
            if not prompts:
                continue

            agents.append(
                DiscoveredAgent(
                    name=name,
                    kind="standalone",
                    source_id=agent_dir.name,
                    flow_triggering=False,
                    prompts=prompts,
                )
            )

    if agent_filter:
        filter_set = set(agent_filter)
        agents = [a for a in agents if a.name in filter_set or a.source_id in filter_set]

    return agents


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------


def run_traffic_build(
    root: Path,
    engine: str | None = None,
    no_cache: bool = False,
    dry_run: bool = False,
) -> int:
    """Build the traffic generator container image."""
    engine_name, engine_exe = find_container_engine(engine)
    dockerfile = root / "traffic-gen" / "Dockerfile"
    if not dockerfile.is_file():
        fail(f"Dockerfile not found at {dockerfile}")
        return 1

    cmd = [engine_exe, "build", "-f", "traffic-gen/Dockerfile", "-t", DEFAULT_IMAGE]
    if no_cache:
        cmd.append("--no-cache")
    cmd.append(".")

    if dry_run:
        plain(f"[dry-run] would run: {' '.join(cmd)}")
        return 0

    plain(f"Building image '{DEFAULT_IMAGE}' with {engine_name} from repo root ...")
    proc = _run_cmd(cmd, cwd=root)
    if proc.returncode != 0:
        fail(f"Failed to build image '{DEFAULT_IMAGE}' (exit code {proc.returncode})")
        return proc.returncode
    ok(f"Successfully built image '{DEFAULT_IMAGE}' with {engine_name}")
    return 0


def _is_container_running(engine_exe: str, container_name: str) -> bool:
    """Check if container with given name is currently running."""
    proc = _run_cmd(
        [engine_exe, "ps", "-q", "--filter", f"name=^{container_name}$"],
        capture=True,
    )
    return bool(proc.returncode == 0 and proc.stdout.strip())


def run_traffic_start(
    root: Path,
    config: Config | None,
    engine: str | None = None,
    interval: int | None = None,
    agents: str | None = None,
    env: str | None = None,
    container_name: str = DEFAULT_CONTAINER,
    follow: bool = False,
    foreground: bool = False,
    dry_run: bool = False,
) -> int:
    """Start the traffic generator container."""
    engine_name, engine_exe = find_container_engine(engine)

    if config:
        register_secret(config.api_key)

    api_key = config.api_key if config else "your-api-key-here"
    url = config.url if config else "https://api.example.com/instances/id"
    env_type = config.env_type if config else "ibm_iam"

    cmd = [engine_exe, "run"]
    if foreground:
        cmd.append("--rm")
    else:
        cmd.extend(["-d", "--name", container_name])

    cmd.extend([
        "-e", f"WXO_API_KEY={api_key}",
        "-e", f"WXO_URL={url}",
        "-e", f"WXO_ENV_TYPE={env_type}",
    ])
    if interval is not None:
        cmd.extend(["-e", f"CALL_INTERVAL_MINUTES={interval}"])
    if agents:
        cmd.extend(["-e", f"AGENT_FILTER={agents}"])
    if env:
        cmd.extend(["-e", f"WXO_ENVIRONMENT={env}"])

    cmd.append(DEFAULT_IMAGE)

    if dry_run:
        plain(f"[dry-run] would run: {' '.join(cmd)}")
        return 0

    if not foreground and _is_container_running(engine_exe, container_name):
        fail(
            f"Container '{container_name}' is already running.\n"
            f"Use 'python wxodemo.py traffic stop' or 'python wxodemo.py traffic redeploy'."
        )
        return 1

    # If detached, clean up any stopped container holding the name
    if not foreground:
        _run_cmd([engine_exe, "rm", "-f", container_name], capture=True)

    plain(f"Starting traffic generator container '{container_name}' with {engine_name} ...")
    proc = _run_cmd(cmd, cwd=root)
    if proc.returncode != 0:
        fail(f"Failed to start container '{container_name}' (exit code {proc.returncode})")
        return proc.returncode

    target_env = env or "live"
    win_interval = interval or 1
    ok(
        f"Traffic generator container '{container_name}' started "
        f"(interval={win_interval}m, env={target_env})"
    )

    if follow and not foreground:
        return run_traffic_logs(root, engine=engine, container_name=container_name, follow=True)

    if not foreground:
        info("Follow live traffic logs with:  python wxodemo.py traffic logs")
        info("Check container status with:    python wxodemo.py traffic status")
        info("Stop traffic generator with:    python wxodemo.py traffic stop")
    return 0


def run_traffic_stop(
    root: Path,
    engine: str | None = None,
    container_name: str = DEFAULT_CONTAINER,
    dry_run: bool = False,
) -> int:
    """Stop and remove the traffic generator container."""
    engine_name, engine_exe = find_container_engine(engine)

    if dry_run:
        plain(f"[dry-run] would stop and remove container '{container_name}' using {engine_name}")
        return 0

    plain(f"Stopping container '{container_name}' ...")
    stop_proc = _run_cmd([engine_exe, "stop", container_name], capture=True)
    _run_cmd([engine_exe, "rm", "-f", container_name], capture=True)

    if stop_proc.returncode == 0:
        ok(f"Stopped and removed container '{container_name}'")
        return 0

    info(f"Container '{container_name}' was not running")
    return 0


def run_traffic_status(
    root: Path,
    config: Config | None = None,
    engine: str | None = None,
    container_name: str = DEFAULT_CONTAINER,
) -> int:
    """Check and display the container and image status."""
    engine_name, engine_exe = find_container_engine(engine)
    ver_info = get_container_engine_info(engine)
    ver_str = ver_info[1] if ver_info else engine_name

    plain("Traffic Generator Status")
    plain(f"  Container Engine:  {ver_str}")

    # Check container status
    ps_proc = _run_cmd(
        [
            engine_exe,
            "ps",
            "-a",
            "--filter",
            f"name=^{container_name}$",
            "--format",
            "{{.ID}}\t{{.Status}}\t{{.Image}}",
        ],
        capture=True,
    )
    container_info = ps_proc.stdout.strip() if ps_proc.returncode == 0 else ""

    if container_info:
        parts = container_info.split("\t")
        cid = parts[0] if len(parts) > 0 else ""
        cstatus = parts[1] if len(parts) > 1 else ""
        cimg = parts[2] if len(parts) > 2 else ""
        plain(f"  Container:         {container_name} ({cid}) - {cstatus} [image: {cimg}]")
    else:
        plain(f"  Container:         {container_name} - not running / not created")

    # Check image status
    img_proc = _run_cmd(
        [
            engine_exe,
            "images",
            DEFAULT_IMAGE,
            "--format",
            "{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}",
        ],
        capture=True,
    )
    img_info = img_proc.stdout.strip() if img_proc.returncode == 0 else ""
    if img_info:
        first_img = img_info.splitlines()[0]
        plain(f"  Image:             {first_img.replace(chr(9), '  ')}")
    else:
        warn(f"Image '{DEFAULT_IMAGE}' is not built yet. Run: python wxodemo.py traffic build")

    if config:
        plain(f"  Target Instance:   {config.url}")
        plain(f"  Auth Type:         {config.env_type}")

    return 0


def run_traffic_redeploy(
    root: Path,
    config: Config | None,
    engine: str | None = None,
    interval: int | None = None,
    agents: str | None = None,
    env: str | None = None,
    container_name: str = DEFAULT_CONTAINER,
    no_cache: bool = False,
    follow: bool = False,
    dry_run: bool = False,
) -> int:
    """Stop container, rebuild image, and start container."""
    if dry_run:
        run_traffic_stop(root, engine=engine, container_name=container_name, dry_run=True)
        run_traffic_build(root, engine=engine, no_cache=no_cache, dry_run=True)
        return run_traffic_start(
            root,
            config,
            engine=engine,
            interval=interval,
            agents=agents,
            env=env,
            container_name=container_name,
            follow=follow,
            dry_run=True,
        )

    run_traffic_stop(root, engine=engine, container_name=container_name, dry_run=False)
    build_code = run_traffic_build(root, engine=engine, no_cache=no_cache, dry_run=False)
    if build_code != 0:
        return build_code
    return run_traffic_start(
        root,
        config,
        engine=engine,
        interval=interval,
        agents=agents,
        env=env,
        container_name=container_name,
        follow=follow,
        dry_run=False,
    )


def run_traffic_logs(
    root: Path,
    engine: str | None = None,
    container_name: str = DEFAULT_CONTAINER,
    follow: bool = True,
    tail: int | None = None,
) -> int:
    """View or follow traffic generator container logs (default follow=True)."""
    _, engine_exe = find_container_engine(engine)

    cmd = [engine_exe, "logs"]
    if follow:
        cmd.append("-f")
    if tail:
        cmd.extend(["--tail", str(tail)])
    cmd.append(container_name)

    try:
        proc = _run_cmd(cmd)
        return proc.returncode
    except KeyboardInterrupt:
        return 0


def run_traffic_pool(
    root: Path,
    agents: str | None = None,
    json_output: bool = False,
) -> int:
    """Preview the pool of agents and prompts discovered locally for traffic generation."""
    agent_filter = [a.strip() for a in agents.split(",")] if agents else None
    pool = discover_traffic_pool(root, agent_filter=agent_filter)

    if json_output:
        data = [
            {
                "name": a.name,
                "kind": a.kind,
                "source_id": a.source_id,
                "flow_triggering": a.flow_triggering,
                "prompt_count": len(a.prompts),
                "prompts": a.prompts,
            }
            for a in pool
        ]
        plain(json.dumps(data, indent=2))
        return 0

    plain(f"Traffic Generator Discovered Pool ({len(pool)} agents)\n")
    plain(f"{'AGENT':<30} {'KIND':<12} {'EXECUTION':<15} {'PROMPTS':<8} {'SAMPLE PROMPT'}")
    plain(f"{'-'*30} {'-'*12} {'-'*15} {'-'*8} {'-'*30}")

    for a in pool:
        exec_type = "async (flow)" if a.flow_triggering else "polled"
        sample = a.prompts[0] if a.prompts else ""
        if len(sample) > 35:
            sample = sample[:32] + "..."
        plain(f"{a.name:<30} {a.kind:<12} {exec_type:<15} {len(a.prompts):<8} {sample}")

    plain("\nNotes:")
    plain("  - Scenario prompts are loaded from evaluation/<id>/ground_truth.json (smoke_prompts).")
    plain("  - Standalone agent prompts are loaded from traffic-gen/prompts.yaml.")
    plain("  - Flow-triggering agents (with flows) are sent fire-and-forget; others are polled.")
    return 0

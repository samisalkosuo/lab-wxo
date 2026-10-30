"""Upload test cases to watsonx Orchestrate agent evaluation API and trigger evaluations.

Communicates with the WXO Agent Evaluation REST service:
  POST /v1/orchestrate/agent/{agent_id}/test_case    (upload test cases CSV)
  POST /v1/orchestrate/agent/{agent_id}/evaluate     (trigger evaluation run)
"""

from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from wxodemo.chats import Api, ExportError, USER_AGENT, get_token
from wxodemo.config import Config, UsageError
from wxodemo.discovery import Target
from wxodemo.logging_setup import fail, get_logger, ok, plain, warn


def find_agent_id(api: Api, root_url: str, agent_name: str) -> str | None:
    """Find the UUID of an agent by its name."""
    root = root_url.rstrip("/")
    for path in ("/v1/orchestrate/agents", "/v1/agents"):
        try:
            result = api.request(f"{root}{path}")
        except ExportError:
            get_logger().debug("agent catalog not at %s", path, exc_info=True)
            continue
        items = result if isinstance(result, list) else (result or {}).get("data")
        if isinstance(items, list):
            for agent in items:
                if isinstance(agent, dict) and agent.get("name") == agent_name and "id" in agent:
                    return str(agent["id"])
    return None


def collect_test_prompts(root: Path, target: Target) -> list[str]:
    """Collect test prompts from test cases and ground truth files."""
    prompts: list[str] = []

    # 1. From scenario test_cases/*.json
    if target.scenario is not None:
        ev = target.scenario.get("evaluation")
        if ev and ev.get("path"):
            tc_dir = root / ev["path"] / "test_cases"
            if tc_dir.is_dir():
                for json_file in sorted(tc_dir.glob("*.json")):
                    try:
                        data = json.loads(json_file.read_text(encoding="utf-8-sig"))
                        start = data.get("starting_sentence") or data.get("prompt")
                        if start and start.strip():
                            prompts.append(start.strip())
                    except Exception:  # noqa: BLE001
                        pass

            # Also check ground_truth.json smoke_prompts
            gt_path = root / ev["path"] / "ground_truth.json"
            if gt_path.is_file():
                try:
                    gt_data = json.loads(gt_path.read_text(encoding="utf-8-sig"))
                    for sp in gt_data.get("smoke_prompts", []):
                        if isinstance(sp, dict) and sp.get("prompt"):
                            prompts.append(sp["prompt"].strip())
                except Exception:  # noqa: BLE001
                    pass

    # 2. From standalone agent directory
    elif target.agent is not None:
        tc_dir = target.agent.dir / "test_cases"
        if tc_dir.is_dir():
            for json_file in sorted(tc_dir.glob("*.json")):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8-sig"))
                    start = data.get("starting_sentence") or data.get("prompt")
                    if start and start.strip():
                        prompts.append(start.strip())
                except Exception:  # noqa: BLE001
                    pass

    # Deduplicate while preserving order
    unique: list[str] = []
    seen: set[str] = set()
    for p in prompts:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def build_test_case_csv(prompts: list[str]) -> bytes:
    """Build CSV file content for test case upload."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["prompt"])
    for p in prompts:
        writer.writerow([p])
    return output.getvalue().encode("utf-8")


def upload_test_cases_to_agent(
    token: str, root_url: str, agent_id: str, csv_bytes: bytes, *, retries: int = 3
) -> list[str]:
    """Upload test cases CSV via multipart/form-data to WXO API. Returns test_case_ids."""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="test_cases.csv"\r\n')
    body.extend(b"Content-Type: text/csv\r\n\r\n")
    body.extend(csv_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    url = f"{root_url.rstrip('/')}/v1/orchestrate/agent/{agent_id}/test_case"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=bytes(body), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("test_case_ids") or []
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and attempt < retries - 1:
                continue
            if exc.code == 404 and "WXO-PROXY" in detail:
                raise ExportError(
                    "The remote SaaS gateway does not expose the Agent Evaluation upload API.\n"
                    "On SaaS, create tests interactively in the web console using Draft Preview ('Save as test'),\n"
                    "or run automated evaluations locally using: python wxodemo.py eval <target>"
                ) from exc
            raise ExportError(f"HTTP {exc.code} uploading test cases: {detail}") from exc
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_err = exc
    raise ExportError(f"Failed to upload test cases after {retries} attempts: {last_err}")


def trigger_agent_evaluation(
    api: Api, root_url: str, agent_id: str, test_case_ids: list[str]
) -> str | None:
    """Trigger an evaluation run on WXO platform. Returns evaluation_id."""
    url = f"{root_url.rstrip('/')}/v1/orchestrate/agent/{agent_id}/evaluate"
    payload = {"test_case_ids": test_case_ids}
    res = api.request(url, method="POST", body=payload)
    return (res or {}).get("evaluation_id")


def run_test_upload(
    root: Path,
    target: Target,
    cfg: Config | None,
    *,
    evaluate: bool = False,
    dry_run: bool = False,
) -> int:
    """Upload test cases to the WXO Agent Evaluation service and optionally trigger evaluation."""
    prompts = collect_test_prompts(root, target)
    if not prompts:
        warn(f"No test cases or smoke prompts found for {target.name}.")
        return 0

    agent_name = (
        target.scenario.get("agents")[0]["name"]
        if target.scenario and target.scenario.get("agents")
        else target.name
    )

    plain(f"Target: {target.name} (agent '{agent_name}')")
    plain(f"Collected {len(prompts)} test prompt(s):")
    for idx, p in enumerate(prompts, 1):
        truncated = p if len(p) <= 75 else p[:72] + "..."
        plain(f"  {idx}. {truncated}")

    if dry_run:
        plain(f"[dry-run] would upload {len(prompts)} test case(s) via POST /v1/orchestrate/agent/<agent_id>/test_case")
        if evaluate:
            plain("[dry-run] would trigger evaluation run via POST /v1/orchestrate/agent/<agent_id>/evaluate")
        return 0

    if cfg is None:
        raise UsageError("env.cfg is required for live test upload. Re-run without --dry-run or check env.cfg.")

    plain(f"Connecting to WXO at {cfg.url} ...")
    token = get_token(cfg)
    api = Api(token)

    agent_id = find_agent_id(api, cfg.url, agent_name)
    if not agent_id:
        fail(f"Agent '{agent_name}' was not found in active WXO instance. Please deploy it first with 'wxodemo deploy {target.name}'.")
        return 1

    plain(f"Found agent '{agent_name}' (ID: {agent_id})")
    csv_bytes = build_test_case_csv(prompts)
    plain(f"Uploading {len(prompts)} test case(s) to WXO 'Tests' tab ...")
    test_case_ids = upload_test_cases_to_agent(token, cfg.url, agent_id, csv_bytes)
    ok(f"Uploaded {len(test_case_ids)} test case(s) successfully! (Visible in WXO 'Tests' tab)")

    if evaluate and test_case_ids:
        plain("Triggering server-side evaluation run ...")
        eval_id = trigger_agent_evaluation(api, cfg.url, agent_id, test_case_ids)
        if eval_id:
            ok(f"Evaluation started! (ID: {eval_id} - visible in WXO 'Evaluations' tab)")
        else:
            ok("Evaluation started! (Check WXO 'Evaluations' tab)")

    return 0

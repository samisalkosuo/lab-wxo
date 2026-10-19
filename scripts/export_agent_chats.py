#!/usr/bin/env python3
"""Export and backup all agent conversation threads and observability traces from watsonx Orchestrate.

By default, this script runs with zero arguments, reading credentials from env.cfg,
querying the WXO REST API for all message threads and their messages, and using the
ADK CLI to export observability traces into a timestamped directory (YYYYMMDDHHMMSS).

Usage:
    python scripts/export_agent_chats.py
    python scripts/export_agent_chats.py --help
    python scripts/export_agent_chats.py --agent-id <UUID> --last 7d
    python scripts/export_agent_chats.py --threads-only
    python scripts/export_agent_chats.py --traces-only
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuration and Authentication
# ---------------------------------------------------------------------------

def load_env_cfg(cfg_path: Path | None = None) -> dict:
    """Parse env.cfg. Returns dictionary with credentials."""
    target_path = cfg_path or (ROOT / "env.cfg")
    if not target_path.is_file():
        sys.exit(
            f"ERROR: Configuration file not found at '{target_path}'.\n"
            "Create 'env.cfg' in the repository root or specify one with --env-file."
        )

    env = {}
    for line in target_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        idx = line.index("=") if "=" in line else -1
        if idx < 1:
            continue
        env[line[:idx].strip()] = line[idx + 1:].strip()

    for required in ("WXO_API_KEY", "WXO_URL", "WXO_ENV_NAME"):
        if not env.get(required):
            sys.exit(f"ERROR: '{target_path}' must define {required}.")

    if "WXO_ENV_TYPE" not in env:
        env["WXO_ENV_TYPE"] = "ibm_iam"

    return env


def get_iam_token(api_key: str, env_type: str = "ibm_iam") -> str:
    """Exchange API key for an access token (IAM or MCSP)."""
    if env_type.lower() == "mcsp":
        token_url = "https://iam.platform.saas.ibm.com/saas/v1/auth/token"
    else:
        token_url = "https://iam.cloud.ibm.com/identity/token"

    payload = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }).encode("utf-8")

    req = urllib.request.Request(
        token_url,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "wxo-export-tool/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            token = data.get("access_token")
            if not token:
                raise ValueError("Response did not contain 'access_token'")
            return token
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"ERROR: Failed to authenticate against IAM ({e.code}): {error_body}")
    except Exception as e:
        sys.exit(f"ERROR: Failed to obtain access token: {e}")


def make_api_request(url: str, token: str, method: str = "GET", body: dict | None = None) -> dict | list:
    """Execute authenticated JSON HTTP request against WXO REST API."""
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "wxo-export-tool/1.0",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} on {url}: {err}") from e
    except Exception as e:
        raise RuntimeError(f"Request failed on {url}: {e}") from e


# ---------------------------------------------------------------------------
# Message Threads & Chat Exporter (REST API)
# ---------------------------------------------------------------------------

def fetch_all_threads(base_url: str, token: str, agent_id: str | None = None, page_size: int = 50) -> list[dict]:
    """Retrieve all message threads using pagination."""
    threads = []
    offset = 0
    clean_base = base_url.rstrip("/")

    while True:
        params = {"limit": str(page_size), "offset": str(offset)}
        if agent_id:
            params["agent_id"] = agent_id

        url = f"{clean_base}/v1/threads?{urllib.parse.urlencode(params)}"
        response = make_api_request(url, token)

        if isinstance(response, dict):
            items = response.get("data") or response.get("items") or []
            total = response.get("total")
        elif isinstance(response, list):
            items = response
            total = len(items)
        else:
            items = []
            total = 0

        if not items:
            break

        threads.extend(items)
        offset += len(items)

        if total is not None and len(threads) >= total:
            break
        if len(items) < page_size:
            break

    return threads


def fetch_thread_messages(base_url: str, token: str, thread_id: str) -> list[dict]:
    """Retrieve all messages for a given thread ID."""
    clean_base = base_url.rstrip("/")
    url = f"{clean_base}/v1/threads/{urllib.parse.urlencode({'': thread_id})[1:]}/messages"
    try:
        res = make_api_request(url, token)
        if isinstance(res, list):
            return res
        if isinstance(res, dict):
            return res.get("data") or res.get("items") or res.get("messages") or []
        return []
    except Exception as e:
        print(f"    [!] Warning: Failed to fetch messages for thread {thread_id}: {e}", file=sys.stderr)
        return []


def export_threads_data(base_url: str, token: str, output_dir: Path, agent_id: str | None = None) -> dict:
    """Export all threads and their messages to disk."""
    threads_dir = output_dir / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Querying WXO REST API for message threads (agent_id={agent_id or 'all'})...")
    threads = fetch_all_threads(base_url, token, agent_id=agent_id)
    print(f"    Found {len(threads)} message thread(s).")

    summary_records = []
    total_messages = 0

    for idx, thread in enumerate(threads, start=1):
        thread_id = thread.get("id")
        if not thread_id:
            continue

        thread_title = thread.get("title") or "Untitled"
        created_on = thread.get("created_on") or thread.get("created_at")
        thread_agent_id = thread.get("agent_id")

        messages = fetch_thread_messages(base_url, token, thread_id)
        msg_count = len(messages)
        total_messages += msg_count

        thread_payload = {
            "thread": thread,
            "message_count": msg_count,
            "messages": messages,
        }

        thread_file = threads_dir / f"{thread_id}.json"
        thread_file.write_text(json.dumps(thread_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        summary_records.append({
            "id": thread_id,
            "title": thread_title,
            "agent_id": thread_agent_id,
            "created_on": created_on,
            "message_count": msg_count,
            "file": f"threads/{thread_id}.json",
        })

        if idx % 10 == 0 or idx == len(threads):
            print(f"    Exported {idx}/{len(threads)} threads ({total_messages} total messages)...")

    # Write summary index
    summary_file = threads_dir / "summary.json"
    summary_payload = {
        "total_threads": len(threads),
        "total_messages": total_messages,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "threads": summary_records,
    }
    summary_file.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "total_threads": len(threads),
        "total_messages": total_messages,
        "threads_summary_file": str(summary_file.relative_to(output_dir)),
    }


# ---------------------------------------------------------------------------
# ADK Observability Traces Exporter
# ---------------------------------------------------------------------------

def check_orchestrate_cli() -> bool:
    """Check if orchestrate CLI is available in PATH."""
    return shutil.which("orchestrate") is not None


def search_and_export_traces(output_dir: Path, last_window: str = "30d", limit: int = 1000) -> dict:
    """Use ADK CLI to search and export observability traces."""
    traces_dir = output_dir / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    if not check_orchestrate_cli():
        print("    [!] Warning: 'orchestrate' CLI not found on PATH. Skipping ADK trace export.")
        summary_payload = {
            "error": "orchestrate CLI not available on PATH",
            "total_traces": 0,
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "traces": [],
        }
        (traces_dir / "summary.json").write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
        return {"total_traces": 0, "status": "cli_not_found"}

    print(f"[*] Searching observability traces via ADK CLI (window: {last_window}, limit: {limit})...")
    
    cmd_search = [
        "orchestrate", "observability", "traces", "search",
        "--last", last_window,
        "--limit", str(limit),
    ]

    try:
        proc = subprocess.run(cmd_search, capture_output=True, text=True, check=False)
        stdout = proc.stdout.strip()
    except Exception as e:
        print(f"    [!] Error running trace search: {e}", file=sys.stderr)
        stdout = ""

    # Parse trace IDs from search output (handles both table output and JSON if present)
    trace_ids = []
    if stdout:
        for line in stdout.splitlines():
            line_str = line.strip()
            # Look for UUID / trace ID patterns or first column items
            parts = line_str.split()
            if parts:
                candidate = parts[0].strip("|").strip()
                # Check if candidate looks like a hex/uuid trace id (e.g. 16+ chars hex or hyphenated uuid)
                if len(candidate) >= 16 and all(c in "0123456789abcdefABCDEF-" for c in candidate):
                    trace_ids.append(candidate)

    print(f"    Found {len(trace_ids)} trace(s) to export.")

    trace_records = []
    for idx, trace_id in enumerate(trace_ids, start=1):
        trace_file = traces_dir / f"{trace_id}.json"
        cmd_export = [
            "orchestrate", "observability", "traces", "export",
            "--trace-id", trace_id,
        ]

        try:
            exp_proc = subprocess.run(cmd_export, capture_output=True, text=True, check=False)
            if exp_proc.returncode == 0 and exp_proc.stdout.strip():
                try:
                    parsed_json = json.loads(exp_proc.stdout)
                    trace_file.write_text(json.dumps(parsed_json, indent=2, ensure_ascii=False), encoding="utf-8")
                except json.JSONDecodeError:
                    trace_file.write_text(exp_proc.stdout, encoding="utf-8")
                
                trace_records.append({
                    "trace_id": trace_id,
                    "file": f"traces/{trace_id}.json",
                    "status": "exported",
                })
            else:
                trace_records.append({
                    "trace_id": trace_id,
                    "status": "export_failed",
                    "error": exp_proc.stderr.strip() or "Empty response",
                })
        except Exception as e:
            trace_records.append({
                "trace_id": trace_id,
                "status": "error",
                "error": str(e),
            })

        if idx % 10 == 0 or idx == len(trace_ids):
            print(f"    Exported {idx}/{len(trace_ids)} traces...")

    summary_file = traces_dir / "summary.json"
    summary_payload = {
        "total_traces": len(trace_ids),
        "exported_count": sum(1 for r in trace_records if r.get("status") == "exported"),
        "search_window": last_window,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "traces": trace_records,
    }
    summary_file.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "total_traces": len(trace_ids),
        "exported_count": summary_payload["exported_count"],
        "traces_summary_file": str(summary_file.relative_to(output_dir)),
    }


# ---------------------------------------------------------------------------
# Main Orchestration
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save and backup all watsonx Orchestrate (WXO) agent chats and execution traces.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "export",
        help="Base export directory (a timestamped subfolder will be created inside).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Path to env.cfg file (defaults to env.cfg in repository root).",
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        default=None,
        help="Optional agent UUID to filter message threads.",
    )
    parser.add_argument(
        "--last",
        type=str,
        default="30d",
        help="Time window for ADK trace search (e.g., '24h', '7d', '30d').",
    )
    parser.add_argument(
        "--threads-only",
        action="store_true",
        help="Only export REST API message threads and chat messages.",
    )
    parser.add_argument(
        "--traces-only",
        action="store_true",
        help="Only export ADK observability traces.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_time = time.time()

    # 1. Generate timestamp in YYYYMMDDHHMMSS format (e.g. 20261019125234)
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y%m%d%H%M%S")
    target_export_dir = args.output_dir / timestamp_str
    target_export_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f" WXO AGENT CHATS & TRACES BACKUP TOOL")
    print(f" Export Directory: {target_export_dir}")
    print(f" Timestamp:        {timestamp_str} ({now.isoformat()})")
    print("=" * 70)

    # 2. Load configuration from env.cfg
    cfg = load_env_cfg(args.env_file)
    wxo_url = cfg["WXO_URL"]
    wxo_api_key = cfg["WXO_API_KEY"]
    wxo_env_type = cfg.get("WXO_ENV_TYPE", "ibm_iam")
    wxo_env_name = cfg.get("WXO_ENV_NAME", "default")

    manifest = {
        "timestamp": timestamp_str,
        "created_at": now.isoformat(),
        "instance_url": wxo_url,
        "environment_name": wxo_env_name,
        "components": {},
    }

    # 3. Message Threads via REST API
    if not args.traces_only:
        print("\n--- [1/2] Exporting Message Threads via REST API ---")
        token = get_iam_token(wxo_api_key, wxo_env_type)
        threads_stats = export_threads_data(
            base_url=wxo_url,
            token=token,
            output_dir=target_export_dir,
            agent_id=args.agent_id,
        )
        manifest["components"]["threads"] = threads_stats
    else:
        print("\n--- [1/2] Skipping REST API Threads (--traces-only specified) ---")

    # 4. Observability Traces via ADK CLI
    if not args.threads_only:
        print("\n--- [2/2] Exporting Observability Traces via ADK CLI ---")
        traces_stats = search_and_export_traces(
            output_dir=target_export_dir,
            last_window=args.last,
        )
        manifest["components"]["traces"] = traces_stats
    else:
        print("\n--- [2/2] Skipping ADK Traces (--threads-only specified) ---")

    # 5. Write Manifest
    duration_sec = round(time.time() - start_time, 2)
    manifest["duration_seconds"] = duration_sec
    manifest_file = target_export_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. Final Summary Report
    print("\n" + "=" * 70)
    print(" BACKUP COMPLETED SUCCESSFULLY")
    print("=" * 70)
    if "threads" in manifest["components"]:
        t_stat = manifest["components"]["threads"]
        print(f"  * Threads exported:  {t_stat.get('total_threads', 0)}")
        print(f"  * Messages exported: {t_stat.get('total_messages', 0)}")
        print(f"  * Threads Index:     {target_export_dir / t_stat.get('threads_summary_file', '')}")
    if "traces" in manifest["components"]:
        tr_stat = manifest["components"]["traces"]
        print(f"  * Traces discovered: {tr_stat.get('total_traces', 0)}")
        print(f"  * Traces exported:   {tr_stat.get('exported_count', 0)}")
        print(f"  * Traces Index:      {target_export_dir / tr_stat.get('traces_summary_file', '')}")
    print(f"  * Top-level Manifest: {manifest_file}")
    print(f"  * Time Elapsed:       {duration_sec}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export and backup agent conversation threads and observability traces from watsonx Orchestrate.

By default, this script runs with zero arguments, reading credentials from env.cfg,
querying the WXO REST API for all message threads and their messages, and saving them
into a timestamped directory (YYYYMMDDHHMMSS).

To also download observability traces, provide the `--trace` flag.

Usage:
    python scripts/export_agent_chats.py
    python scripts/export_agent_chats.py --trace
    python scripts/export_agent_chats.py --trace --last 24h
    python scripts/export_agent_chats.py --agent-id <UUID>
    python scripts/export_agent_chats.py --traces-only
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Ensure UTF-8 output on Windows consoles
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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


def make_api_request(url: str, token: str, method: str = "GET", body: dict | None = None, retries: int = 3) -> dict | list:
    """Execute authenticated JSON HTTP request against WXO REST API with retry support."""
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "wxo-export-tool/1.0",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            # If 429 rate limit, wait and retry
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} on {url}: {err}") from e
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
            raise RuntimeError(f"Request failed on {url}: {last_err}") from e

    raise RuntimeError(f"Request failed after {retries} retries: {url}")


# ---------------------------------------------------------------------------
# Message Threads & Chat Exporter (REST API)
# ---------------------------------------------------------------------------

def resolve_threads_base_url(base_url: str, token: str) -> str:
    """Determine whether threads are hosted under /v1/orchestrate/threads or /v1/threads."""
    clean_base = base_url.rstrip("/")
    candidates = [
        f"{clean_base}/v1/orchestrate/threads",
        f"{clean_base}/v1/threads",
    ]
    for candidate in candidates:
        test_url = f"{candidate}?limit=1&offset=0"
        try:
            make_api_request(test_url, token)
            return candidate
        except Exception:
            continue
    # Default to SaaS endpoint if probe fails
    return f"{clean_base}/v1/orchestrate/threads"


def fetch_all_threads(threads_base_url: str, token: str, agent_id: str | None = None, page_size: int = 50) -> list[dict]:
    """Retrieve all message threads using pagination."""
    threads = []
    offset = 0

    while True:
        params = {"limit": str(page_size), "offset": str(offset)}
        if agent_id:
            params["agent_id"] = agent_id

        url = f"{threads_base_url}?{urllib.parse.urlencode(params)}"
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


def fetch_thread_messages(threads_base_url: str, token: str, thread_id: str) -> list[dict]:
    """Retrieve all messages for a given thread ID."""
    url = f"{threads_base_url}/{urllib.parse.quote(thread_id)}/messages"
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


def export_threads_data(base_url: str, token: str, output_dir: Path, agent_id: str | None = None, max_workers: int = 10) -> dict:
    """Export all threads and their messages to disk concurrently."""
    threads_dir = output_dir / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)

    threads_base_url = resolve_threads_base_url(base_url, token)
    print(f"[*] Querying WXO REST API for message threads (agent_id={agent_id or 'all'})...")
    
    threads = fetch_all_threads(threads_base_url, token, agent_id=agent_id)
    print(f"    Found {len(threads)} message thread(s).")

    summary_records = []
    total_messages = 0

    def process_thread(thread: dict) -> dict:
        thread_id = thread.get("id")
        if not thread_id:
            return {}

        thread_title = thread.get("title") or "Untitled"
        created_on = thread.get("created_on") or thread.get("created_at")
        thread_agent_id = thread.get("agent_id")

        messages = fetch_thread_messages(threads_base_url, token, thread_id)
        msg_count = len(messages)

        thread_payload = {
            "thread": thread,
            "message_count": msg_count,
            "messages": messages,
        }

        thread_file = threads_dir / f"{thread_id}.json"
        thread_file.write_text(json.dumps(thread_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "id": thread_id,
            "title": thread_title,
            "agent_id": thread_agent_id,
            "created_on": created_on,
            "message_count": msg_count,
            "file": f"threads/{thread_id}.json",
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_thread, t): t for t in threads}
        done_count = 0
        for f in as_completed(futures):
            res = f.result()
            if res:
                summary_records.append(res)
                total_messages += res["message_count"]
            done_count += 1
            if done_count % 25 == 0 or done_count == len(threads):
                print(f"    Exported {done_count}/{len(threads)} threads...")

    # Sort summary records by created_on descending or id
    summary_records.sort(key=lambda r: str(r.get("created_on") or ""), reverse=True)

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
        "threads_summary_file": summary_file.relative_to(output_dir).as_posix(),
    }


# ---------------------------------------------------------------------------
# Observability Traces Exporter (agentops-v3 REST API)
# ---------------------------------------------------------------------------

def parse_time_window_to_delta(last_str: str) -> datetime.timedelta:
    """Parse time window strings such as '4h', '24h', '7d', '30d' into timedelta."""
    match = re.match(r"^(\d+)\s*([mhd])$", last_str.strip().lower())
    if not match:
        return datetime.timedelta(hours=24)
    val = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return datetime.timedelta(minutes=val)
    elif unit == "h":
        return datetime.timedelta(hours=val)
    elif unit == "d":
        return datetime.timedelta(days=val)
    return datetime.timedelta(hours=24)


def generate_4h_time_chunks(total_delta: datetime.timedelta) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """Break total time delta into consecutive <= 4 hour windows."""
    chunks = []
    now = datetime.datetime.now(datetime.timezone.utc)
    target_start = now - total_delta
    current_end = now
    max_chunk = datetime.timedelta(hours=3, minutes=55)

    while current_end > target_start:
        current_start = max(target_start, current_end - max_chunk)
        chunks.append((current_start, current_end))
        current_end = current_start

    return chunks


def fetch_and_export_traces(base_url: str, token: str, output_dir: Path, last_window: str = "24h", limit: int = 1000, max_workers: int = 10) -> dict:
    """Export observability traces concurrently using the agentops-v3 REST API."""
    traces_dir = output_dir / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    clean_base = base_url.rstrip("/")
    if clean_base.endswith("/v1/orchestrate"):
        agentops_base = clean_base[:-len("/v1/orchestrate")] + "/v1/agentops-v3"
    else:
        agentops_base = f"{clean_base}/v1/agentops-v3"

    print(f"[*] Querying WXO Observability API for traces (window: {last_window}, limit: {limit})...")
    
    total_delta = parse_time_window_to_delta(last_window)
    time_chunks = generate_4h_time_chunks(total_delta)

    seen_trace_ids = set()
    trace_summaries = []

    for chunk_start, chunk_end in time_chunks:
        from_ts = chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ")
        to_ts = chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ")

        page = 1
        page_size = 50
        while len(trace_summaries) < limit:
            params = {
                "page": str(page),
                "limit": str(page_size),
                "fromTimestamp": from_ts,
                "toTimestamp": to_ts,
            }
            url = f"{agentops_base}/traces?{urllib.parse.urlencode(params)}"
            try:
                resp = make_api_request(url, token)
            except Exception as e:
                # If chunk request fails, log warning and continue
                print(f"    [!] Note: Trace search interval {from_ts} - {to_ts}: {e}", file=sys.stderr)
                break

            items = resp.get("data", []) if isinstance(resp, dict) else []
            if not items:
                break

            for item in items:
                t_id = item.get("id")
                if t_id and t_id not in seen_trace_ids:
                    seen_trace_ids.add(t_id)
                    trace_summaries.append(item)
                    if len(trace_summaries) >= limit:
                        break

            meta = resp.get("meta", {}) if isinstance(resp, dict) else {}
            total_pages = meta.get("totalPages", 1)
            if page >= total_pages or len(items) < page_size:
                break
            page += 1

    print(f"    Found {len(trace_summaries)} trace(s) to export.")

    trace_records = []

    def process_trace(trace_meta: dict) -> dict:
        trace_id = trace_meta.get("id")
        if not trace_id:
            return {}

        trace_file = traces_dir / f"{trace_id}.json"
        detail_url = f"{agentops_base}/traces/{urllib.parse.quote(trace_id)}"

        try:
            full_trace = make_api_request(detail_url, token)
            trace_file.write_text(json.dumps(full_trace, indent=2, ensure_ascii=False), encoding="utf-8")
            return {
                "trace_id": trace_id,
                "timestamp": trace_meta.get("timestamp"),
                "name": trace_meta.get("name"),
                "file": f"traces/{trace_id}.json",
                "status": "exported",
            }
        except Exception as e:
            return {
                "trace_id": trace_id,
                "timestamp": trace_meta.get("timestamp"),
                "name": trace_meta.get("name"),
                "status": "error",
                "error": str(e),
            }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_trace, tm): tm for tm in trace_summaries}
        done_count = 0
        for f in as_completed(futures):
            res = f.result()
            if res:
                trace_records.append(res)
            done_count += 1
            if done_count % 50 == 0 or done_count == len(trace_summaries):
                print(f"    Exported {done_count}/{len(trace_summaries)} traces...")

    # Sort traces by timestamp descending
    trace_records.sort(key=lambda r: str(r.get("timestamp") or ""), reverse=True)

    summary_file = traces_dir / "summary.json"
    summary_payload = {
        "total_traces": len(trace_summaries),
        "exported_count": sum(1 for r in trace_records if r.get("status") == "exported"),
        "search_window": last_window,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "traces": trace_records,
    }
    summary_file.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "total_traces": len(trace_summaries),
        "exported_count": summary_payload["exported_count"],
        "traces_summary_file": summary_file.relative_to(output_dir).as_posix(),
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
        default="24h",
        help="Time window for trace search (e.g., '4h', '24h', '7d', '30d').",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of traces to export.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Concurrent worker threads for downloading chat messages and traces.",
    )
    parser.add_argument(
        "--trace",
        "--traces",
        dest="trace",
        action="store_true",
        help="Enable downloading observability traces (skipped by default).",
    )
    parser.add_argument(
        "--threads-only",
        action="store_true",
        help="Only export REST API message threads and chat messages.",
    )
    parser.add_argument(
        "--traces-only",
        action="store_true",
        help="Only export observability traces (skips message threads).",
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

    token = get_iam_token(wxo_api_key, wxo_env_type)

    manifest = {
        "timestamp": timestamp_str,
        "created_at": now.isoformat(),
        "instance_url": wxo_url,
        "environment_name": wxo_env_name,
        "components": {},
    }

    should_export_traces = (args.trace or args.traces_only) and not args.threads_only
    should_export_threads = not args.traces_only

    # 3. Message Threads via REST API
    if should_export_threads:
        print("\n--- [1/2] Exporting Message Threads via REST API ---")
        threads_stats = export_threads_data(
            base_url=wxo_url,
            token=token,
            output_dir=target_export_dir,
            agent_id=args.agent_id,
            max_workers=args.workers,
        )
        manifest["components"]["threads"] = threads_stats
    else:
        print("\n--- [1/2] Skipping REST API Threads (--traces-only specified) ---")

    # 4. Observability Traces
    if should_export_traces:
        print("\n--- [2/2] Exporting Observability Traces ---")
        traces_stats = fetch_and_export_traces(
            base_url=wxo_url,
            token=token,
            output_dir=target_export_dir,
            last_window=args.last,
            limit=args.limit,
            max_workers=args.workers,
        )
        manifest["components"]["traces"] = traces_stats
    else:
        print("\n--- [2/2] Skipping Observability Traces (pass --trace to enable) ---")

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

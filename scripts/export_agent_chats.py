#!/usr/bin/env python3
"""Export and backup agent conversation threads and observability traces from watsonx Orchestrate.

By default, this script runs with zero arguments, reading credentials from env.cfg,
querying the WXO REST API for all message threads and their messages, and organizing them
into agent-specific subdirectories with human-friendly filenames and Markdown transcripts.

To also download observability execution traces, provide the `--trace` flag.

Usage:
    python scripts/export_agent_chats.py
    python scripts/export_agent_chats.py --trace
    python scripts/export_agent_chats.py --agent translator
    python scripts/export_agent_chats.py --last 24h
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
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
# File Timestamp and Utility Helpers
# ---------------------------------------------------------------------------

def parse_iso_datetime(dt_str: str | None) -> datetime.datetime:
    """Parse ISO date string into datetime object with fallback to now."""
    if not dt_str:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        clean = dt_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def set_file_timestamps(file_path: Path, dt: datetime.datetime) -> None:
    """Set file Modified, Accessed, and Created timestamps."""
    ts = dt.timestamp()
    try:
        os.utime(file_path, (ts, ts))
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            from ctypes import wintypes
            # Convert unix timestamp to Windows FILETIME (100-nanosecond intervals since Jan 1, 1601)
            filetime_val = int((ts + 11644473600) * 10000000)
            low = filetime_val & 0xFFFFFFFF
            high = (filetime_val >> 32) & 0xFFFFFFFF

            class FILETIME(ctypes.Structure):
                _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

            ft = FILETIME(low, high)
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            FILE_SHARE_WRITE = 0x00000002
            OPEN_EXISTING = 3
            FILE_ATTRIBUTE_NORMAL = 0x80

            handle = ctypes.windll.kernel32.CreateFileW(
                str(file_path),
                GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL,
                None,
            )
            if handle not in (-1, 0):
                ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ft), None, ctypes.byref(ft))
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass


def sanitize_filename_slug(text: str, max_length: int = 50) -> str:
    """Convert text into a clean filesystem-friendly slug."""
    if not text:
        return "Untitled"
    # Remove markdown/formatting artifacts
    clean = re.sub(r"[\r\n\t]+", " ", text).strip()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    if not clean:
        return "Untitled"
    return clean[:max_length].rstrip("_")


# ---------------------------------------------------------------------------
# Message Extraction & Agent Detection Engine
# ---------------------------------------------------------------------------

def extract_message_text(content_item: dict | str) -> str:
    """Extract plain text from various WXO message content blocks."""
    if isinstance(content_item, str):
        return content_item
    if isinstance(content_item, dict):
        if "text" in content_item:
            return content_item["text"]
        if content_item.get("response_type") == "forms":
            schema = content_item.get("json_schema") or {}
            title = schema.get("title") or "Form"
            return f"[Form: {title}]"
    return ""


def parse_clean_transcript(messages: list[dict]) -> tuple[list[dict], str]:
    """Parse messages into clean turns and extract first user message."""
    transcript = []
    first_user_prompt = ""

    for msg in messages:
        role = msg.get("role") or "unknown"
        created_on = msg.get("created_on") or msg.get("created_at")
        content_items = msg.get("content") or []
        
        texts = []
        citations = []
        for c in content_items:
            t = extract_message_text(c)
            if t:
                texts.append(t)
            if isinstance(c, dict) and "citations" in c:
                for cit in c.get("citations") or []:
                    c_title = cit.get("title") or cit.get("url") or "Document"
                    citations.append(c_title)

        combined_text = "\n\n".join(texts) if texts else "[No text content]"

        # Collect tools used
        tools_used = []
        step_hist = msg.get("step_history") or []
        for step in step_hist:
            for sd in step.get("step_details") or []:
                for tc in sd.get("tool_calls") or []:
                    t_name = tc.get("name")
                    if t_name and t_name not in tools_used:
                        tools_used.append(t_name)

        turn = {
            "role": role,
            "timestamp": created_on,
            "text": combined_text,
        }
        if tools_used:
            turn["tools_used"] = tools_used
        if citations:
            turn["citations"] = list(dict.fromkeys(citations))

        transcript.append(turn)

        if role == "user" and not first_user_prompt and combined_text:
            first_user_prompt = combined_text

    return transcript, first_user_prompt


def detect_agent_for_thread(thread: dict, messages: list[dict], catalog: dict[str, str]) -> str:
    """Identify which agent handled this conversation."""
    # 1. Direct thread agent_id
    tid = thread.get("agent_id") or thread.get("assistant_id")
    if tid and tid in catalog:
        return catalog[tid]

    # 2. Inspect messages and step history
    for m in messages:
        step_hist = m.get("step_history") or []
        for step in step_hist:
            for sd in step.get("step_details") or []:
                agent_name = sd.get("agent_display_name")
                if agent_name and agent_name not in ("kb_retrieval_probe_tmp", "default", "unknown"):
                    return agent_name

                for tc in sd.get("tool_calls") or []:
                    t_name = tc.get("name", "").lower()
                    if any(k in t_name for k in ("incident", "remediation", "service", "cluster", "deployment")):
                        return "incident_triage"
                    if "greeting" in t_name:
                        return "hello_world"
                    if "translate" in t_name:
                        return "translator"

        # 3. Inspect message contents
        for c in m.get("content") or []:
            if isinstance(c, dict):
                r_type = c.get("response_type")
                if r_type == "conversational_search":
                    cits = c.get("citations") or []
                    for cit in cits:
                        cit_title = str(cit.get("title", "")).lower()
                        if "runbook" in cit_title:
                            return "incident_triage"
                    return "travel_rules_qa"

                if r_type == "forms" or "Travel Request" in str(c):
                    return "travel_request"

                txt = c.get("text", "")
                if any(k in txt for k in ("Finnish travel", "hotel price", "per diem", "allowance", "reimbursement")):
                    return "travel_rules_qa"
                if any(k in txt for k in ("INC-", "Runbook ID", "RB-DEPLOY", "remediation action")):
                    return "incident_triage"
                if "Hello World!" in txt:
                    return "hello_world"

    return "general"


def generate_markdown_transcript(agent_name: str, thread: dict, transcript: list[dict], thread_id: str) -> str:
    """Format conversation transcript into clean human-readable Markdown."""
    created_on = thread.get("created_on") or "N/A"
    title = thread.get("title") or "Untitled Conversation"
    
    md_lines = [
        f"# Chat Transcript: {agent_name}",
        f"**Title:** {title}  ",
        f"**Date:** {created_on} | **Messages:** {len(transcript)} | **Thread ID:** `{thread_id}`",
        "\n---\n",
    ]

    for turn in transcript:
        role = turn["role"].capitalize()
        ts = turn.get("timestamp") or ""
        ts_display = f" ({ts.split('T')[1][:8]} UTC)" if "T" in ts else ""
        icon = "👤" if turn["role"] == "user" else "🤖"
        
        md_lines.append(f"### {icon} {role}{ts_display}\n")
        
        # Quote user text, regular paragraph for agent text
        text = turn.get("text", "")
        if turn["role"] == "user":
            quoted = "\n".join(f"> {line}" for line in text.splitlines())
            md_lines.append(f"{quoted}\n")
        else:
            md_lines.append(f"{text}\n")

        if turn.get("tools_used"):
            tools_str = ", ".join(f"`{t}`" for t in turn["tools_used"])
            md_lines.append(f"🛠️ *Tools Used:* {tools_str}\n")

        if turn.get("citations"):
            citations_str = ", ".join(f"_{c}_" for c in turn["citations"])
            md_lines.append(f"📚 *Sources:* {citations_str}\n")

        md_lines.append("")

    return "\n".join(md_lines)


# ---------------------------------------------------------------------------
# Message Threads & Chat Exporter (REST API)
# ---------------------------------------------------------------------------

def resolve_threads_base_url(base_url: str, token: str) -> str:
    """Determine whether threads are hosted under /v1/orchestrate/threads or /v1/threads."""
    clean_base = base_url.rstrip("/")
    for candidate in (f"{clean_base}/v1/orchestrate/threads", f"{clean_base}/v1/threads"):
        try:
            make_api_request(f"{candidate}?limit=1&offset=0", token)
            return candidate
        except Exception:
            continue
    return f"{clean_base}/v1/orchestrate/threads"


def fetch_agent_catalog(base_url: str, token: str) -> dict[str, str]:
    """Fetch map of agent_id -> agent_name from WXO instance."""
    clean_base = base_url.rstrip("/")
    for path in ("/v1/orchestrate/agents", "/v1/agents"):
        try:
            res = make_api_request(f"{clean_base}{path}", token)
            if isinstance(res, list):
                return {a["id"]: a.get("name") or a["id"] for a in res if "id" in a}
            if isinstance(res, dict) and "data" in res:
                return {a["id"]: a.get("name") or a["id"] for a in res["data"] if "id" in a}
        except Exception:
            continue
    return {}


def fetch_all_threads(threads_base_url: str, token: str, agent_id: str | None = None) -> list[dict]:
    """Retrieve all message threads without early pagination cutoff."""
    params = {}
    if agent_id:
        params["agent_id"] = agent_id

    initial_url = f"{threads_base_url}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    res = make_api_request(initial_url, token)

    if isinstance(res, list):
        return res

    if isinstance(res, dict):
        total = res.get("total")
        items = res.get("data") or res.get("items") or []
        if total is None or len(items) >= total:
            return items

    threads = []
    offset = 0
    while True:
        p = {"offset": str(offset), "limit": "100"}
        if agent_id:
            p["agent_id"] = agent_id
        url_page = f"{threads_base_url}?{urllib.parse.urlencode(p)}"
        resp = make_api_request(url_page, token)

        if isinstance(resp, dict):
            items = resp.get("data") or resp.get("items") or []
            total = resp.get("total")
        elif isinstance(resp, list):
            items = resp
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


def export_threads_data(base_url: str, token: str, output_dir: Path, agent_filter: str | None = None, max_workers: int = 10) -> dict:
    """Export all threads organized into agent-specific subdirectories with clean JSON and Markdown."""
    agent_catalog = fetch_agent_catalog(base_url, token)
    resolved_agent_id = None
    if agent_filter:
        for aid, aname in agent_catalog.items():
            if agent_filter.lower() in (aid.lower(), aname.lower()):
                resolved_agent_id = aid
                break
        if not resolved_agent_id:
            resolved_agent_id = agent_filter

    threads_base_url = resolve_threads_base_url(base_url, token)
    print(f"[*] Querying WXO REST API for all message threads (agent filter: {agent_filter or 'all'})...")
    if agent_catalog:
        print(f"    Registered agents in instance: {', '.join(agent_catalog.values())}")
    
    threads = fetch_all_threads(threads_base_url, token, agent_id=resolved_agent_id)
    print(f"    Found {len(threads)} total message thread(s).")

    agent_records: dict[str, list[dict]] = {}
    total_messages = 0

    def process_thread(thread: dict) -> dict:
        thread_id = thread.get("id")
        if not thread_id:
            return {}

        created_on = thread.get("created_on") or thread.get("created_at")
        thread_dt = parse_iso_datetime(created_on)

        messages = fetch_thread_messages(threads_base_url, token, thread_id)
        msg_count = len(messages)

        transcript, first_user_prompt = parse_clean_transcript(messages)
        agent_name = detect_agent_for_thread(thread, messages, agent_catalog)

        # Build human-friendly filename: YYYYMMDD_HHMMSS_<prompt_slug>_<short_id>
        time_prefix = thread_dt.strftime("%Y%m%d_%H%M%S")
        slug = sanitize_filename_slug(first_user_prompt or thread.get("title") or "chat")
        short_id = thread_id[:6]
        base_filename = f"{time_prefix}_{slug}_{short_id}"

        agent_dir = output_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        json_path = agent_dir / f"{base_filename}.json"
        md_path = agent_dir / f"{base_filename}.md"

        # Structured JSON payload
        thread_payload = {
            "thread_id": thread_id,
            "agent": agent_name,
            "created_on": created_on,
            "message_count": msg_count,
            "first_prompt": first_user_prompt,
            "transcript": transcript,
            "raw_thread": thread,
            "raw_messages": messages,
        }
        json_path.write_text(json.dumps(thread_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        # Markdown transcript
        md_content = generate_markdown_transcript(agent_name, thread, transcript, thread_id)
        md_path.write_text(md_content, encoding="utf-8")

        # Adjust creation and modification times to match thread conversation start
        set_file_timestamps(json_path, thread_dt)
        set_file_timestamps(md_path, thread_dt)

        return {
            "id": thread_id,
            "agent": agent_name,
            "title": thread.get("title") or "Untitled",
            "created_on": created_on,
            "first_prompt": first_user_prompt[:80],
            "message_count": msg_count,
            "json_file": json_path.relative_to(output_dir).as_posix(),
            "md_file": md_path.relative_to(output_dir).as_posix(),
            "created_dt": thread_dt,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_thread, t): t for t in threads}
        done_count = 0
        for f in as_completed(futures):
            res = f.result()
            if res:
                agent = res["agent"]
                if agent not in agent_records:
                    agent_records[agent] = []
                agent_records[agent].append(res)
                total_messages += res["message_count"]
            done_count += 1
            if done_count % 50 == 0 or done_count == len(threads):
                print(f"    Exported {done_count}/{len(threads)} threads...")

    # Write per-agent summary.json
    agent_summary_counts = {}
    for agent, records in agent_records.items():
        records.sort(key=lambda r: r["created_dt"], reverse=True)
        agent_dir = output_dir / agent
        summary_payload = {
            "agent": agent,
            "total_threads": len(records),
            "total_messages": sum(r["message_count"] for r in records),
            "threads": [
                {k: v for k, v in r.items() if k != "created_dt"}
                for r in records
            ],
        }
        summary_file = agent_dir / "summary.json"
        summary_file.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        agent_summary_counts[agent] = {
            "threads": len(records),
            "messages": sum(r["message_count"] for r in records),
        }

    return {
        "total_threads": len(threads),
        "total_messages": total_messages,
        "agents": agent_summary_counts,
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

        trace_dt = parse_iso_datetime(trace_meta.get("timestamp"))
        time_prefix = trace_dt.strftime("%Y%m%d_%H%M%S")
        trace_name = sanitize_filename_slug(trace_meta.get("name") or "trace")
        short_id = trace_id[:6]
        base_filename = f"{time_prefix}_{trace_name}_{short_id}"

        trace_file = traces_dir / f"{base_filename}.json"
        detail_url = f"{agentops_base}/traces/{urllib.parse.quote(trace_id)}"

        try:
            full_trace = make_api_request(detail_url, token)
            trace_file.write_text(json.dumps(full_trace, indent=2, ensure_ascii=False), encoding="utf-8")
            set_file_timestamps(trace_file, trace_dt)
            return {
                "trace_id": trace_id,
                "timestamp": trace_meta.get("timestamp"),
                "name": trace_meta.get("name"),
                "file": trace_file.relative_to(output_dir).as_posix(),
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
# Root Export Documentation (README.md)
# ---------------------------------------------------------------------------

def write_root_export_readme(export_dir: Path, manifest: dict) -> None:
    """Generate a clean overview README.md in the export folder."""
    timestamp = manifest.get("timestamp", "")
    created_at = manifest.get("created_at", "")
    instance_url = manifest.get("instance_url", "")
    env_name = manifest.get("environment_name", "")

    threads_stat = manifest.get("components", {}).get("threads", {})
    traces_stat = manifest.get("components", {}).get("traces", {})

    lines = [
        f"# WXO Agent Chats Export Report",
        f"**Export Timestamp:** `{timestamp}` ({created_at})  ",
        f"**Environment:** `{env_name}`  ",
        f"**Instance:** `{instance_url}`\n",
        "## Agent Breakdown\n",
        "| Agent Directory | Total Conversations | Total Messages | Link |",
        "| :--- | :--- | :--- | :--- |",
    ]

    agents_info = threads_stat.get("agents", {})
    for agent, counts in sorted(agents_info.items(), key=lambda x: x[0]):
        lines.append(f"| **`{agent}/`** | {counts['threads']} | {counts['messages']} | [{agent}/summary.json]({agent}/summary.json) |")

    lines.append(f"\n**Total Conversations:** {threads_stat.get('total_threads', 0)} | **Total Messages:** {threads_stat.get('total_messages', 0)}\n")

    if traces_stat:
        lines.append("## Observability Traces\n")
        lines.append(f"- **Discovered Traces:** {traces_stat.get('total_traces', 0)}")
        lines.append(f"- **Exported Traces:** {traces_stat.get('exported_count', 0)}")
        lines.append(f"- **Traces Index:** [traces/summary.json](traces/summary.json)\n")

    lines.append("## File Formats\n")
    lines.append("- **`.md` files**: Clean, human-readable Markdown chat transcripts ready to view in any text editor.")
    lines.append("- **`.json` files**: Complete structured data including clean turn summaries and raw WXO schemas.")
    lines.append("- **File timestamps**: Set to each conversation's initial start time for intuitive sorting.\n")

    readme_path = export_dir / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")


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
        "--agent",
        "--agent-id",
        dest="agent",
        type=str,
        default=None,
        help="Optional agent name (e.g., 'translator', 'incident_triage') or UUID to filter message threads.",
    )
    parser.add_argument(
        "--trace",
        "--traces",
        dest="trace",
        action="store_true",
        help="Enable downloading observability traces (skipped by default).",
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
        print("\n--- [1/2] Exporting Message Threads into Agent Directories ---")
        threads_stats = export_threads_data(
            base_url=wxo_url,
            token=token,
            output_dir=target_export_dir,
            agent_filter=args.agent,
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

    # 5. Write Manifest and Root Report
    duration_sec = round(time.time() - start_time, 2)
    manifest["duration_seconds"] = duration_sec
    manifest_file = target_export_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    write_root_export_readme(target_export_dir, manifest)

    # 6. Final Summary Report
    print("\n" + "=" * 70)
    print(" BACKUP COMPLETED SUCCESSFULLY")
    print("=" * 70)
    if "threads" in manifest["components"]:
        t_stat = manifest["components"]["threads"]
        print(f"  * Total Conversations: {t_stat.get('total_threads', 0)}")
        print(f"  * Total Messages:      {t_stat.get('total_messages', 0)}")
        agents_info = t_stat.get("agents", {})
        for ag, cnts in sorted(agents_info.items()):
            print(f"    - {ag}/: {cnts['threads']} chats ({cnts['messages']} messages)")
    if "traces" in manifest["components"]:
        tr_stat = manifest["components"]["traces"]
        print(f"  * Traces Discovered:   {tr_stat.get('total_traces', 0)}")
        print(f"  * Traces Exported:     {tr_stat.get('exported_count', 0)}")
    print(f"  * Overview Report:     {target_export_dir / 'README.md'}")
    print(f"  * Manifest:            {manifest_file}")
    print(f"  * Time Elapsed:        {duration_sec}s")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

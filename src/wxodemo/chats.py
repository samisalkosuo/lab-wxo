"""Export agent conversations (API threads and Web UI chats from traces) to Markdown and JSON.

Reads credentials from env.cfg through the shared config, exchanges the API key for a token
(IAM or MCSP) and reads from the watsonx Orchestrate REST API. Nothing is changed in WXO.
Output goes to export/<timestamp>/<agent>/*.md|json, with summary.json per agent plus a
manifest.json and README.md at the top.
"""

from __future__ import annotations

import ctypes
import datetime as dt
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wxodemo.config import Config, UsageError
from wxodemo.logging_setup import get_logger, ok, plain, register_secret, warn

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
MCSP_URL = "https://iam.platform.saas.ibm.com/saas/v1/auth/token"
USER_AGENT = "wxodemo/1.0"
TRACE_PAGE_SIZE = 50
TRACE_MAX_PAGES = 10
# The traces API rejects windows longer than 4 hours.
MAX_CHUNK = dt.timedelta(hours=3, minutes=55)


class ExportError(Exception):
    """The export could not run (authentication or API failure). Exit code 1."""


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def get_token(cfg: Config) -> str:
    """Exchange the API key for an access token (IAM, or MCSP for AWS-hosted instances)."""
    url = MCSP_URL if cfg.env_type.lower() == "mcsp" else IAM_URL
    payload = urllib.parse.urlencode(
        {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": cfg.api_key}
    ).encode("utf-8")
    request = urllib.request.Request(
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
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https URL
            token = json.loads(response.read().decode("utf-8")).get("access_token")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        get_logger().debug("token exchange failed: HTTP %s %s", exc.code, body)
        raise ExportError(
            f"Authentication failed (HTTP {exc.code}). "
            f"Check WXO_API_KEY and WXO_ENV_TYPE in env.cfg."
        ) from exc
    except (urllib.error.URLError, ValueError, OSError) as exc:
        raise ExportError(f"Could not obtain an access token: {exc}") from exc
    if not token:
        raise ExportError("The token response did not contain an access_token.")
    register_secret(token)
    return token


class Api:
    """Authenticated JSON requests against the WXO REST API, with retries."""

    def __init__(self, token: str) -> None:
        self.token = token

    def request(
        self, url: str, *, method: str = "GET", body: dict | None = None, retries: int = 3
    ) -> Any:
        data = json.dumps(body).encode("utf-8") if body else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }
        last: Exception | None = None
        for attempt in range(retries):
            request = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                    content = response.read().decode("utf-8")
                    return json.loads(content) if content else {}
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise ExportError(f"HTTP {exc.code} on {url}: {detail}") from exc
            except (urllib.error.URLError, http.client.HTTPException, ValueError, OSError) as exc:
                last = exc
                if attempt < retries - 1:
                    time.sleep(attempt + 1)
        raise ExportError(f"Request failed after {retries} attempts: {url}: {last}")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def parse_iso(value: str | None) -> dt.datetime:
    """ISO timestamp to datetime; now (UTC) when missing or unparsable."""
    if value:
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)
        except ValueError:
            pass
    return dt.datetime.now(dt.UTC)


def parse_window(text: str) -> dt.timedelta:
    """'90m', '24h' or '7d' to a timedelta."""
    match = re.fullmatch(r"(\d+)\s*([mhd])", text.strip().lower())
    if not match:
        raise UsageError(f"--last '{text}' is not valid. Use a number and m, h or d: 90m, 24h, 7d.")
    value, unit = int(match.group(1)), match.group(2)
    if value <= 0:
        raise UsageError("--last must be greater than zero.")
    return {"m": dt.timedelta(minutes=value), "h": dt.timedelta(hours=value)}.get(
        unit, dt.timedelta(days=value)
    )


def time_chunks(
    total: dt.timedelta, now: dt.datetime | None = None
) -> list[tuple[dt.datetime, dt.datetime]]:
    """Consecutive windows of at most MAX_CHUNK, newest first, covering `total`."""
    end = now or dt.datetime.now(dt.UTC)
    start_limit = end - total
    chunks = []
    while end > start_limit:
        start = max(start_limit, end - MAX_CHUNK)
        chunks.append((start, end))
        end = start
    return chunks


def slugify(text: str, max_length: int = 50) -> str:
    """Filesystem-friendly slug; 'Untitled' when nothing usable is left."""
    clean = re.sub(r"[\r\n\t]+", " ", text or "").strip()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    return clean[:max_length].rstrip("_") if clean else "Untitled"


def set_file_times(path: Path, when: dt.datetime) -> None:
    """Give a file the conversation's time as modified/accessed (and created, on Windows)."""
    stamp = when.timestamp()
    try:
        os.utime(path, (stamp, stamp))
    except OSError:
        return
    if sys.platform != "win32":
        return
    try:
        from ctypes import wintypes

        value = int((stamp + 11644473600) * 10_000_000)

        class FILETIME(ctypes.Structure):
            _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

        filetime = FILETIME(value & 0xFFFFFFFF, (value >> 32) & 0xFFFFFFFF)
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CreateFileW.restype = ctypes.c_void_p
        handle = kernel32.CreateFileW(str(path), 0x40000000, 0x3, None, 3, 0x80, None)
        if handle not in (None, 0, ctypes.c_void_p(-1).value):
            kernel32.SetFileTime(
                ctypes.c_void_p(handle), ctypes.byref(filetime), None, ctypes.byref(filetime)
            )
            kernel32.CloseHandle(ctypes.c_void_p(handle))
    except Exception:  # noqa: BLE001 - creation time is cosmetic; modified time is already set
        get_logger().debug("could not set creation time on %s", path, exc_info=True)


# ---------------------------------------------------------------------------
# Messages and transcripts
# ---------------------------------------------------------------------------


def message_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        if "text" in item:
            return item["text"]
        if item.get("response_type") == "forms":
            title = (item.get("json_schema") or {}).get("title") or "Form"
            return f"[Form: {title}]"
    return ""


def parse_transcript(messages: list[dict]) -> tuple[list[dict], str]:
    """(turns, first user prompt) from thread messages."""
    transcript: list[dict] = []
    first_prompt = ""
    for msg in messages:
        role = msg.get("role") or "unknown"
        texts: list[str] = []
        citations: list[str] = []
        for item in msg.get("content") or []:
            text = message_text(item)
            if text:
                texts.append(text)
            if isinstance(item, dict):
                for cit in item.get("citations") or []:
                    citations.append(cit.get("title") or cit.get("url") or "Document")

        tools: list[str] = []
        for step in msg.get("step_history") or []:
            for detail in step.get("step_details") or []:
                for call in detail.get("tool_calls") or []:
                    name = call.get("name")
                    if name and name not in tools:
                        tools.append(name)

        combined = "\n\n".join(texts) if texts else "[No text content]"
        turn: dict[str, Any] = {
            "role": role,
            "timestamp": msg.get("created_on") or msg.get("created_at"),
            "text": combined,
        }
        if tools:
            turn["tools_used"] = tools
        if citations:
            turn["citations"] = list(dict.fromkeys(citations))
        transcript.append(turn)
        if role == "user" and not first_prompt and texts:
            first_prompt = combined
    return transcript, first_prompt


# Fallback guesses for threads that carry no agent id. Keyword -> agent name.
_TOOL_HINTS = (
    (("incident", "remediation", "service", "cluster", "deployment"), "incident_triage"),
    (("hr_", "onboarding", "hire", "provision"), "hr_onboarding"),
    (("returns_", "refund", "warranty"), "customer_returns"),
    (("travel_", "per_diem", "reimbursement"), "travel_request"),
    (("release", "cve", "runbooks_index"), "release_readiness"),
    (("greeting",), "hello_world"),
    (("translate",), "translator"),
)
_TEXT_HINTS = (
    (
        ("Finnish travel", "hotel price", "per diem", "allowance", "reimbursement"),
        "travel_rules_qa",
    ),
    (("INC-", "Runbook ID", "RB-DEPLOY", "remediation action"), "incident_triage"),
    (("HR-POL-", "H-100", "onboard", "provisioning"), "hr_onboarding"),
    (("RP-", "ORD-", "refund", "return"), "customer_returns"),
    (("TP-", "travel request"), "travel_request"),
    (("RR-", "release readiness"), "release_readiness"),
    (("Hello World!",), "hello_world"),
)


def detect_agent(thread: dict, messages: list[dict], catalog: dict[str, str]) -> str:
    """Which agent handled this conversation: catalog lookup first, then content hints."""
    agent_id = thread.get("agent_id") or thread.get("assistant_id")
    if agent_id and agent_id in catalog:
        return catalog[agent_id]

    for msg in messages:
        for step in msg.get("step_history") or []:
            for detail in step.get("step_details") or []:
                shown = detail.get("agent_display_name")
                if shown and shown not in ("kb_retrieval_probe_tmp", "default", "unknown"):
                    return shown
                for call in detail.get("tool_calls") or []:
                    tool = (call.get("name") or "").lower()
                    for words, agent in _TOOL_HINTS:
                        if any(word in tool for word in words):
                            return agent

        for item in msg.get("content") or []:
            if not isinstance(item, dict):
                continue
            kind = item.get("response_type")
            if kind == "conversational_search":
                for cit in item.get("citations") or []:
                    if "runbook" in str(cit.get("title", "")).lower():
                        return "incident_triage"
                return "travel_rules_qa"
            if kind == "forms":
                schema_title = str((item.get("json_schema") or {}).get("title") or "")
                item_str = str(item)
                if "Provisioning" in schema_title or "HR Manager" in item_str:
                    return "hr_onboarding"
                if "Remediation" in schema_title:
                    return "incident_triage"
                if "Return" in schema_title:
                    return "customer_returns"
                if "Travel" in schema_title or "Travel Request" in item_str:
                    return "travel_request"
            if "Travel Request" in str(item):
                return "travel_request"
            text = item.get("text", "")
            for words, agent in _TEXT_HINTS:
                if any(word in text for word in words):
                    return agent
    return "general"


def render_markdown(
    agent: str, title: str, created_on: str, transcript: list[dict], item_id: str
) -> str:
    lines = [
        f"# Chat Transcript: {agent}",
        f"**Topic:** {title}  ",
        f"**Date:** {created_on} | **Messages:** {len(transcript)} | **ID:** `{item_id}`",
        "\n---\n",
    ]
    for turn in transcript:
        stamp = turn.get("timestamp") or ""
        shown = f" ({stamp.split('T')[1][:8]} UTC)" if "T" in stamp else ""
        who = "User" if turn["role"] == "user" else turn["role"].capitalize()
        lines.append(f"### {who}{shown}\n")
        text = turn.get("text", "")
        if turn["role"] == "user":
            lines.append("\n".join(f"> {line}" for line in text.splitlines()) + "\n")
        else:
            lines.append(f"{text}\n")
        if turn.get("model"):
            lines.append(f"*Model:* `{turn['model']}`\n")
        if turn.get("tools_used"):
            lines.append("*Tools used:* " + ", ".join(f"`{t}`" for t in turn["tools_used"]) + "\n")
        if turn.get("citations"):
            lines.append("*Sources:* " + ", ".join(f"_{c}_" for c in turn["citations"]) + "\n")
        lines.append("")
    return "\n".join(lines)


def trace_user_text(trace: dict) -> str:
    data = trace.get("input", {})
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return ""
    content = data.get("content") or []
    if isinstance(content, list) and content:
        return content[0].get("text", "") if isinstance(content[0], dict) else ""
    if isinstance(content, str) and content:
        return content
    return data.get("text", "")


def trace_answer(trace: dict) -> tuple[str, str, list[str]]:
    """(assistant text, model, tools used) from a trace's observations."""
    answer = model = ""
    tools: list[str] = []
    for obs in trace.get("observations", []):
        kind = obs.get("type")
        if kind == "GENERATION":
            model = model or obs.get("model") or ""
            out = obs.get("output") or {}
            if isinstance(out, dict) and "content" in out:
                answer = out["content"]
            elif isinstance(out, str):
                answer = out
        elif kind in ("TOOL", "SPAN") and obs.get("name"):
            name = obs["name"]
            if not name.startswith(("POST ", "GET ")) and name not in (
                "LangGraph",
                "agent",
                "answer",
            ):
                tools.append(name)
    if not answer and isinstance(trace.get("output"), dict):
        answer = str(trace["output"])
    return answer, model, list(dict.fromkeys(tools))


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------


@dataclass
class Exporter:
    api: Api
    base_url: str
    output_dir: Path
    agent_filter: str | None = None
    last: str = "7d"
    raw_traces: bool = False
    workers: int = 10
    catalog: dict[str, str] = field(default_factory=dict)
    records: dict[str, list[dict]] = field(default_factory=dict)
    seen_threads: set[str] = field(default_factory=set)
    _agent_id: str | None = None

    # -- discovery ---------------------------------------------------------

    @property
    def root(self) -> str:
        return self.base_url.rstrip("/")

    def load_catalog(self) -> None:
        for path in ("/v1/orchestrate/agents", "/v1/agents"):
            try:
                result = self.api.request(f"{self.root}{path}")
            except ExportError:
                get_logger().debug("agent catalog not at %s", path, exc_info=True)
                continue
            items = result if isinstance(result, list) else (result or {}).get("data")
            if isinstance(items, list):
                self.catalog = {a["id"]: a.get("name") or a["id"] for a in items if "id" in a}
                return

    def resolve_filter(self) -> None:
        if not self.agent_filter:
            return
        wanted = self.agent_filter.lower()
        for agent_id, name in self.catalog.items():
            if wanted in (agent_id.lower(), name.lower()):
                self._agent_id = agent_id
                return
        self._agent_id = self.agent_filter

    def wanted(self, agent_name: str, agent_id: str | None) -> bool:
        if not self.agent_filter:
            return True
        return agent_name.lower() == self.agent_filter.lower() or agent_id == self._agent_id

    def threads_url(self) -> str:
        for candidate in (f"{self.root}/v1/orchestrate/threads", f"{self.root}/v1/threads"):
            try:
                self.api.request(f"{candidate}?limit=1&offset=0")
                return candidate
            except ExportError:
                continue
        return f"{self.root}/v1/orchestrate/threads"

    # -- writing -----------------------------------------------------------

    def write_chat(
        self, agent: str, when: dt.datetime, prompt: str, item_id: str, payload: dict, markdown: str
    ) -> tuple[Path, Path]:
        folder = self.output_dir / agent
        folder.mkdir(parents=True, exist_ok=True)
        base = f"{when.strftime('%Y%m%d_%H%M%S')}_{slugify(prompt)}_{item_id[:6]}"
        json_path, md_path = folder / f"{base}.json", folder / f"{base}.md"
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(markdown, encoding="utf-8")
        set_file_times(json_path, when)
        set_file_times(md_path, when)
        return json_path, md_path

    def _record(self, **fields: Any) -> dict:
        json_path, md_path = fields.pop("paths")
        return {
            **fields,
            "json_file": json_path.relative_to(self.output_dir).as_posix(),
            "md_file": md_path.relative_to(self.output_dir).as_posix(),
        }

    # -- threads -----------------------------------------------------------

    def _thread(self, base: str, thread: dict) -> dict:
        thread_id = thread.get("id")
        if not thread_id:
            return {}
        created = thread.get("created_on") or thread.get("created_at")
        when = parse_iso(created)
        try:
            result = self.api.request(f"{base}/{urllib.parse.quote(thread_id)}/messages")
        except ExportError:
            get_logger().debug("messages for thread %s unavailable", thread_id, exc_info=True)
            return {}
        messages = (
            result
            if isinstance(result, list)
            else (result.get("data") or result.get("messages") or [])
        )
        if not messages:
            return {}

        transcript, prompt = parse_transcript(messages)
        agent = detect_agent(thread, messages, self.catalog)
        if not self.wanted(agent, thread.get("agent_id")):
            return {}

        payload = {
            "source": "api_thread",
            "thread_id": thread_id,
            "agent": agent,
            "created_on": created,
            "message_count": len(messages),
            "first_prompt": prompt,
            "transcript": transcript,
            "raw_thread": thread,
            "raw_messages": messages,
        }
        markdown = render_markdown(
            agent, prompt or "Conversation", created or "", transcript, thread_id
        )
        paths = self.write_chat(
            agent, when, prompt or thread.get("title") or "chat", thread_id, payload, markdown
        )
        return self._record(
            id=thread_id,
            source="api_thread",
            agent=agent,
            title=thread.get("title") or "Untitled",
            created_on=created,
            first_prompt=prompt[:80],
            message_count=len(messages),
            created_dt=when,
            paths=paths,
        )

    def export_threads(self) -> None:
        base = self.threads_url()
        plain("Reading message threads ...")
        url = base + (f"?agent_id={self._agent_id}" if self._agent_id else "")
        threads: list[dict] = []
        try:
            result = self.api.request(url)
            threads = (
                result
                if isinstance(result, list)
                else (result.get("data") or result.get("items") or [])
            )
        except ExportError as exc:
            warn(f"Could not list threads: {exc}")
        plain(f"  found {len(threads)} thread(s)")
        self._collect(self.workers, [(self._thread, base, t) for t in threads], remember=True)

    # -- traces ------------------------------------------------------------

    def agentops_url(self) -> str:
        suffix = "/v1/orchestrate"
        root = self.root[: -len(suffix)] if self.root.endswith(suffix) else self.root
        return f"{root}/v1/agentops-v3"

    def discover_traces(self, base: str) -> list[dict]:
        found: list[dict] = []
        seen: set[str] = set()
        for start, end in time_chunks(parse_window(self.last)):
            for page in range(1, TRACE_MAX_PAGES + 1):
                query = urllib.parse.urlencode(
                    {
                        "page": str(page),
                        "limit": str(TRACE_PAGE_SIZE),
                        "fromTimestamp": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "toTimestamp": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )
                try:
                    response = self.api.request(f"{base}/traces?{query}")
                except ExportError:
                    get_logger().debug("trace page failed", exc_info=True)
                    break
                items = response.get("data", []) if isinstance(response, dict) else []
                for item in items:
                    trace_id = item.get("id")
                    if trace_id and trace_id not in seen:
                        seen.add(trace_id)
                        found.append(item)
                meta = response.get("meta", {}) if isinstance(response, dict) else {}
                if not items or len(items) < TRACE_PAGE_SIZE or page >= meta.get("totalPages", 1):
                    break
        return found

    def _trace(self, base: str, meta: dict) -> dict:
        trace_id = meta.get("id")
        if not trace_id:
            return {}
        when = parse_iso(meta.get("timestamp"))
        try:
            trace = self.api.request(f"{base}/traces/{urllib.parse.quote(trace_id)}")
        except ExportError:
            get_logger().debug("trace %s unavailable", trace_id, exc_info=True)
            return {}

        if self.raw_traces:
            raw_dir = self.output_dir / "raw_traces"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw = raw_dir / f"{trace_id}.json"
            raw.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
            set_file_times(raw, when)

        output = trace.get("output")
        thread_id = output.get("thread_id") if isinstance(output, dict) else None
        conversation = trace.get("conversationId") or trace.get("sessionId")
        if thread_id in self.seen_threads or conversation in self.seen_threads:
            return {}  # already exported as a thread

        agent_id = trace.get("agentId")
        agent = self.catalog.get(agent_id) if agent_id else None
        agent = agent or "general"
        if not self.wanted(agent, agent_id):
            return {}

        user_text = trace_user_text(trace)
        if not user_text:
            return {}
        answer, model, tools = trace_answer(trace)
        stamp = trace.get("timestamp")
        transcript = [
            {"role": "user", "timestamp": stamp, "text": user_text},
            {
                "role": "assistant",
                "timestamp": trace.get("createdAt") or stamp,
                "text": answer or "[Response processed]",
                "model": model,
                "tools_used": tools,
            },
        ]
        payload = {
            "source": "web_ui_trace_run",
            "trace_id": trace_id,
            "agent": agent,
            "created_on": stamp,
            "message_count": len(transcript),
            "first_prompt": user_text,
            "transcript": transcript,
            "raw_trace": trace,
        }
        markdown = render_markdown(agent, user_text, stamp or "", transcript, trace_id)
        paths = self.write_chat(agent, when, user_text, trace_id, payload, markdown)
        return self._record(
            id=trace_id,
            source="web_ui_trace",
            agent=agent,
            title=user_text[:60],
            created_on=stamp,
            first_prompt=user_text[:80],
            message_count=len(transcript),
            created_dt=when,
            paths=paths,
        )

    def export_traces(self) -> None:
        base = self.agentops_url()
        plain(f"Reading Web UI chats from traces (last {self.last}) ...")
        traces = self.discover_traces(base)
        plain(f"  found {len(traces)} trace(s)")
        self._collect(self.workers, [(self._trace, base, t) for t in traces], remember=False)

    # -- shared ------------------------------------------------------------

    def _collect(self, workers: int, jobs: list[tuple], *, remember: bool) -> None:
        if not jobs:
            return
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = [pool.submit(fn, *args) for fn, *args in jobs]
            for done, future in enumerate(as_completed(futures), 1):
                record = future.result()
                if record:
                    self.records.setdefault(record["agent"], []).append(record)
                    if remember:
                        self.seen_threads.add(record["id"])
                if done % 50 == 0 or done == len(futures):
                    plain(f"  processed {done}/{len(futures)}")

    def write_summaries(self) -> dict[str, dict[str, int]]:
        per_agent: dict[str, dict[str, int]] = {}
        for agent, records in self.records.items():
            records.sort(key=lambda r: r["created_dt"], reverse=True)
            total = sum(r["message_count"] for r in records)
            summary = {
                "agent": agent,
                "total_conversations": len(records),
                "total_messages": total,
                "conversations": [
                    {k: v for k, v in r.items() if k != "created_dt"} for r in records
                ],
            }
            (self.output_dir / agent / "summary.json").write_text(
                json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            per_agent[agent] = {"conversations": len(records), "messages": total}
        return per_agent


def write_overview(folder: Path, manifest: dict) -> Path:
    """README.md at the top of an export folder."""
    chats = manifest["components"]["chats"]
    lines = [
        "# WXO Agent Chats Export",
        f"**Export timestamp:** `{manifest['timestamp']}` ({manifest['created_at']})  ",
        f"**Environment:** `{manifest['environment_name']}`  ",
        f"**Instance:** `{manifest['instance_url']}`\n",
        "## Agents\n",
        "| Agent folder | Conversations | Messages | Index |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for agent, counts in sorted(chats["agents"].items()):
        lines.append(
            f"| `{agent}/` | {counts['conversations']} | {counts['messages']} "
            f"| [summary.json]({agent}/summary.json) |"
        )
    lines += [
        f"\n**Total conversations:** {chats['total_conversations']} | "
        f"**Total messages:** {chats['total_messages']}\n",
        "## Files\n",
        "- `.md`: readable transcript of one conversation.",
        "- `.json`: structured turns plus the full raw WXO payload.",
        "- File times are set to when each conversation started, so folders sort by time.\n",
    ]
    path = folder / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_export_chats(
    cfg: Config | None,
    *,
    output_dir: Path,
    agent: str | None,
    last: str,
    raw_traces: bool,
    workers: int,
    dry_run: bool,
) -> int:
    """Export conversations to <output_dir>/<timestamp>/. Reads from WXO; changes nothing there."""
    parse_window(last)  # fail on a bad --last before touching the network
    if workers < 1:
        raise UsageError("--workers must be at least 1.")
    started = time.time()
    now = dt.datetime.now()
    stamp = now.strftime("%Y%m%d%H%M%S")
    target = output_dir / stamp
    scope = f"agent '{agent}'" if agent else "all agents"

    if dry_run or cfg is None:
        plain(f"[dry-run] would export chats of {scope} (last {last}) to {target}")
        return 0

    plain(f"Exporting chats of {scope} (last {last})")
    api = Api(get_token(cfg))
    ok("Authenticated")
    target.mkdir(parents=True, exist_ok=True)

    exporter = Exporter(api, cfg.url, target, agent, last, raw_traces, workers)
    exporter.load_catalog()
    if exporter.catalog:
        plain(f"Agents in this instance: {', '.join(sorted(exporter.catalog.values()))}")
    exporter.resolve_filter()
    exporter.export_threads()
    exporter.export_traces()
    per_agent = exporter.write_summaries()

    conversations = sum(c["conversations"] for c in per_agent.values())
    messages = sum(c["messages"] for c in per_agent.values())
    manifest = {
        "timestamp": stamp,
        "created_at": now.isoformat(),
        "instance_url": cfg.url,
        "environment_name": cfg.env_name,
        "duration_seconds": round(time.time() - started, 2),
        "components": {
            "chats": {
                "total_conversations": conversations,
                "total_messages": messages,
                "agents": per_agent,
            }
        },
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_overview(target, manifest)

    if not conversations:
        warn(f"No conversations found for {scope} in the last {last}. Try a longer --last.")
    else:
        ok(f"Exported {conversations} conversation(s), {messages} message(s)")
        for name, counts in sorted(per_agent.items()):
            plain(f"    {name}/: {counts['conversations']} chat(s)")
    plain(f"Output: {target}")
    return 0

"""Smoke test: run the incident_triage agent for all four incidents via SDK.

Uses the ADK SDK RunClient and ThreadsClient (same auth path as the CLI).

Usage:
    python scripts/smoke_test_triage.py

Sends one diagnosis-only prompt per incident (no request_remediation call),
polls for completion, and reports tools called and the final assistant answer.
"""

import time
import json
import sys
import os

# Force UTF-8 output on Windows
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

from ibm_watsonx_orchestrate.client.utils import instantiate_client
from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient

AGENT_NAME = "incident_triage"
# UUID from: orchestrate agents list -v
AGENT_UUID = "2354f514-3358-4999-96c9-2bad3d010129"

# Diagnosis-only prompts — do not trigger request_remediation (approval form
# cannot be driven via the run API; the smoke test is diagnosis-only).
PROMPTS = [
    ("INC-1001",
     "Investigate incident INC-1001 on the checkout service. "
     "Use your tools to find the root cause. "
     "Do NOT call request_remediation — just report your diagnosis "
     "and what remediation action you would recommend."),
    ("INC-1002",
     "Investigate incident INC-1002 on the payments service. "
     "Use your tools to find the root cause. "
     "Do NOT call request_remediation — just report your diagnosis "
     "and what remediation action you would recommend."),
    ("INC-1003",
     "Investigate incident INC-1003. "
     "Use your tools to find the root cause. "
     "Do NOT call request_remediation — just report your diagnosis "
     "and what remediation action you would recommend."),
    ("INC-1004",
     "Investigate incident INC-1004. "
     "Use your tools to find the root cause. "
     "Do NOT call request_remediation — just report your diagnosis "
     "and whether any action is needed."),
]

MAX_RETRIES = 36   # 36 x 5s = 3 min per incident


def extract_results(messages: object) -> tuple:
    """Return (tool_names, last_assistant_text) from thread messages."""
    tool_names = []
    last_assistant = ""

    if not messages:
        return tool_names, last_assistant

    # messages may be a list or a dict
    if isinstance(messages, dict):
        msg_list = messages.get("messages", [])
    elif isinstance(messages, list):
        msg_list = messages
    else:
        msg_list = []

    for msg in msg_list:
        role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", "")
        content = msg.get("content", []) if isinstance(msg, dict) else getattr(msg, "content", [])
        tool_name = msg.get("tool_name", "") if isinstance(msg, dict) else getattr(msg, "tool_name", "")

        # Extract tool call name
        if role in ("tool_call", "tool_calls"):
            if tool_name:
                tool_names.append(tool_name)
            elif isinstance(content, list):
                for item in content:
                    n = item.get("tool_name", "") if isinstance(item, dict) else ""
                    if n:
                        tool_names.append(n)
        elif role == "tool" and tool_name:
            tool_names.append(tool_name)

        # Capture last assistant text
        if role == "assistant":
            if isinstance(content, str):
                last_assistant = content
            elif isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        parts.append(item.get("text", ""))
                    else:
                        parts.append(str(item))
                last_assistant = " ".join(parts).strip()
            elif content:
                last_assistant = str(content)

    return tool_names, last_assistant


def run_one(run_client: RunClient, thread_client: ThreadsClient, inc_id: str, prompt: str) -> dict:
    print(f"\n{'='*60}")
    print(f"[{inc_id}] Creating run ...")

    try:
        run_resp = run_client.create_run(
            message=prompt,
            agent_id=AGENT_UUID,
        )
    except Exception as e:
        print(f"  ERROR creating run: {e}")
        return {"status": "create_error", "error": str(e)}

    run_id = run_resp.get("run_id") if isinstance(run_resp, dict) else getattr(run_resp, "run_id", None)
    thread_id = run_resp.get("thread_id") if isinstance(run_resp, dict) else getattr(run_resp, "thread_id", None)
    print(f"  run_id={run_id}, thread_id={thread_id}")

    if not run_id:
        print(f"  ERROR: no run_id in response: {run_resp}")
        return {"status": "no_run_id", "response": str(run_resp)}

    # Poll for completion
    try:
        final_status = run_client.wait_for_run_completion(
            run_id=run_id,
            poll_interval=5,
            max_retries=MAX_RETRIES,
        )
        status_str = final_status.get("status", str(final_status)) if isinstance(final_status, dict) else str(final_status)
        print(f"  Final run status: {status_str}")
    except TimeoutError:
        print(f"  Timed out waiting for run {run_id}")
        status_str = "timeout"
    except Exception as e:
        print(f"  ERROR polling run: {e}")
        status_str = f"poll_error: {e}"

    # Read thread messages
    if thread_id:
        try:
            messages = thread_client.get_thread_messages(thread_id)
        except Exception as e:
            print(f"  ERROR reading messages: {e}")
            messages = []
    else:
        messages = []

    tool_names, last_assistant = extract_results(messages)

    print(f"\n  Tools called: {tool_names if tool_names else '(none found in messages)'}")
    print(f"\n  Answer (first 600 chars):\n    {last_assistant[:600]}")

    return {
        "status": status_str,
        "thread_id": thread_id,
        "tools_called": tool_names,
        "answer": last_assistant,
    }


def main():
    print("=== Incident Triage Smoke Test ===\n")

    run_client = instantiate_client(RunClient)
    thread_client = instantiate_client(ThreadsClient)
    print(f"Runs endpoint: {run_client.base_url}{run_client.base_endpoint}")

    results = {}
    for inc_id, prompt in PROMPTS:
        results[inc_id] = run_one(run_client, thread_client, inc_id, prompt)

    print(f"\n\n{'='*60}")
    print("=== SMOKE TEST SUMMARY ===\n")
    for inc_id, r in results.items():
        tools = r.get("tools_called", [])
        answer = r.get("answer", "")[:300].replace("\n", " ")
        print(f"  {inc_id}: status={r['status']}")
        print(f"    tools : {tools}")
        print(f"    answer: {answer}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

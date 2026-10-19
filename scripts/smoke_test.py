"""Smoke test: send a scenario's prompts to its deployed agent through the ADK run API.

Usage:
    python scripts/smoke_test.py --scenario incident-triage
    python scripts/smoke_test.py --scenario incident-triage --only INC-1001
    python scripts/smoke_test.py --scenario incident-triage --dry-run   # no network, prints the prompts

What it does, per prompt:
    1. looks the agent up BY NAME in the active environment (no hard-coded UUID),
    2. creates a run, polls until it finishes,
    3. prints the tools that were called and the first part of the final answer.

Where things come from (scenarios/<id>/scenario.yaml and the evaluation folder it names):
    - the agent name:  the first entry of `agents:` in the manifest
    - the prompts:     `smoke_prompts` in <evaluation.path>/ground_truth.json, a list of
                       {"id": "...", "prompt": "..."}. Write diagnosis-only prompts: an approval
                       form (human in the loop) cannot be answered through the run API.

This script only tells you what the agent did. It does NOT judge whether the answer is right;
compare with ground_truth.json yourself. It sends real prompts, so each run uses LLM capacity.

Prerequisite: the environment is active (deploy-all does `orchestrate env activate`; the token
expires after 2 hours; re-run `orchestrate env activate <name> --api-key ...` if calls fail).
Never reads env.cfg or local/.
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenario_manifest as sm  # noqa: E402

MAX_RETRIES = 36  # 36 x 5 s = 3 min per prompt


def load_scenario(scenario_id: str) -> tuple:
    """Return (agent_name, [(id, prompt), ...]) from the manifest and ground_truth.json."""
    manifests = sm.load_all()
    if scenario_id not in manifests:
        sys.exit(f"ERROR: unknown scenario '{scenario_id}'. Known: {', '.join(manifests) or '(none)'}")
    m = manifests[scenario_id]
    agents = m.get("agents") or []
    if not agents:
        sys.exit(f"ERROR: scenario '{scenario_id}' has no agents in its manifest")
    ev = (m.get("evaluation") or {}).get("path")
    if not ev:
        sys.exit(f"ERROR: scenario '{scenario_id}' has no evaluation.path in its manifest")
    gt_path = sm.ROOT / ev / "ground_truth.json"
    if not gt_path.is_file():
        sys.exit(f"ERROR: {ev}/ground_truth.json not found")
    gt = json.loads(gt_path.read_text(encoding="utf-8-sig"))
    prompts = [(p["id"], p["prompt"]) for p in gt.get("smoke_prompts") or []]
    if not prompts:
        sys.exit(f"ERROR: {ev}/ground_truth.json has no 'smoke_prompts' (list of {{id, prompt}})")
    return agents[0]["name"], prompts


def find_agent_id(agent_name: str) -> str:
    from ibm_watsonx_orchestrate.client.utils import instantiate_client
    from ibm_watsonx_orchestrate.client.agents.agent_client import AgentClient

    found = instantiate_client(AgentClient).get_draft_by_name(agent_name)
    if not found:
        sys.exit(f"ERROR: no agent named '{agent_name}' in the active environment. "
                 f"Run scripts/deploy-all first.")
    if len(found) > 1:
        sys.exit(f"ERROR: {len(found)} agents named '{agent_name}' found; cannot choose one.")
    agent_id = found[0].get("id")
    if not agent_id:
        sys.exit(f"ERROR: agent '{agent_name}' came back without an 'id' field: {sorted(found[0])}")
    return agent_id


def extract_results(messages: object) -> tuple:
    """Return (tool_names, last_assistant_text) from thread messages."""
    tool_names = []
    last_assistant = ""

    if not messages:
        return tool_names, last_assistant

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

        # Current ADK thread messages record tool calls inside step_history.
        steps = msg.get("step_history") if isinstance(msg, dict) else getattr(msg, "step_history", None)
        for step in steps or []:
            for detail in (step.get("step_details", []) if isinstance(step, dict) else []):
                if isinstance(detail, dict) and detail.get("type") == "tool_call" and detail.get("name"):
                    tool_names.append(detail["name"])

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


def run_one(run_client, thread_client, agent_id: str, case_id: str, prompt: str) -> dict:
    print(f"\n{'=' * 60}")
    print(f"[{case_id}] Creating run ...")

    try:
        run_resp = run_client.create_run(message=prompt, agent_id=agent_id)
    except Exception as e:
        print(f"  ERROR creating run: {e}")
        return {"status": "create_error", "error": str(e)}

    run_id = run_resp.get("run_id") if isinstance(run_resp, dict) else getattr(run_resp, "run_id", None)
    thread_id = run_resp.get("thread_id") if isinstance(run_resp, dict) else getattr(run_resp, "thread_id", None)
    print(f"  run_id={run_id}, thread_id={thread_id}")

    if not run_id:
        print(f"  ERROR: no run_id in response: {run_resp}")
        return {"status": "no_run_id", "response": str(run_resp)}

    try:
        final_status = run_client.wait_for_run_completion(run_id=run_id, poll_interval=5, max_retries=MAX_RETRIES)
        status_str = final_status.get("status", str(final_status)) if isinstance(final_status, dict) else str(final_status)
        print(f"  Final run status: {status_str}")
    except TimeoutError:
        print(f"  Timed out waiting for run {run_id}")
        status_str = "timeout"
    except Exception as e:
        print(f"  ERROR polling run: {e}")
        status_str = f"poll_error: {e}"

    messages = []
    if thread_id:
        try:
            messages = thread_client.get_thread_messages(thread_id)
        except Exception as e:
            print(f"  ERROR reading messages: {e}")

    tool_names, last_assistant = extract_results(messages)

    print(f"\n  Tools called: {tool_names if tool_names else '(none found in messages)'}")
    print(f"\n  Answer (first 600 chars):\n    {last_assistant[:600]}")

    return {"status": status_str, "thread_id": thread_id, "tools_called": tool_names, "answer": last_assistant}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", required=True, help="scenario id (folder name under scenarios/)")
    ap.add_argument("--only", action="append", default=[], help="run only this prompt id (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="print the agent name and prompts; no network")
    args = ap.parse_args()

    agent_name, prompts = load_scenario(args.scenario)
    if args.only:
        unknown = sorted(set(args.only) - {i for i, _ in prompts})
        if unknown:
            sys.exit(f"ERROR: unknown prompt id(s) {unknown}. Known: {[i for i, _ in prompts]}")
        prompts = [(i, p) for i, p in prompts if i in args.only]

    print(f"=== Smoke test: {args.scenario} (agent '{agent_name}', {len(prompts)} prompt(s)) ===")
    if args.dry_run:
        for case_id, prompt in prompts:
            print(f"\n[{case_id}] {prompt}")
        print("\n(dry run: nothing was sent)")
        return 0

    from ibm_watsonx_orchestrate.client.utils import instantiate_client
    from ibm_watsonx_orchestrate.client.chat.run_client import RunClient
    from ibm_watsonx_orchestrate.client.threads.threads_client import ThreadsClient

    agent_id = find_agent_id(agent_name)
    print(f"Agent id: {agent_id}")
    run_client = instantiate_client(RunClient)
    thread_client = instantiate_client(ThreadsClient)

    results = {}
    for case_id, prompt in prompts:
        results[case_id] = run_one(run_client, thread_client, agent_id, case_id, prompt)

    print(f"\n\n{'=' * 60}\n=== SMOKE TEST SUMMARY ===\n")
    for case_id, r in results.items():
        answer = r.get("answer", "")[:300].replace("\n", " ")
        print(f"  {case_id}: status={r['status']}")
        print(f"    tools : {r.get('tools_called', [])}")
        print(f"    answer: {answer}\n")

    bad = [c for c, r in results.items() if r["status"] not in ("completed", "COMPLETED")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

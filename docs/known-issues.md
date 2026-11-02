# Known issues

Real defects and gaps in this repo, with what you will see and what to do about it. For general things to keep in mind (mock data, probabilistic agents, browser-only approval forms) see [Good to know](../README.md#good-to-know) in the README. For `wxodemo` error messages see the [troubleshooting table](wxodemo.md#troubleshooting).

## Contents

- [Evaluation results](#evaluation-results)
- [Incident Triage: wrong incident in approval requests](#incident-triage-wrong-incident-in-approval-requests)
- [Scenario verification status](#scenario-verification-status)
- [Tooling and platform](#tooling-and-platform)

## Evaluation results

**Incident Triage: the final-answer check passes in 0 of 15 evaluation runs.**
Tool selection is good: recall is 1.0 in 13 of 15 runs and `tool_match_success` is true in 13 of 15. The overall `is_success` metric still fails, because it also requires the text check to pass, and the text check fails for two reasons:

- The agent writes IDs with non-breaking hyphens (U+2011, for example `RB-DEPLOY-01`), which break exact keyword matches.
- The agent's answers are much longer than the one-sentence expected responses.

What to do: treat the tool-selection metrics as the useful signal, and do not quote the overall score as a quality measure. To make the score meaningful, loosen the expected responses or normalise hyphens in the check.

**Incident Triage: the INC-1004 test case is too strict.** It expects a `get_metrics` call that the agent can legitimately skip.

**The evaluation has not been re-run** since the `p99_latency_ms` to `latency` fix in the Incident Triage tools.

**Field Maintenance: 1 of 5 test cases succeeded in the one evaluation run** (`evaluation/field-maintenance/results/2026-11-02_14-19-03/`, `n_runs: 1`, Journey Success 0.2). Causes found in the result files: exact matching of the free-text `description` argument of `mx_find_asset`; text goals that the evaluator does not score when the answer arrives as a knowledge-base answer message; and in one test case the agent asked a question without calling `mx_find_asset`. The test cases and one agent instruction were edited after the run and **have not been re-run**. Details: [Scene 6 of the demo script](demo/field-maintenance-demo.md).

**The evaluation framework is optional and not installed by `setup`.** On Python 3.14 its `pandas~=2.2.3` pin cannot be satisfied. The workaround is in [Running the evaluation](../README.md#running-the-evaluation-optional).

## Incident Triage: wrong incident in approval requests

Seen in 3 of 19 runs that start with a vague message such as "Hey, checkout is slow...". The agent sometimes investigates the payments service while working on `INC-1001`, then calls `request_remediation` with `service=payments, incident_id=INC-1001`, which do not match.

- The human approval gate catches this before anything runs, and the data is mock.
- Changing the instructions in `agents/incident-triage/agent.yaml` gave no measurable improvement.
- A proper fix is to validate that service and incident match inside the flow. This has not been done.

What to do in a demo: read the approval form before you click Approve, and say so to the audience. The mismatch is a good example of why the gate exists.

## Scenario verification status

The demo scripts in `docs/demo/` have a "What was and was not verified" table for each scenario. In summary, these parts have **not** been seen working:

| Scenario | Not verified |
|---|---|
| `field-maintenance` | Repeat-run reliability: scenes 3 to 5 were run in the browser, counts not recorded. The agent sometimes prints the full work log and waits for "ok" before the form (seen again in Scene 4). The approval form was seen working (Submit and Reject). The ADK evaluation re-run after the test-case edits. The Maximo connection is a mock; no real Maximo was tested. |
| `travel-request` | The approval form in a browser (render, Approve issues an id, Reject issues none). Retrieval quality on the Finnish PDF: in an early test the best configuration answered 11 of 20 questions correctly, so amounts come from tools, not from the knowledge base. Quotes from the Finnish document are not exact. |
| `release-readiness` | Which specialists the supervisor called in which order, and whether collaborator replies are visible in the chat UI. Post-fix answers were reported as fine but not recorded. |
| `pension-ove-advisor` | The governed application flow in a browser. |
| `yel-income-assessment` | Scenes 2 to 4 were checked at the data layer only, not run live against the agent. |
| `hr-onboarding` | Approve and Reject outcomes for each of the two forms are not recorded. |
| `pension-disability-triage` | Reliability across repeated runs: one smoke run per case. |

Model output also varies from run to run. Rehearse before a live demo.

## Tooling and platform

- **Windows only.** `wxodemo` has been run on Windows only. The Linux and macOS commands are provided but were not run on those systems. The test suite replaces `orchestrate` with a fake and needs no platform-specific tool.
- **Developer Edition.** `wxodemo deploy` promotes each agent to live after import. It has not been run against a Developer Edition instance. If your edition refuses promotion, the deploy stops with exit code 1 and the agent stays a draft. It can still be used through the ADK run API, but the chat UI will not list it.
- **Scenario `undeploy`** (tools, flows, knowledge bases) has been recorded as run with `--dry-run` only. Run it with `--dry-run` first on your own instance and read the plan before you confirm. Standalone agent `deploy` and `undeploy` were run for real.
- **`orchestrate chat ask` hangs** in non-interactive shells. Use `python wxodemo.py smoke <scenario>` or the browser chat.
- **Updating a knowledge base in place can fail ingestion** ("1 document(s) failed in ingestion"). Remove it with `orchestrate knowledge-bases remove --name <kb>` and deploy again.
- **Embedding models.** Only `travel-request` needs the embedding model `ibm/granite-embedding-278m-multilingual`. Two other embedding models (`ibm/multilingual-e5-large` and `virtual-model/openai/text-embedding-3-small`) were not found on the test instance. Check what your instance offers.
- **Container run.** The traffic generator image builds with Podman and starts; a full run against a real instance has not been verified.

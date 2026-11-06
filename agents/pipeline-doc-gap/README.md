# Pipeline Docs and Test Gap Agent

Finds data pipelines whose documentation or tests are missing or ineffective, checks them
against the `pdg_standards` knowledge base, drafts a README and test skeleton from catalog
metadata, and, only when the user asks, proposes a **draft** pull request through a
mandatory human-approval flow (`pdg_request_draft_pr`). Review and merge stay with the
repository's existing PR process.

## Files

- `agent.yaml` -- agent definition
- `../../tools/pdg/pdg.py` -- Python tool package (5 tools) and `../../tools/pdg/data/` mock world
- `../../knowledge/pipeline-doc-gap/pdg_standards.yaml` -- knowledge base (`.txt` documents in `standards/`)
- `../../flows/pipeline_doc_gap/pdg_request_draft_pr.py` -- draft-PR approval flow

## Tools attached (5)

| Tool | Kind | Purpose |
|---|---|---|
| `pdg_list_pipelines` | Python | Catalog overview with objective gap signals (capped at 10 rows) |
| `pdg_get_pipeline` | Python | Metadata, README sections and tests folder status for one pipeline |
| `pdg_get_ci_history` | Python | Recent CI runs; shows whether the test stage is executed |
| `pdg_get_ownership` | Python | CODEOWNERS, committer activity, key-person risk, reviewer to use |
| `pdg_request_draft_pr` | Flow | Human-approval gate before a draft PR record is created |

**Not attached:** `pdg_create_draft_pr` is called only by the `pdg_request_draft_pr` flow
after a human approves. In addition, the tool itself enforces: the PR is always a draft (no
parameter makes it ready); `repo`, `pipeline_id` and `owner` must match the mock catalog;
the README must be under `docs/` and the test skeleton under `tests/`.

## Knowledge base

`pdg_standards` -- six `.txt` documents: documentation standard (STD-DOC-01), test standard
(STD-TEST-01), country requirements for Finland (REQ-FI-01), Sweden (REQ-SE-01) and Germany
(REQ-DE-01), and the pull request and reviewer policy (POL-PR-01).

## Mock pipelines

| Pipeline | Case | Planted situation |
|---|---|---|
| `fi-customer-ingest` | A | No README and no tests folder; handles personal data |
| `se-invoice-batch` | B | Tests folder exists, but the CI test stage is `not_run` in every recent run (red herring) |
| `fi-claims-export` | C | README has the five STD-DOC-01 sections but no "Data residency" section required by REQ-FI-01; tests run in CI |
| `de-payroll-feed` | D | Only committer has left; no active owner; no tests folder; PR reviewer is the DE fallback |
| `se-tax-report` | E | Healthy: complete README (with Retention), tests run in CI, active owner |
| `de-sales-rollup` | F | Healthy: second restraint case |

## Deploy

```bash
python wxodemo.py deploy pipeline-doc-gap
```

## Browser test (approval flow)

The approval form only renders in the watsonx Orchestrate browser chat UI. Ask for a draft PR
for a pipeline, check the form, click **Approve** (agent reports the PR record verbatim) and
in a fresh conversation **Reject** (agent reports "REJECTED. No pull request was created.").

## Known limitations

- Mock data only: no real repository, CI or CODEOWNERS access. The PR record is deterministic and nothing is stored.
- Drafts are built from catalog metadata only; the agent never sees pipeline source code.
- The planted cases were written before the prompts, so the catalog is easy.
- Agent-washing is argued, not measured: there is no baseline script comparison.
- Not yet verified in a live instance: LLM and embedding model availability, KB indexing delay, whether the agent passes matching `repo`/`pipeline_id`/`owner`, whether it opens a PR only when asked, and the approval form (Approve and Reject).

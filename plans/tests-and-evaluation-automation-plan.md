# Plan: Automated Agent Tests & Evaluation Integration

## Top-Level Overview
Establish automated agent test suites across both demo scenarios and standalone agents in `lab-wxo`. We will start with a pilot on `incident_triage` to validate test case structure, evaluation execution, and deployment hooks. Once validated, we will update `wxodemo` to automatically deploy/sync tests on deploy, update the scenario scaffold to generate test cases and `eval_config.yaml` by default, and update both `scenario-builder` and `standalone-builder` modes/skills so all future agent development automatically authors tests.

---

## Sub-Tasks

### Sub-Task 1: Incident Triage Pilot & Test Deployment Validation
- **Intent**: Validate and refine the test case setup for `incident_triage`, verify test case formats against WXO ADK standards, and implement automated test deployment / execution hooks in `wxodemo`.
- **Expected Outcomes**:
  - `incident_triage` evaluation assets (`ground_truth.json`, `eval_config.yaml`, `test_cases/*.json`) verified and aligned with current agent tools and prompts.
  - Mechanism to deploy/sync test cases to WXO instance or run evaluations verified via `wxodemo`.
  - Smoke tests and evaluation commands run cleanly against the pilot agent.
- **Todo List**:
  - [x] Audit `evaluation/incident-triage/test_cases/*.json` against `agents/incident-triage/agent.yaml` tools and instructions.
  - [x] Verify `wxodemo eval incident-triage --dry-run` and `wxodemo smoke incident-triage --dry-run`.
  - [x] Test upload/execution mechanisms for test cases (e.g., via ADK evaluation runner or WXO test case API integration).
  - [x] Document verified pilot test workflow in notes.
- **Relevant Context**:
  - `evaluation/incident-triage/`
  - `src/wxodemo/evaluate.py`
  - `src/wxodemo/smoke.py`
- **Status**: `[x] done`

---

### Sub-Task 2: Automatic Test Deployment in `wxodemo`
- **Intent**: Enhance `wxodemo deploy` and CLI commands so that test suites are automatically deployed/validated whenever a scenario or standalone agent is deployed.
- **Expected Outcomes**:
  - `wxodemo deploy <target>` automatically identifies associated test cases and deploys/syncs them (or runs test verification where configured).
  - `wxodemo validate` validates that test case files and evaluation configs exist and are well-formed.
  - `wxodemo scaffold` automatically generates starter `eval_config.yaml` and `test_cases/tc_01.json` alongside `ground_truth.json`.
- **Todo List**:
  - [x] Update `src/wxodemo/deploy.py` to include test case deployment actions for scenarios and standalone agents if present.
  - [x] Update `src/wxodemo/scaffold.py` to scaffold `eval_config.yaml` and starter test cases in `test_cases/`.
  - [x] Update `src/wxodemo/validate.py` to check for test cases and evaluation config completeness.
  - [x] Add unit tests in `tests/` for new scaffold, validation, and deploy test actions.
- **Relevant Context**:
  - `src/wxodemo/deploy.py`
  - `src/wxodemo/scaffold.py`
  - `src/wxodemo/validate.py`
  - `tests/test_deploy.py`
  - `tests/test_manifest.py`
- **Status**: `[x] done`

---

### Sub-Task 3: Update Scenario Builder Mode & Authoring Skills
- **Intent**: Upgrade the Scenario Builder workflow so that every scenario is required to provide test cases and an evaluation config (`evaluation.tier: full`), making automated testing a standard part of scenario development.
- **Expected Outcomes**:
  - `.bob/skills/wxo-scenario-authoring/SKILL.md` updated to make `eval_config.yaml` and `test_cases/*.json` mandatory deliverables (upgrading from optional).
  - `.bob/custom_modes.yaml` updated for `scenario-builder` mode instructions to enforce test creation and validation before finishing.
  - Scenario template and documentation updated to reflect automatic test requirements.
- **Todo List**:
  - [x] Update `.bob/skills/wxo-scenario-authoring/SKILL.md` (Sections 3, 6, and 7) with test case authoring standards.
  - [x] Update `.bob/custom_modes.yaml` for `scenario-builder` mode prompt/instructions.
  - [x] Ensure validation rules and checklist items include test case verification.
- **Relevant Context**:
  - `.bob/skills/wxo-scenario-authoring/SKILL.md`
  - `.bob/custom_modes.yaml`
- **Status**: `[x] done`

---

### Sub-Task 4: Update Standalone Builder Mode & Agent Conventions
- **Intent**: Extend automated testing to standalone agents so that one-off agents under `standalone/<agent-name>/` automatically include structured test cases derived from `examples.md` and tool definitions.
- **Expected Outcomes**:
  - Standalone agents gain structured test cases (e.g., `standalone/<agent-name>/test_cases/*.json` and `eval_config.yaml`).
  - `.bob/custom_modes.yaml` updated for `standalone-builder` mode to require authoring test cases alongside `examples.md`.
  - Standalone documentation (`standalone/README.md`) updated with test case structure and evaluation instructions.
- **Todo List**:
  - [x] Define standard test case layout for standalone agents in `standalone/README.md`.
  - [x] Add starter test cases to existing standalone agent (`standalone/travel-rules-qa/` and `standalone/hello-world/`).
  - [x] Update `.bob/custom_modes.yaml` for `standalone-builder` mode to enforce test creation and dry-run eval verification.
  - [x] Update `wxodemo` discovery to discover standalone test suites.
- **Relevant Context**:
  - `standalone/README.md`
  - `.bob/custom_modes.yaml`
  - `src/wxodemo/discovery.py`
- **Status**: `[x] done`

---

### Sub-Task 5: End-to-End Verification & Documentation
- **Intent**: Validate the entire test authoring and deployment pipeline across both modes and CLI commands, ensuring all tests pass cleanly.
- **Expected Outcomes**:
  - `python wxodemo.py validate <id>` passes with test checks.
  - `python wxodemo.py deploy <id> --dry-run` shows test deployment actions.
  - Unit test suite (`pytest`) passes cleanly.
  - Documentation updated across `README.md` and scenario authoring guides.
- **Todo List**:
  - [x] Run `pytest` across all test files in `tests/`.
  - [x] Validate `incident_triage` and all existing scenarios with updated validation logic.
  - [x] Verify standalone agent discovery and deployment preview.
  - [x] Update root `README.md` and CLI documentation with test management instructions.
- **Relevant Context**:
  - `tests/`
  - `docs/wxodemo.md`
  - `README.md`
- **Status**: `[x] done`

---

### Scenario Test Suites Status Summary
All 10 scenarios upgraded to `evaluation.tier: full` with verified `eval_config.yaml` and ADK DAG `test_cases/*.json`:
- `incident-triage`: 4 test cases (`tier: full`)
- `travel-request`: 3 test cases (`tier: full`)
- `cloud-finops`: 4 test cases (`tier: full`)
- `customer-returns`: 4 test cases (`tier: full`)
- `hr-onboarding`: 4 test cases (`tier: full`)
- `hr-tacit-knowledge`: 3 test cases (`tier: full`)
- `pension-disability-triage`: 4 test cases (`tier: full`)
- `pension-ove-advisor`: 4 test cases (`tier: full`)
- `release-readiness`: 4 test cases (`tier: full`)
- `yel-income-assessment`: 4 test cases (`tier: full`)

Standalone test suites created:
- `standalone/hello-world`: 1 test case (`eval_config.yaml`)
- `standalone/travel-rules-qa`: 2 test cases (`eval_config.yaml`)

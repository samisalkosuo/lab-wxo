# Plan: Multi-Scenario Interactive HTML Presentation & WXO Demo Assistant

## Top-Level Overview
Create a modern, self-contained, interactive HTML5 presentation application located at `docs/demo/presentation.html`. The application is structured as a multi-scenario presentation platform featuring a scenario sidebar, rich technical presentation slides, and an interactive "WXO Live Chat Assistant" slide designed for presenters to drive demos smoothly with one-click prompt copying and live fallback guidance.

The initial scenario implemented will be **Scenario 1: Production Incident Triage**, based directly on [`docs/demo/incident-triage-demo.md`](docs/demo/incident-triage-demo.md) and [`agents/incident-triage/agent.yaml`](agents/incident-triage/agent.yaml), with an extensible data and layout architecture for adding future scenarios.

---

## Sub-Tasks

### Sub-Task 1: Design Presentation Architecture & Extensible Data Model
- **Intent**: Establish the layout shell, modular scenario data model, responsive IBM Carbon-inspired UI design system, and navigation controls.
- **Expected Outcomes**:
  - Self-contained file (`docs/demo/presentation.html`) with embedded styling (CSS) and interactive engine (Vanilla JS, zero build step required).
  - Scenario Sidebar with active scenario indicator and collapsible menu for future scenarios.
  - Slide/Page navigation bar (Previous / Next, slide indicator, keyboard shortcuts, fullscreen toggle).
  - Modular JS data structure for scenarios and slides to make adding future scenarios seamless.
- **Todo List**:
  1. Define CSS variables for IBM Carbon palette (dark theme default with toggle, elevated cards, clean typography, badge components).
  2. Implement slide engine supporting slide transitions, progress bar, hash navigation (`#scenario1/slide2`), and keyboard shortcuts (`ArrowLeft`, `ArrowRight`, `Space`, `F` for fullscreen).
  3. Build responsive sidebar supporting multi-scenario switching (Scenario 1: Incident Triage active, Scenario 2 & 3 marked as upcoming).
- **Relevant Context**:
  - `docs/demo/incident-triage-demo.md`
  - `agents/incident-triage/agent.yaml`
- **Status**: `[x] done`

---

### Sub-Task 2: Author Scenario 1 Educational & Architecture Slides
- **Intent**: Build the core educational slides for Incident Triage explaining context, agent mechanics, backend mappings, and business benefits without mentioning deployment steps.
- **Expected Outcomes**:
  - **Slide 1: Scenario Overview**: Business problem, high MTTR, alert fatigue, fragmented observability data across microservices.
  - **Slide 2: Why & How Agent is Used**: Shift from manual dashboard-hopping to conversational triage; how engineers interact with WXO to accelerate diagnosis.
  - **Slide 3: How & Why Agent Works (Architecture)**: ReAct decision loop, 8 diagnostic tools (`list_open_incidents`, `get_incident`, `get_service_health`, `query_logs`, `get_metrics`, `list_recent_deployments`, `open_ticket`), Slate-125m Runbook Knowledge Base retrieval, and Human-in-the-Loop flow gate.
  - **Slide 4: Real-Life Backend Services**: Side-by-side mapping matrix showing mock tools vs enterprise backend systems (PagerDuty/ServiceNow, Datadog/Dynatrace, Splunk/Elasticsearch, Prometheus/Grafana, GitHub/ArgoCD, Ansible/Kubernetes).
  - **Slide 5: Value & Benefits**: Quantifiable benefits (MTTR reduction, cognitive load relief, consistent citation-backed reasoning) and safety guarantees (zero direct execution permissions on agent).
- **Todo List**:
  1. Draft slide content using structured cards, data chips, architecture flow diagrams, and backend comparison tables.
  2. Add visual callouts for key platform concepts (ReAct loop, retrieval-augmented runbooks, flow-governed remediation).
  3. Ensure all content strictly assumes agents are pre-deployed and WXO is ready.
- **Relevant Context**:
  - `agents/incident-triage/agent.yaml`
  - `knowledge/incident-triage/incident_triage_runbooks.yaml`
  - `flows/incident_triage/request_remediation.py`
- **Status**: `[x] done`

---

### Sub-Task 3: Author Streamlined Demo Prompts Slide
- **Intent**: Create a clean, presenter-friendly slide containing the actual prompt texts for live WXO chat with one-click copy buttons (omitting expected outputs/mock answers so the live WXO run speaks for itself).
- **Expected Outcomes**:
  - A clean, single-slide prompt board presenting the 5 demo scene prompts ready for live execution:
    - **Scene 1 (Vague Opening)**: `"Hey, checkout is slow. Can you look into it?"`
    - **Scene 2 (Root Cause INC-1001)**: `"Investigate incident INC-1001 on the checkout service. Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and what remediation action you would recommend."`
    - **Scene 3 (Red Herring INC-1002)**: `"Investigate incident INC-1002 on the payments service. There was a recent deployment to notification-service - could that be related? Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and recommended action."`
    - **Scene 4 (Approval Flow)**: `"There is a critical incident on the checkout service, INC-1001. Logs show an N+1 query regression introduced by a recent deployment. Investigate and propose a fix."`
    - **Scene 5 (Non-Incident Restraint INC-1004)**: `"Investigate incident INC-1004. Use your tools to find the root cause and whether any action is needed."`
  - Instant one-click copy buttons with clear visual confirmation ("Copied!") for quick pasting into WXO chat.
  - Minimal layout without expected response text or mock logs, keeping the focus entirely on the live WXO environment.
- **Todo List**:
  1. Design a clean prompt card grid / list for the 5 scenes on the final slide of the scenario.
  2. Implement one-click clipboard copy utility with tooltip / toast confirmation.
  3. Keep the slide uncluttered and distraction-free for live presenting.
- **Relevant Context**:
  - `docs/demo/incident-triage-demo.md` (Scenes 1–5 prompts)
- **Status**: `[x] done`

---

### Sub-Task 4: Validation & Usability Testing
- **Intent**: Validate presentation layout, interactive controls, clipboard functionality, responsiveness, and slide flow.
- **Expected Outcomes**:
  - Presentation renders cleanly in all major modern browsers.
  - All navigation modes (sidebar clicks, next/prev buttons, keyboard shortcuts, swipe) operate smoothly.
  - Clipboard copy triggers successfully without console errors.
  - Future scenario extension slots are cleanly templated.
- **Todo List**:
  1. Test slide progression, sidebar toggles, and scene switcher interactions.
  2. Verify all text matches the approved demo script and architectural facts.
  3. Confirm complete absence of deployment instructions as specified in requirements.
- **Relevant Context**:
  - `docs/demo/presentation.html`
- **Status**: `[x] done`

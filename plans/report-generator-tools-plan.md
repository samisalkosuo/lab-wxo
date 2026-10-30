# Report Generator Tools Package Plan (WXO Native)

## Top-Level Overview

This plan defines the creation of a native watsonx Orchestrate (WXO) shared tool package at `tools/report_generator/`. 

The tool package encapsulates the report prompt engineering and synthetic parameter generation from [`local/report-generator.py`](local/report-generator.py). It is designed for WXO agent execution without external runtime dependencies (no Ollama, no local filesystem persistence):
1. **Report Type Registry & Discovery:** A central registry and `list_supported_report_types()` tool for dynamic discovery and future extensibility.
2. **Individual Report Generation Tools:** Dedicated `@tool` functions for each report type (`doctor_visit`, `traffic_incident`, `building_inspection`, `project_update`, `social_services_visit`).
3. **Dual Parameter Modes:** Accepts explicit user/agent arguments while providing realistic synthetic defaults (preserving Finnish municipalities, industries, blockers, dates, etc.) when arguments are omitted.
4. **Verbatim Prompts:** Uses the exact prompt templates and variable placeholders from [`local/report-generator.py`](local/report-generator.py:31) to return the structured prompt instructions and filled parameters directly to the WXO agent.

---

## Sub-Tasks

### Sub-Task 1: Extensible Registry & Data Architecture
- **Intent:** Build the data and registry foundation in `tools/report_generator/data/` with clean modularization for prompt templates, synthetic generators, and an extensible report type registry.
- **Expected Outcomes:**
  - `tools/report_generator/data/prompts.py`: Contains verbatim `PROMPT_TEMPLATES` and report type constants from [`local/report-generator.py`](local/report-generator.py:31).
  - `tools/report_generator/data/generators.py`: Contains municipal lists, industry mappings, blockers, visit types, severity weights, and synthetic parameter generator functions.
  - `tools/report_generator/data/registry.py`: Extensible registry pattern mapping report types to their schemas, descriptions, prompt templates, and default generators.
  - `tools/report_generator/data/__init__.py`: Package init exporting registry and data components.
- **Todo List:**
  1. Create `tools/report_generator/data/` directory structure.
  2. Implement `tools/report_generator/data/prompts.py` with exact prompt strings and keys.
  3. Implement `tools/report_generator/data/generators.py` preserving all random generator helpers.
  4. Implement `tools/report_generator/data/registry.py` defining report type metadata (id, title, description, parameter schema, prompt template, and generator function).
  5. Create `tools/report_generator/data/__init__.py`.
- **Relevant Context:**
  - Source: [`local/report-generator.py`](local/report-generator.py)
  - Data module patterns: [`tools/incident_triage/data/`](tools/incident_triage/incident_triage.py)
- **Status:** `[x] done`

---

### Sub-Task 2: Implement WXO Tool Functions & Package Exports
- **Intent:** Implement `tools/report_generator/report_generator.py` with `@tool` decorated functions for report type listing and individual report prompt generation.
- **Expected Outcomes:**
  - `list_supported_report_types`: Returns a structured overview / table of all supported report types, descriptions, and parameter requirements (easily extended when new types are registered).
  - Dedicated individual report tools:
    - `generate_doctor_visit_report`: Accepts optional `location`, `date`, `patient_gender`, `patient_age`, `severity`.
    - `generate_traffic_incident_report`: Accepts optional `date`, `country`, `municipality`, `number_of_vehicles`, `time_of_day`, `weather_conditions`.
    - `generate_building_inspection_report`: Accepts optional `country`, `municipality`, `inspection_date`, `building_type`, `construction_year`.
    - `generate_project_update_report`: Accepts optional `project_name`, `industry`, `quarter`, `project_stage`, `primary_blocker`.
    - `generate_social_services_visit_report`: Accepts optional `municipality`, `country`, `date`, `visit_type`, `household_composition`, `case_severity`.
  - All tools return the filled prompt instruction and parameter summary for the WXO agent to synthesize.
  - `tools/report_generator/__init__.py` and `tools/report_generator/requirements.txt` are created.
- **Todo List:**
  1. Implement `tools/report_generator/report_generator.py` with `@tool` decorators from `ibm_watsonx_orchestrate.agent_builder.tools`.
  2. Implement `list_supported_report_types()` tool.
  3. Implement individual report generation tools with explicit parameter merging and synthetic fallbacks.
  4. Implement `tools/report_generator/__init__.py` exporting all tools.
  5. Implement `tools/report_generator/requirements.txt`.
- **Relevant Context:**
  - WXO ADK Tool syntax: [`standalone/hello-world/greetings.py`](standalone/hello-world/greetings.py) and [`tools/incident_triage/incident_triage.py`](tools/incident_triage/incident_triage.py)
- **Status:** `[x] done`

---

### Sub-Task 3: Unit Testing & Verification
- **Intent:** Create automated pytest suite covering registry discovery, explicit and synthetic parameter handling, prompt template population, and error handling.
- **Expected Outcomes:**
  - `tests/test_report_generator_tools.py` passes all unit tests.
  - Verifies `list_supported_report_types` output.
  - Verifies each of the 5 report generator tools with default/random parameters.
  - Verifies each of the 5 report generator tools with explicit custom parameters.
  - Verifies registry extensibility (adding a new report type dynamically).
- **Todo List:**
  1. Create `tests/test_report_generator_tools.py`.
  2. Test `list_supported_report_types()`.
  3. Test synthetic default generation for all 5 report types.
  4. Test explicit override parameters for all 5 report types.
  5. Test adding a custom report type to the registry to verify extensibility.
  6. Run pytest to validate all tests pass.
- **Relevant Context:**
  - Pytest conventions: [`tests/test_hr_tk_tools.py`](tests/test_hr_tk_tools.py)
- **Status:** `[x] done`

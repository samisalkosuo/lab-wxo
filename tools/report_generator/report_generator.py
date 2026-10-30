"""Report generator tools for watsonx Orchestrate.

This package provides prompt construction and synthetic parameter generation tools
for various official report types. Designed for consumption by WXO agents to generate
realistic synthetic reports using native foundation models.
"""

import json
from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data.prompts import (
        REPORT_TYPE_BUILDING_INSPECTION,
        REPORT_TYPE_DOCTOR_VISIT,
        REPORT_TYPE_PROJECT_UPDATE,
        REPORT_TYPE_SOCIAL_SERVICES_VISIT,
        REPORT_TYPE_TRAFFIC_INCIDENT,
    )
    from .data.registry import registry
except ImportError:
    from data.prompts import (
        REPORT_TYPE_BUILDING_INSPECTION,
        REPORT_TYPE_DOCTOR_VISIT,
        REPORT_TYPE_PROJECT_UPDATE,
        REPORT_TYPE_SOCIAL_SERVICES_VISIT,
        REPORT_TYPE_TRAFFIC_INCIDENT,
    )
    from data.registry import registry


def _format_tool_response(report_type: str, resolved_params: dict, prompt: str) -> str:
    """Format the structured prompt output for agent consumption."""
    params_lines = "\n".join(f"- **{k}:** {v}" for k, v in resolved_params.items())
    return (
        f"### Report Generation Specification: `{report_type}`\n\n"
        f"**Parameters Used:**\n{params_lines}\n\n"
        f"**Prompt Instructions for Generation:**\n\n"
        f"{prompt}"
    )


# ---------------------------------------------------------------------------
# Tool 1: list_supported_report_types
# ---------------------------------------------------------------------------
@tool
def list_supported_report_types() -> str:
    """Lists all supported report types, their descriptions, and parameters.

    Use this tool when you need to discover which types of reports can be generated,
    or to inspect the expected parameters for each report type.

    Returns:
        str: A Markdown-formatted summary table of supported report types and their parameters.
    """
    specs = registry.list_specs()
    if not specs:
        return "No report types are currently registered."

    lines = [
        "| Report Type (`id`) | Title | Description | Supported Parameters |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for spec in specs:
        params_summary = ", ".join(f"`{p}`" for p in spec.parameters.keys())
        lines.append(
            f"| `{spec.report_type}` | **{spec.title}** | {spec.description} | {params_summary} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: generate_doctor_visit_report
# ---------------------------------------------------------------------------
@tool
def generate_doctor_visit_report(
    location: Optional[str] = None,
    date: Optional[str] = None,
    patient_gender: Optional[str] = None,
    patient_age: Optional[int] = None,
    severity: Optional[int] = None,
) -> str:
    """Builds a Doctor's Visit Summary report prompt with explicit or synthetic parameters.

    Use this tool to generate clinical visit summaries covering Chief Complaint,
    HPI, Physical Exam, Assessment/Diagnosis, Plan/Treatment, and Follow-up.
    Any omitted arguments are automatically populated with realistic synthetic values.

    Args:
        location (str, optional): Clinic or hospital location (e.g. 'Helsinki', 'Tampere'). Defaults to random Finnish municipality.
        date (str, optional): Visit date in format DD.MM.YYYY. Defaults to random past date within 2 years.
        patient_gender (str, optional): Patient gender ('male' or 'female'). Defaults to random choice.
        patient_age (int, optional): Patient age between 1 and 105. Defaults to random age.
        severity (int, optional): Severity level 1-5 (1=Resuscitation, 2=Emergent, 3=Urgent, 4=Less-urgent, 5=Non-urgent). Defaults to random level.

    Returns:
        str: Structured prompt instructions and parameters for the agent to synthesize the final report.
    """
    explicit = {
        "location": location,
        "date": date,
        "patient_gender": patient_gender,
        "patient_age": patient_age,
        "severity": severity,
    }
    prompt, resolved = registry.build_prompt(REPORT_TYPE_DOCTOR_VISIT, explicit)
    return _format_tool_response(REPORT_TYPE_DOCTOR_VISIT, resolved, prompt)


# ---------------------------------------------------------------------------
# Tool 3: generate_traffic_incident_report
# ---------------------------------------------------------------------------
@tool
def generate_traffic_incident_report(
    date: Optional[str] = None,
    country: Optional[str] = None,
    municipality: Optional[str] = None,
    number_of_vehicles: Optional[int] = None,
    time_of_day: Optional[str] = None,
    weather_conditions: Optional[str] = None,
) -> str:
    """Builds a Traffic Incident Report prompt with explicit or synthetic parameters.

    Use this tool to generate detailed police/investigator traffic accident reports
    with timeline, fictional driver/witness names, road conditions, and vehicle damage.
    Any omitted arguments are automatically populated with realistic synthetic values.

    Args:
        date (str, optional): Incident date in format DD.MM.YYYY. Defaults to random past date within 3 years.
        country (str, optional): Country where incident occurred. Defaults to 'Finland'.
        municipality (str, optional): Municipality name (e.g. 'Espoo', 'Vantaa'). Defaults to random Finnish municipality.
        number_of_vehicles (int, optional): Number of vehicles involved (2-11). Defaults to random weighted count.
        time_of_day (str, optional): Time of day ('night', 'morning', 'day', 'evening'). Defaults to random choice.
        weather_conditions (str, optional): Weather and road conditions description. Defaults to random weather condition.

    Returns:
        str: Structured prompt instructions and parameters for the agent to synthesize the final report.
    """
    explicit = {
        "date": date,
        "country": country,
        "municipality": municipality,
        "number_of_vehicles": number_of_vehicles,
        "time_of_day": time_of_day,
        "weather_conditions": weather_conditions,
    }
    prompt, resolved = registry.build_prompt(REPORT_TYPE_TRAFFIC_INCIDENT, explicit)
    return _format_tool_response(REPORT_TYPE_TRAFFIC_INCIDENT, resolved, prompt)


# ---------------------------------------------------------------------------
# Tool 4: generate_building_inspection_report
# ---------------------------------------------------------------------------
@tool
def generate_building_inspection_report(
    country: Optional[str] = None,
    municipality: Optional[str] = None,
    inspection_date: Optional[str] = None,
    building_type: Optional[str] = None,
    construction_year: Optional[int] = None,
) -> str:
    """Builds an official Building Inspection Report prompt with explicit or synthetic parameters.

    Use this tool to generate building inspection reports covering General Information,
    Building Overview, Context, Observations (structural, HVAC, electrical, fire safety),
    Issues/Recommendations, Compliance Summary, and Conclusion.
    Any omitted arguments are automatically populated with realistic synthetic values.

    Args:
        country (str, optional): Country of inspection. Defaults to 'Finland'.
        municipality (str, optional): Municipality name (e.g. 'Turku', 'Oulu'). Defaults to random Finnish municipality.
        inspection_date (str, optional): Inspection date DD.MM.YYYY. Defaults to random past date within 1 year.
        building_type (str, optional): Building type ('residential', 'commercial', 'industrial', 'public'). Defaults to random type.
        construction_year (int, optional): Year of construction (1970 to present). Defaults to random year.

    Returns:
        str: Structured prompt instructions and parameters for the agent to synthesize the final report.
    """
    explicit = {
        "country": country,
        "municipality": municipality,
        "inspection_date": inspection_date,
        "building_type": building_type,
        "construction_year": construction_year,
    }
    prompt, resolved = registry.build_prompt(REPORT_TYPE_BUILDING_INSPECTION, explicit)
    return _format_tool_response(REPORT_TYPE_BUILDING_INSPECTION, resolved, prompt)


# ---------------------------------------------------------------------------
# Tool 5: generate_project_update_report
# ---------------------------------------------------------------------------
@tool
def generate_project_update_report(
    project_name: Optional[str] = None,
    industry: Optional[str] = None,
    quarter: Optional[str] = None,
    project_stage: Optional[str] = None,
    primary_blocker: Optional[str] = None,
) -> str:
    """Builds a Quarterly Project Update Report prompt with explicit or synthetic parameters.

    Use this tool to generate executive project reports covering Executive Summary,
    Key Milestones Achieved, Risks/Blockers, Next Quarter Objectives, and Resource/Budget Overview.
    Any omitted arguments are automatically populated with realistic synthetic values.

    Args:
        project_name (str, optional): Strategic project name. Defaults to industry-specific realistic project name.
        industry (str, optional): Industry sector (e.g. 'Healthcare', 'Finance', 'Energy', 'Retail'). Defaults to random industry.
        quarter (str, optional): Quarter covered (e.g. 'Q2 2024'). Defaults to recent quarter.
        project_stage (str, optional): Project stage (e.g. 'Implementation', 'Testing', 'Deployment'). Defaults to random stage.
        primary_blocker (str, optional): Primary risk or blocker being managed. Defaults to industry-aligned blocker.

    Returns:
        str: Structured prompt instructions and parameters for the agent to synthesize the final report.
    """
    explicit = {
        "project_name": project_name,
        "industry": industry,
        "quarter": quarter,
        "project_stage": project_stage,
        "primary_blocker": primary_blocker,
    }
    prompt, resolved = registry.build_prompt(REPORT_TYPE_PROJECT_UPDATE, explicit)
    return _format_tool_response(REPORT_TYPE_PROJECT_UPDATE, resolved, prompt)


# ---------------------------------------------------------------------------
# Tool 6: generate_social_services_visit_report
# ---------------------------------------------------------------------------
@tool
def generate_social_services_visit_report(
    municipality: Optional[str] = None,
    country: Optional[str] = None,
    date: Optional[str] = None,
    visit_type: Optional[str] = None,
    household_composition: Optional[str] = None,
    case_severity: Optional[str] = None,
) -> str:
    """Builds a Social Services Visit Report prompt with explicit or synthetic parameters.

    Use this tool to generate social services visit documentation covering Visit Purpose,
    Observations, Assessment/Risks, and Recommended Actions/Follow-up.
    Any omitted arguments are automatically populated with realistic synthetic values.

    Args:
        municipality (str, optional): Location municipality (e.g. 'Jyväskylä', 'Lahti'). Defaults to random Finnish municipality.
        country (str, optional): Country name. Defaults to 'Finland'.
        date (str, optional): Visit date DD.MM.YYYY. Defaults to random past date within 1 year.
        visit_type (str, optional): Reason/type of visit (e.g. 'Child welfare check', 'Elderly care follow-up'). Defaults to random visit type.
        household_composition (str, optional): Family/client household description. Defaults to random composition.
        case_severity (str, optional): Case severity ('Low', 'Moderate', 'High', 'Urgent', 'Critical'). Defaults to weighted random severity.

    Returns:
        str: Structured prompt instructions and parameters for the agent to synthesize the final report.
    """
    explicit = {
        "municipality": municipality,
        "country": country,
        "date": date,
        "visit_type": visit_type,
        "household_composition": household_composition,
        "case_severity": case_severity,
    }
    prompt, resolved = registry.build_prompt(REPORT_TYPE_SOCIAL_SERVICES_VISIT, explicit)
    return _format_tool_response(REPORT_TYPE_SOCIAL_SERVICES_VISIT, resolved, prompt)

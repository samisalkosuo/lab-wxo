"""Unit tests for report generator tools in tools/report_generator."""

import sys
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tools.report_generator.data.registry import ReportRegistry, ReportTypeSpec, registry
from tools.report_generator.data.prompts import (
    AVAILABLE_REPORT_TYPES,
    REPORT_TYPE_BUILDING_INSPECTION,
    REPORT_TYPE_DOCTOR_VISIT,
    REPORT_TYPE_PROJECT_UPDATE,
    REPORT_TYPE_SOCIAL_SERVICES_VISIT,
    REPORT_TYPE_TRAFFIC_INCIDENT,
)
from tools.report_generator.report_generator import (
    generate_building_inspection_report,
    generate_doctor_visit_report,
    generate_project_update_report,
    generate_social_services_visit_report,
    generate_traffic_incident_report,
    list_supported_report_types,
)


def _call(tool_obj, *args, **kwargs):
    """Helper to invoke @tool decorated function directly or via .fn."""
    if hasattr(tool_obj, "fn"):
        return tool_obj.fn(*args, **kwargs)
    return tool_obj(*args, **kwargs)


def test_list_supported_report_types():
    result = _call(list_supported_report_types)
    assert isinstance(result, str)
    assert "| Report Type (`id`) |" in result
    for rtype in AVAILABLE_REPORT_TYPES:
        assert f"`{rtype}`" in result


def test_generate_doctor_visit_report_defaults():
    result = _call(generate_doctor_visit_report)
    assert "### Report Generation Specification: `doctor_visit`" in result
    assert "Chief Complaint" in result
    assert "Physical Examination Findings" in result
    assert "Severity Level:" in result


def test_generate_doctor_visit_report_explicit_params():
    result = _call(
        generate_doctor_visit_report,
        location="Tampere University Hospital",
        date="15.08.2024",
        patient_gender="female",
        patient_age=42,
        severity=2,
    )
    assert "Tampere University Hospital" in result
    assert "15.08.2024" in result
    assert "female" in result
    assert "42" in result
    assert "Severity Level: 2" in result


def test_generate_traffic_incident_report_defaults():
    result = _call(generate_traffic_incident_report)
    assert "### Report Generation Specification: `traffic_incident`" in result
    assert "traffic incident report" in result
    assert "Weather conditions:" in result
    assert "Number of vehicles involved:" in result


def test_generate_traffic_incident_report_explicit_params():
    result = _call(
        generate_traffic_incident_report,
        date="10.01.2024",
        country="Finland",
        municipality="Espoo",
        number_of_vehicles=3,
        time_of_day="morning",
        weather_conditions="Icy roads with heavy snowfall",
    )
    assert "10.01.2024" in result
    assert "Espoo" in result
    assert "3" in result
    assert "morning" in result
    assert "Icy roads with heavy snowfall" in result


def test_generate_building_inspection_report_defaults():
    result = _call(generate_building_inspection_report)
    assert "### Report Generation Specification: `building_inspection`" in result
    assert "official building inspection report" in result
    assert "Building Type:" in result


def test_generate_building_inspection_report_explicit_params():
    result = _call(
        generate_building_inspection_report,
        country="Finland",
        municipality="Turku",
        inspection_date="20.05.2023",
        building_type="commercial",
        construction_year=1995,
    )
    assert "Turku" in result
    assert "20.05.2023" in result
    assert "commercial" in result
    assert "1995" in result


def test_generate_project_update_report_defaults():
    result = _call(generate_project_update_report)
    assert "### Report Generation Specification: `project_update`" in result
    assert "Quarterly Project Update Report" in result
    assert "Executive Summary" in result


def test_generate_project_update_report_explicit_params():
    result = _call(
        generate_project_update_report,
        project_name="Core Cloud Transformation",
        industry="Finance",
        quarter="Q3 2024",
        project_stage="Testing",
        primary_blocker="Legacy mainframe latency",
    )
    assert "Core Cloud Transformation" in result
    assert "Finance" in result
    assert "Q3 2024" in result
    assert "Testing" in result
    assert "Legacy mainframe latency" in result


def test_generate_social_services_visit_report_defaults():
    result = _call(generate_social_services_visit_report)
    assert "### Report Generation Specification: `social_services_visit`" in result
    assert "Social Services Visit Report" in result
    assert "Observations During the Visit" in result


def test_generate_social_services_visit_report_explicit_params():
    result = _call(
        generate_social_services_visit_report,
        municipality="Oulu",
        country="Finland",
        date="12.02.2024",
        visit_type="Elderly care follow-up",
        household_composition="Elderly woman with early dementia symptoms",
        case_severity="Urgent",
    )
    assert "Oulu" in result
    assert "12.02.2024" in result
    assert "Elderly care follow-up" in result
    assert "Elderly woman with early dementia symptoms" in result
    assert "Urgent" in result


def test_registry_extensibility():
    custom_registry = ReportRegistry()
    
    custom_spec = ReportTypeSpec(
        report_type="incident_postmortem",
        title="Incident Postmortem Report",
        description="Engineering postmortem report for service outages.",
        parameters={
            "incident_id": {"type": "str", "description": "Incident ID"},
            "service": {"type": "str", "description": "Service name"},
        },
        prompt_template="Write a postmortem for {incident_id} affecting {service}.",
        default_generator=lambda: {"incident_id": "INC-9999", "service": "payments"},
    )
    custom_registry.register(custom_spec)

    assert "incident_postmortem" in custom_registry.get_supported_types()
    prompt, params = custom_registry.build_prompt("incident_postmortem", {"service": "checkout"})
    assert "Write a postmortem for INC-9999 affecting checkout." == prompt
    assert params["service"] == "checkout"
    assert params["incident_id"] == "INC-9999"


def test_registry_unknown_report_type_raises():
    with pytest.raises(ValueError, match="Unknown report type 'non_existent_type'"):
        registry.build_prompt("non_existent_type")

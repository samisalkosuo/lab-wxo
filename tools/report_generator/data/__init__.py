"""Data and prompt templates subpackage for watsonx Orchestrate report generator tools."""

from .generators import (
    create_building_inspection_request,
    create_doctor_visit_request,
    create_project_update_request,
    create_social_services_visit_request,
    create_traffic_incident_request,
    municipalities,
)
from .prompts import (
    AVAILABLE_REPORT_TYPES,
    PROMPT_TEMPLATES,
    REPORT_TYPE_BUILDING_INSPECTION,
    REPORT_TYPE_DOCTOR_VISIT,
    REPORT_TYPE_PROJECT_UPDATE,
    REPORT_TYPE_SOCIAL_SERVICES_VISIT,
    REPORT_TYPE_TRAFFIC_INCIDENT,
)
from .registry import ReportRegistry, ReportTypeSpec, registry

__all__ = [
    "REPORT_TYPE_DOCTOR_VISIT",
    "REPORT_TYPE_TRAFFIC_INCIDENT",
    "REPORT_TYPE_BUILDING_INSPECTION",
    "REPORT_TYPE_PROJECT_UPDATE",
    "REPORT_TYPE_SOCIAL_SERVICES_VISIT",
    "AVAILABLE_REPORT_TYPES",
    "PROMPT_TEMPLATES",
    "municipalities",
    "create_doctor_visit_request",
    "create_traffic_incident_request",
    "create_building_inspection_request",
    "create_project_update_request",
    "create_social_services_visit_request",
    "ReportTypeSpec",
    "ReportRegistry",
    "registry",
]

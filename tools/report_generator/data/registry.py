"""Extensible Report Type Registry for watsonx Orchestrate report generator tools.

Allows dynamic registration and querying of report types, schemas, and prompt builders.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .generators import (
    create_building_inspection_request,
    create_doctor_visit_request,
    create_project_update_request,
    create_social_services_visit_request,
    create_traffic_incident_request,
)
from .prompts import (
    PROMPT_TEMPLATES,
    REPORT_TYPE_BUILDING_INSPECTION,
    REPORT_TYPE_DOCTOR_VISIT,
    REPORT_TYPE_PROJECT_UPDATE,
    REPORT_TYPE_SOCIAL_SERVICES_VISIT,
    REPORT_TYPE_TRAFFIC_INCIDENT,
)


@dataclass
class ReportTypeSpec:
    """Specification and template definition for a report type."""
    report_type: str
    title: str
    description: str
    parameters: Dict[str, Dict[str, Any]]
    prompt_template: str
    default_generator: Callable[[], Dict[str, Any]]


class ReportRegistry:
    """Registry managing available report types, prompt templates, and default generators."""

    def __init__(self):
        self._registry: Dict[str, ReportTypeSpec] = {}
        self._register_defaults()

    def register(self, spec: ReportTypeSpec) -> None:
        """Register a new or custom report type specification."""
        self._registry[spec.report_type] = spec

    def get(self, report_type: str) -> Optional[ReportTypeSpec]:
        """Retrieve a report specification by its unique identifier."""
        return self._registry.get(report_type)

    def list_specs(self) -> List[ReportTypeSpec]:
        """List all registered report type specifications."""
        return list(self._registry.values())

    def get_supported_types(self) -> List[str]:
        """List all registered report type keys."""
        return list(self._registry.keys())

    def build_prompt(
        self,
        report_type: str,
        explicit_params: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Merge explicit parameters with synthetic defaults and fill the prompt template.

        Returns:
            tuple[str, dict]: (filled_prompt_string, resolved_parameters_dict)
        """
        spec = self.get(report_type)
        if not spec:
            raise ValueError(f"Unknown report type '{report_type}'. Available types: {', '.join(self.get_supported_types())}")

        # Generate default baseline parameters
        resolved_params = spec.default_generator().copy()

        # Overlay any non-None explicit parameters provided by the caller
        if explicit_params:
            for k, v in explicit_params.items():
                if v is not None:
                    resolved_params[k] = v

        filled_prompt = spec.prompt_template.format_map(resolved_params)
        return filled_prompt, resolved_params

    def _register_defaults(self) -> None:
        """Register standard out-of-the-box report types."""
        self.register(
            ReportTypeSpec(
                report_type=REPORT_TYPE_DOCTOR_VISIT,
                title="Doctor Visit Summary",
                description="Medical assistant visit summary covering chief complaint, HPI, exam, diagnosis, plan, and follow-up.",
                parameters={
                    "location": {"type": "str", "description": "Clinic or hospital location (default: Finnish municipality)"},
                    "date": {"type": "str", "description": "Visit date DD.MM.YYYY (default: past 2 years)"},
                    "patient_gender": {"type": "str", "description": "Patient gender: 'male' or 'female'"},
                    "patient_age": {"type": "int", "description": "Patient age 1-105"},
                    "severity": {"type": "int", "description": "Severity level 1-5 (1=Resuscitation, 5=Non-urgent)"},
                },
                prompt_template=PROMPT_TEMPLATES[REPORT_TYPE_DOCTOR_VISIT],
                default_generator=create_doctor_visit_request,
            )
        )

        self.register(
            ReportTypeSpec(
                report_type=REPORT_TYPE_TRAFFIC_INCIDENT,
                title="Traffic Incident Report",
                description="Investigative police report with timeline, driver/witness names, road/weather conditions, and vehicle damage.",
                parameters={
                    "date": {"type": "str", "description": "Incident date DD.MM.YYYY (default: past 3 years)"},
                    "country": {"type": "str", "description": "Country name (default: 'Finland')"},
                    "municipality": {"type": "str", "description": "Municipality name (default: Finnish municipality)"},
                    "number_of_vehicles": {"type": "int", "description": "Number of vehicles involved (2-11)"},
                    "time_of_day": {"type": "str", "description": "Time of day ('night', 'morning', 'day', 'evening')"},
                    "weather_conditions": {"type": "str", "description": "Weather conditions description"},
                },
                prompt_template=PROMPT_TEMPLATES[REPORT_TYPE_TRAFFIC_INCIDENT],
                default_generator=create_traffic_incident_request,
            )
        )

        self.register(
            ReportTypeSpec(
                report_type=REPORT_TYPE_BUILDING_INSPECTION,
                title="Building Inspection Report",
                description="Official building inspection document detailing structure, HVAC, electrical, fire safety, compliance, and issues.",
                parameters={
                    "country": {"type": "str", "description": "Country name (default: 'Finland')"},
                    "municipality": {"type": "str", "description": "Municipality name (default: Finnish municipality)"},
                    "inspection_date": {"type": "str", "description": "Inspection date DD.MM.YYYY (default: past year)"},
                    "building_type": {"type": "str", "description": "Building type ('residential', 'commercial', 'industrial', 'public')"},
                    "construction_year": {"type": "int", "description": "Construction year (1970 to present)"},
                },
                prompt_template=PROMPT_TEMPLATES[REPORT_TYPE_BUILDING_INSPECTION],
                default_generator=create_building_inspection_request,
            )
        )

        self.register(
            ReportTypeSpec(
                report_type=REPORT_TYPE_PROJECT_UPDATE,
                title="Quarterly Project Update Report",
                description="Executive stakeholder project report covering milestones, percentage completion, risks/blockers, budget, and next quarter objectives.",
                parameters={
                    "project_name": {"type": "str", "description": "Large-scale project name"},
                    "industry": {"type": "str", "description": "Industry sector (e.g. Healthcare, Finance, Manufacturing)"},
                    "quarter": {"type": "str", "description": "Quarter string (e.g. 'Q2 2024')"},
                    "project_stage": {"type": "str", "description": "Current stage (e.g. Implementation, Testing, Deployment)"},
                    "primary_blocker": {"type": "str", "description": "Key challenge or blocker being managed"},
                },
                prompt_template=PROMPT_TEMPLATES[REPORT_TYPE_PROJECT_UPDATE],
                default_generator=create_project_update_request,
            )
        )

        self.register(
            ReportTypeSpec(
                report_type=REPORT_TYPE_SOCIAL_SERVICES_VISIT,
                title="Social Services Visit Report",
                description="Professional social care visit report with observations, assessment, risk dynamics, and recommended follow-up actions.",
                parameters={
                    "date": {"type": "str", "description": "Visit date DD.MM.YYYY (default: past year)"},
                    "municipality": {"type": "str", "description": "Municipality name (default: Finnish municipality)"},
                    "country": {"type": "str", "description": "Country name (default: 'Finland')"},
                    "visit_type": {"type": "str", "description": "Visit type (e.g. 'Child welfare check', 'Elderly care follow-up')"},
                    "household_composition": {"type": "str", "description": "Household description (e.g. 'Single mother with three children')"},
                    "case_severity": {"type": "str", "description": "Case severity ('Low', 'Moderate', 'High', 'Urgent', 'Critical')"},
                },
                prompt_template=PROMPT_TEMPLATES[REPORT_TYPE_SOCIAL_SERVICES_VISIT],
                default_generator=create_social_services_visit_request,
            )
        )


# Global singleton instance for easy import and extension
registry = ReportRegistry()

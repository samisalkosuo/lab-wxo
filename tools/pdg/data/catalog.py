"""Mock pipeline catalog for three countries (FI, SE, DE).

Each entry holds metadata only. The agent never sees pipeline source code.
Planted cases (what each one teaches):

  A  fi-customer-ingest : no README and no tests. Clear gap, main path.
  B  se-invoice-batch   : tests folder exists but CI never runs the test stage.
                          Red herring: "tests present" is not "tests effective".
  C  fi-claims-export   : README exists but lacks the sections that the Finnish
                          country requirement (REQ-FI-01 in the KB) asks for.
  D  de-payroll-feed    : only committer has left. Gap is riskier and the PR
                          needs a reviewer fallback.
  E  se-tax-report      : healthy. Docs, running tests, active owner. No action.
  F  de-sales-rollup    : healthy. Second restraint case, so that not every
                          country has a gap.

The sections listed in `readme_sections` are compared by the agent with the
documentation standard (STD-DOC-01) and the country requirement in the KB.
"""

from typing import Any, Dict, List, Optional

COUNTRIES = ["FI", "SE", "DE"]

AS_OF = "2025-05-12"

_STANDARD_SECTIONS = [
    "Overview",
    "Inputs and outputs",
    "Schedule",
    "Failure handling",
    "Owner",
]

PIPELINES: Dict[str, Dict[str, Any]] = {
    # Case A
    "fi-customer-ingest": {
        "pipeline_id": "fi-customer-ingest",
        "country": "FI",
        "repo": "fi-customer-data",
        "description": "Nightly ingest of customer master data from the CRM export into the FI customer data mart.",
        "inputs": ["CRM export customers_*.csv (SFTP drop)"],
        "outputs": ["fi_dm.customer_master"],
        "schedule": "daily 02:00 UTC",
        "handles_personal_data": True,
        "readme_present": False,
        "readme_sections": [],
        "tests_folder_present": False,
        "test_count": 0,
    },
    # Case C
    "fi-claims-export": {
        "pipeline_id": "fi-claims-export",
        "country": "FI",
        "repo": "fi-claims-platform",
        "description": "Weekly export of settled claims to the Finnish regulatory reporting gateway.",
        "inputs": ["fi_dm.claims_settled"],
        "outputs": ["regulatory gateway upload (FI)"],
        "schedule": "weekly Monday 05:00 UTC",
        "handles_personal_data": True,
        "readme_present": True,
        "readme_sections": list(_STANDARD_SECTIONS),
        "tests_folder_present": True,
        "test_count": 18,
    },
    # Case B
    "se-invoice-batch": {
        "pipeline_id": "se-invoice-batch",
        "country": "SE",
        "repo": "se-billing-platform",
        "description": "Nightly batch that builds customer invoices from rated usage records.",
        "inputs": ["se_dm.rated_usage"],
        "outputs": ["se_dm.invoices"],
        "schedule": "daily 01:00 UTC",
        "handles_personal_data": False,
        "readme_present": True,
        "readme_sections": list(_STANDARD_SECTIONS),
        "tests_folder_present": True,
        "test_count": 14,
    },
    # Case E
    "se-tax-report": {
        "pipeline_id": "se-tax-report",
        "country": "SE",
        "repo": "se-billing-platform",
        "description": "Monthly VAT summary report for the Swedish finance team.",
        "inputs": ["se_dm.invoices"],
        "outputs": ["se_reports.vat_monthly"],
        "schedule": "monthly day 3, 06:00 UTC",
        "handles_personal_data": True,
        "readme_present": True,
        "readme_sections": _STANDARD_SECTIONS + ["Retention"],
        "tests_folder_present": True,
        "test_count": 22,
    },
    # Case D
    "de-payroll-feed": {
        "pipeline_id": "de-payroll-feed",
        "country": "DE",
        "repo": "de-hr-analytics",
        "description": "Monthly payroll data feed from the HR system to the German analytics store.",
        "inputs": ["HR system payroll extract"],
        "outputs": ["de_hr.payroll_monthly"],
        "schedule": "monthly day 25, 04:00 UTC",
        "handles_personal_data": True,
        "readme_present": True,
        "readme_sections": _STANDARD_SECTIONS + ["Employee data handling"],
        "tests_folder_present": False,
        "test_count": 0,
    },
    # Case F
    "de-sales-rollup": {
        "pipeline_id": "de-sales-rollup",
        "country": "DE",
        "repo": "de-sales-analytics",
        "description": "Daily rollup of German sales orders by region and product line.",
        "inputs": ["de_dm.sales_orders"],
        "outputs": ["de_reports.sales_daily"],
        "schedule": "daily 03:00 UTC",
        "handles_personal_data": False,
        "readme_present": True,
        "readme_sections": list(_STANDARD_SECTIONS),
        "tests_folder_present": True,
        "test_count": 11,
    },
}


def get_pipeline(pipeline_id: str) -> Optional[Dict[str, Any]]:
    return PIPELINES.get(pipeline_id)


def get_pipeline_ids() -> List[str]:
    return sorted(PIPELINES.keys())


def list_pipelines(country: Optional[str] = None) -> List[Dict[str, Any]]:
    items = [p for p in PIPELINES.values() if country is None or p["country"] == country]
    return sorted(items, key=lambda p: p["pipeline_id"])

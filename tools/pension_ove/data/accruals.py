"""Mock accrued pension records for OVE scenario."""

ACCRUALS = {
    "MEM-101": {
        "member_id": "MEM-101",
        "accrued_pension_monthly": 2400.0,
        "accrued_pension_annual": 28800.0,
        "calculation_date": "2025-01-01",
        "total_insured_years": 38.5,
    },
    "MEM-102": {
        "member_id": "MEM-102",
        "accrued_pension_monthly": 1950.0,
        "accrued_pension_annual": 23400.0,
        "calculation_date": "2025-01-01",
        "total_insured_years": 34.0,
    },
    "MEM-103": {
        "member_id": "MEM-103",
        "accrued_pension_monthly": 3000.0,
        "accrued_pension_annual": 36000.0,
        "calculation_date": "2025-01-01",
        "total_insured_years": 41.0,
    },
    "MEM-104": {
        "member_id": "MEM-104",
        "accrued_pension_monthly": 1850.0,
        "accrued_pension_annual": 22200.0,
        "calculation_date": "2025-01-01",
        "total_insured_years": 32.0,
    },
}


def get_accrued_pension(member_id: str) -> dict:
    """Retrieve accrued pension figures by member ID."""
    return ACCRUALS.get(member_id.strip().upper(), {"error": f"Accrual record for member '{member_id}' not found."})

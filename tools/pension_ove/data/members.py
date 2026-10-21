"""Mock member records for OVE scenario."""

MEMBERS = {
    "MEM-101": {
        "member_id": "MEM-101",
        "name": "Matti Virtanen",
        "date_of_birth": "1964-04-12",
        "birth_year": 1964,
        "employer": "Nordic Tech Solutions Oy",
        "current_position": "Senior Systems Engineer",
        "current_monthly_salary": 4200.0,
        "active_pension_benefit": None,
        "pension_system": "TyEL",
    },
    "MEM-102": {
        "member_id": "MEM-102",
        "name": "Liisa Korhonen",
        "date_of_birth": "1966-08-25",
        "birth_year": 1966,
        "employer": "Espoo City Educational Services",
        "current_position": "Senior Subject Teacher",
        "current_monthly_salary": 3400.0,
        "active_pension_benefit": None,
        "pension_system": "JuEL",
    },
    "MEM-103": {
        "member_id": "MEM-103",
        "name": "Antti Mäkinen",
        "date_of_birth": "1963-02-15",
        "birth_year": 1963,
        "employer": "Finnish Industrial Logistics Ab",
        "current_position": "Supply Chain Project Manager",
        "current_monthly_salary": 3500.0,
        "active_pension_benefit": None,
        "pension_system": "TyEL",
    },
    "MEM-104": {
        "member_id": "MEM-104",
        "name": "Eeva Koskinen",
        "date_of_birth": "1962-11-10",
        "birth_year": 1962,
        "employer": "Helsinki Care Services Oy",
        "current_position": "Healthcare Specialist",
        "current_monthly_salary": 0.0,
        "active_pension_benefit": {
            "benefit_type": "Kuntoutustuki (Full Disability Pension)",
            "monthly_amount": 1850.0,
            "status": "ACTIVE",
            "start_date": "2023-01-01",
        },
        "pension_system": "TyEL",
    },
}


def get_member(member_id: str) -> dict:
    """Retrieve member record by ID."""
    return MEMBERS.get(member_id.strip().upper(), {"error": f"Member with ID '{member_id}' not found."})

"""Finnish statutory retirement cohort tables and life expectancy coefficients.

Based on Finnish TyEL legislation rules for Partial Early Old-Age Pension (OVE).
"""

COHORT_RULES = {
    1962: {
        "min_ove_age_years": 61,
        "min_ove_age_months": 0,
        "full_pension_age_years": 63,
        "full_pension_age_months": 6,
        "life_expectancy_coeff": 0.95722,
    },
    1963: {
        "min_ove_age_years": 61,
        "min_ove_age_months": 0,
        "full_pension_age_years": 64,
        "full_pension_age_months": 0,
        "life_expectancy_coeff": 0.95421,
    },
    1964: {
        "min_ove_age_years": 62,
        "min_ove_age_months": 0,
        "full_pension_age_years": 64,
        "full_pension_age_months": 0,
        "life_expectancy_coeff": 0.94820,
    },
    1965: {
        "min_ove_age_years": 62,
        "min_ove_age_months": 0,
        "full_pension_age_years": 64,
        "full_pension_age_months": 6,
        "life_expectancy_coeff": 0.94420,
    },
    1966: {
        "min_ove_age_years": 62,
        "min_ove_age_months": 0,
        "full_pension_age_years": 64,
        "full_pension_age_months": 9,
        "life_expectancy_coeff": 0.94110,
    },
    1967: {
        "min_ove_age_years": 62,
        "min_ove_age_months": 0,
        "full_pension_age_years": 65,
        "full_pension_age_months": 0,
        "life_expectancy_coeff": 0.93850,
    },
}

DEFAULT_COHORT_RULE = {
    "min_ove_age_years": 62,
    "min_ove_age_months": 0,
    "full_pension_age_years": 65,
    "full_pension_age_months": 0,
    "life_expectancy_coeff": 0.93500,
}


def get_cohort_rule(birth_year: int) -> dict:
    """Returns statutory age thresholds and coefficients for the given birth year."""
    return COHORT_RULES.get(birth_year, DEFAULT_COHORT_RULE)

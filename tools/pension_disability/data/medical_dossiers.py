"""Static mock medical dossiers for the Disability Pension & Rehab Triage demo.

Each dossier corresponds to one claim case. It provides the medical B-statement
summary, work capacity percentage, prognosis, prior rehabilitation measures, and
the employer duty-to-accommodate report.

  CLM-701  Severe neurological condition — < 40% work capacity, rehab exhausted
  CLM-702  Post-surgical back recovery   — significant recovery potential, no trial
  CLM-703  Factory accident injury        — traumatic injury, long rehab prognosis
  CLM-704  Chronic fatigue / comorbidities — assessment blocked by contribution gap
"""

from typing import Optional

MEDICAL_DOSSIERS = {
    "CLM-701": {
        "claimant_id": "CLM-701",
        "b_statement_date": "2025-01-05",
        "issuing_physician": "Dr. Kaarina Salo, Neurologist, TYKS (Turku University Hospital)",
        "primary_diagnosis": "Progressive multiple sclerosis (MS), relapsing-remitting → secondary progressive",
        "icd10_code": "G35",
        "work_capacity_pct": 30,
        "capacity_assessment": (
            "Work capacity permanently impaired to approximately 30% of full capacity. "
            "Claimant can perform only sedentary, highly simplified tasks for short periods. "
            "Prognosis: condition is irreversible and will progress."
        ),
        "prognosis_period_months": None,     # permanent / indefinite
        "recovery_potential": "none",
        "prior_rehab_measures": [
            "Workplace trial (työkokeilu) completed 2022 — discontinued due to MS progression",
            "Vocational retraining assessment completed 2023 — ruled out: neurological deterioration",
            "Physiotherapy and occupational therapy ongoing since 2021",
        ],
        "rehab_measures_exhausted": True,
        "employer_duty_to_accommodate_report": (
            "Employer confirms all ergonomic and role-modification options were explored and "
            "implemented from 2021 to 2024. No further accommodation is feasible."
        ),
        "medical_panel_referral_required": True,
        "b_statement_validity": "valid",
        "notes": (
            "DIS-POL-01 criteria met: permanent incapacity below 40% threshold. "
            "All rehab measures exhausted per DIS-POL-02. "
            "Case ready for full disability pension evaluation."
        ),
    },
    "CLM-702": {
        "claimant_id": "CLM-702",
        "b_statement_date": "2025-02-10",
        "issuing_physician": "Dr. Pekka Nieminen, Orthopaedic Surgeon, HUS Orthopaedics",
        "primary_diagnosis": "Lumbar disc herniation post-discectomy (L4/L5)",
        "icd10_code": "M51.1",
        "work_capacity_pct": 55,
        "capacity_assessment": (
            "Current work capacity reduced to approximately 55% due to post-operative pain "
            "and limited mobility. Significant recovery expected with structured rehabilitation "
            "and ergonomic workplace modifications."
        ),
        "prognosis_period_months": 18,
        "recovery_potential": "significant",
        "prior_rehab_measures": [
            "Post-surgical physiotherapy started 2024-12-20 (ongoing, 6 sessions completed)",
        ],
        "rehab_measures_exhausted": False,
        "employer_duty_to_accommodate_report": (
            "Employer confirms modified light-duty roles are available. "
            "No workplace ergonomic trial (työkokeilu) has been attempted."
        ),
        "medical_panel_referral_required": False,
        "b_statement_validity": "valid",
        "notes": (
            "DIS-POL-02 applies: rehabilitation before pension. "
            "Work capacity > 40%; recovery potential significant. "
            "No workplace trial attempted. Agent must recommend vocational rehab "
            "(työeläkekuntoutus / työkokeilu) as the primary disposition. "
            "Direct pension grant would be premature."
        ),
    },
    "CLM-703": {
        "claimant_id": "CLM-703",
        "b_statement_date": "2025-02-20",
        "issuing_physician": "Dr. Hanna Korhonen, Trauma Surgeon, Tampere University Hospital",
        "primary_diagnosis": "Traumatic crush injury to right hand and forearm (occupational accident)",
        "icd10_code": "S67.8",
        "work_capacity_pct": 25,
        "capacity_assessment": (
            "Severe traumatic crush injury sustained during factory operation. "
            "Work capacity reduced to approximately 25% for foreseeable future. "
            "Rehabilitation prognosis: 18–24 months for partial recovery; "
            "return to previous occupational role unlikely."
        ),
        "prognosis_period_months": 24,
        "recovery_potential": "partial",
        "prior_rehab_measures": [
            "Acute surgical stabilisation (2025-02-14)",
            "Occupational therapy assessment scheduled (2025-03-10)",
        ],
        "rehab_measures_exhausted": False,
        "employer_duty_to_accommodate_report": (
            "Employer (Teräs Metalli Oy) confirms the accident report was filed with the "
            "insurance carrier on 2025-02-15. Accident officially classified as työtapaturma. "
            "Workplace ergonomic accommodation is not currently feasible given the injury severity."
        ),
        "accident_confirmation": "työtapaturma_confirmed",
        "accident_date": "2025-02-14",
        "medical_panel_referral_required": True,
        "b_statement_validity": "valid",
        "notes": (
            "Standard 36/60-month qualifying condition not met (14 months only). "
            "However, DIS-POL-04 waiver applies: injury is a verified occupational accident. "
            "Agent must validate accident documentation before confirming waiver eligibility."
        ),
    },
    "CLM-704": {
        "claimant_id": "CLM-704",
        "b_statement_date": "2025-01-15",
        "issuing_physician": "Dr. Juha Laitinen, Internal Medicine, Mehiläinen Clinic",
        "primary_diagnosis": "Severe chronic fatigue syndrome with fibromyalgia and depressive disorder",
        "icd10_code": "G93.3",
        "work_capacity_pct": 35,
        "capacity_assessment": (
            "Work capacity reduced to approximately 35% due to combination of chronic fatigue, "
            "widespread musculoskeletal pain, and treatment-resistant depressive disorder. "
            "Prognosis uncertain; condition is chronic and degenerative."
        ),
        "prognosis_period_months": None,
        "recovery_potential": "low",
        "prior_rehab_measures": [
            "Psychiatric treatment ongoing since 2022",
            "Pain management programme completed 2023",
        ],
        "rehab_measures_exhausted": False,
        "employer_duty_to_accommodate_report": (
            "Employer confirms limited remote-work options were explored without success."
        ),
        "medical_panel_referral_required": False,
        "b_statement_validity": "valid",
        "notes": (
            "Medical criteria (< 40% work capacity) would otherwise support a pension claim. "
            "However, DIS-POL-03/04: claimant has only 8 insured months in the last 60. "
            "No occupational accident or bilateral treaty waiver applies. "
            "Case must be refused under TyEL; claimant directed to Kela national pension."
        ),
    },
}


def get_medical_dossier(claimant_id: str) -> Optional[dict]:
    """Return medical dossier by claimant ID or None."""
    return MEDICAL_DOSSIERS.get(claimant_id.strip().upper())


def get_claimant_ids() -> list:
    return list(MEDICAL_DOSSIERS.keys())

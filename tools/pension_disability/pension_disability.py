"""Disability Pension & Vocational Rehabilitation Triage tools for watsonx Orchestrate.

Provides deterministic, read-only claim-assessment tools over the mock Finnish
statutory pension (TyEL/YEL) disability claims world.  All tools are prefixed
`pdis_` so their names are unique across the WXO instance.

Tools exposed to the agent:
  pdis_get_claim_dossier        -- full claimant record + submission overview
  pdis_verify_qualifying_months -- 36/60-month condition check + tuleva aika flag
  pdis_assess_rehab_eligibility -- rehabilitation-before-pension assessment
  pdis_get_medical_summary      -- B-statement, work capacity, prognosis, prior rehab

The write tool pdis_dispatch_referral is NOT defined here; it lives in
flows/pension_disability/refer_medical_board.py and is called only after
human approval.
"""

import json
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import claimants, insurance_periods, medical_dossiers
except ImportError:
    from data import claimants, insurance_periods, medical_dossiers


# ---------------------------------------------------------------------------
# Tool 1: pdis_get_claim_dossier
# ---------------------------------------------------------------------------
@tool
def pdis_get_claim_dossier(claimant_id: str) -> str:
    """Retrieves the full claim submission dossier for a disability pension claimant.

    Use this tool first when a claims handler asks to evaluate, triage, or review
    a disability pension application. It returns the claimant's personal details,
    employment history summary, claim type, submission date, and current claim status.

    Args:
        claimant_id (str): The claimant identifier, e.g. 'CLM-701'. Case-insensitive.

    Returns:
        str: Structured claim dossier summary. Returns a structured error with a hint
             listing valid IDs if the claimant is not found.
    """
    clean_id = claimant_id.strip().upper() if claimant_id else ""
    record = claimants.get_claimant(clean_id)
    if not record:
        valid_ids = claimants.get_claimant_ids()
        return json.dumps({
            "status": "error",
            "error_code": "CLAIMANT_NOT_FOUND",
            "message": f"Claimant '{claimant_id}' was not found in the registry.",
            "hint": f"Known claimant IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    lines = [
        f"### Claim Dossier: {record['name']} (`{record['claimant_id']}`)\n",
        f"- **Date of Birth:** {record['date_of_birth']}",
        f"- **Nationality:** {record['nationality']}",
        f"- **Country of Residence:** {record['residence_country']}",
        f"- **Claim Type:** {record['claim_type']} ({record['claim_subtype']})",
        f"- **Submission Date:** {record['submission_date']}",
        f"- **Claim Status:** `{record['claim_status'].upper()}`",
        f"- **Last Working Day:** {record.get('last_working_day', 'N/A')}",
        f"- **Employer:** {record.get('employer', 'N/A')}",
        "",
        f"**Occupational History:**",
        f"{record['occupational_history_summary']}",
    ]

    # Surface occupational accident details if present
    if record.get("accident_type"):
        lines += [
            "",
            f"**Accident Information:**",
            f"- Type: `{record['accident_type']}`",
            f"- Date: {record.get('accident_date', 'N/A')}",
            f"- Verified: {'Yes' if record.get('accident_verified') else 'Pending'}",
        ]

    # Surface abroad period if present
    if record.get("abroad_period"):
        ab = record["abroad_period"]
        lines += [
            "",
            f"**Abroad Period:**",
            f"- {ab['start']} to {ab['end']}",
            f"- Bilateral Treaty Applies: {'Yes' if ab.get('treaty_applies') else 'No'}",
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: pdis_verify_qualifying_months
# ---------------------------------------------------------------------------
@tool
def pdis_verify_qualifying_months(claimant_id: str) -> str:
    """Verifies whether a claimant meets the statutory 36/60-month qualifying insurance
    condition (tulevan ajan ansioedellytys) for a TyEL disability pension.

    Use this tool to determine:
    - Whether the claimant has at least 36 insured months in the last 60 months.
    - Whether tuleva aika (future-period accrual) eligibility is met.
    - Whether a statutory waiver applies (e.g. occupational accident under TyEL § 12).
    - If the condition fails and no waiver applies, the claimant cannot receive a
      TyEL disability pension and should be referred to Kela.

    Args:
        claimant_id (str): The claimant identifier, e.g. 'CLM-701'. Case-insensitive.

    Returns:
        str: Insurance period verification report including insured months, threshold,
             qualifying status, waiver details, and tuleva aika eligibility.
    """
    clean_id = claimant_id.strip().upper() if claimant_id else ""
    record = insurance_periods.get_insurance_period(clean_id)
    if not record:
        valid_ids = insurance_periods.get_claimant_ids()
        return json.dumps({
            "status": "error",
            "error_code": "INSURANCE_RECORD_NOT_FOUND",
            "message": f"Insurance period record not found for claimant '{claimant_id}'.",
            "hint": f"Known claimant IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    condition_met = record["qualifying_condition_met"]
    waiver = record.get("qualifying_condition_waived", False)
    eligible = condition_met or waiver

    status_label = (
        "ELIGIBLE (condition met)"
        if condition_met
        else ("ELIGIBLE (waiver applies)" if waiver else "NOT ELIGIBLE")
    )

    lines = [
        f"### Insurance Period Verification: `{record['claimant_id']}`\n",
        f"- **Insured Months (last 36):** {record['insured_months_last_36']}",
        f"- **Insured Months (last 60):** {record['insured_months_last_60']}",
        f"- **Required Threshold:** {record['required_threshold_months']} months",
        f"- **36/60 Condition Met:** {'Yes' if condition_met else 'No'}",
        f"- **Overall Eligibility:** **{status_label}**",
    ]

    if waiver:
        lines += [
            f"- **Waiver Applies:** Yes — {record.get('waiver_reason', 'N/A')}",
            f"- **Waiver Statute:** {record.get('waiver_statute', 'N/A')}",
        ]
    elif not condition_met:
        lines += [
            "- **No waiver applies.** Claimant does not meet TyEL qualifying condition.",
            "- **Recommended action:** Refer claimant to Kela national disability pension (SOLITA).",
        ]

    lines += [
        "",
        f"**Tuleva Aika (Future Period) Eligibility:** {'Yes' if record['tuleva_aika_eligible'] else 'No'}",
        f"- Annual Earnings: €{record['annual_earnings_eur']:,}",
        f"- Statutory Earnings Floor (2025): €{record['tuleva_aika_earnings_threshold_eur']:,}",
        "",
        f"**Career Coverage:** {record['total_insured_years']} total insured years",
    ]

    if record.get("coverage_gaps"):
        for gap in record["coverage_gaps"]:
            lines.append(
                f"- **Coverage Gap:** {gap['start']} – {gap['end']} "
                f"({gap['reason']}; treaty: {'Yes' if gap.get('bilateral_treaty') else 'No'})"
            )

    if record.get("notes"):
        lines += ["", f"*Note: {record['notes']}*"]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3: pdis_assess_rehab_eligibility
# ---------------------------------------------------------------------------
@tool
def pdis_assess_rehab_eligibility(claimant_id: str) -> str:
    """Assesses whether a claimant must be directed to vocational rehabilitation
    (työeläkekuntoutus / työkokeilu) before a disability pension can be granted.

    The statutory 'Rehabilitation before Pension' principle (Kuntoutus ensin, DIS-POL-02)
    requires that all viable rehabilitation pathways be exhausted before early pension
    is approved. This tool evaluates:
    - Work capacity percentage vs. the 40% threshold.
    - Recovery potential (significant / partial / low / none).
    - Whether prior rehabilitation measures have been attempted and exhausted.
    - Whether the employer has fulfilled the duty-to-accommodate.
    - Recommended disposition: rehab_priority | pension_eligible | pending_evidence.

    Args:
        claimant_id (str): The claimant identifier, e.g. 'CLM-701'. Case-insensitive.

    Returns:
        str: Rehabilitation eligibility assessment report with recommended disposition
             and required next steps.
    """
    clean_id = claimant_id.strip().upper() if claimant_id else ""
    dossier = medical_dossiers.get_medical_dossier(clean_id)
    if not dossier:
        valid_ids = medical_dossiers.get_claimant_ids()
        return json.dumps({
            "status": "error",
            "error_code": "MEDICAL_DOSSIER_NOT_FOUND",
            "message": f"Medical dossier not found for claimant '{claimant_id}'.",
            "hint": f"Known claimant IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    capacity = dossier["work_capacity_pct"]
    recovery = dossier["recovery_potential"]
    rehab_exhausted = dossier["rehab_measures_exhausted"]

    # Determine disposition
    if capacity >= 40 and not rehab_exhausted and recovery in ("significant", "partial"):
        disposition = "rehab_priority"
        disposition_label = "REHABILITATION PRIORITY"
        rationale = (
            f"Work capacity is {capacity}% (above 40% threshold). "
            f"Recovery potential is '{recovery}'. "
            "Rehabilitation measures have NOT been exhausted. "
            "Per DIS-POL-02 (Rehabilitation before Pension), vocational rehabilitation "
            "(työeläkekuntoutus or workplace trial / työkokeilu) must be pursued before "
            "any pension decision can be made."
        )
    elif capacity < 40 and rehab_exhausted:
        disposition = "pension_eligible"
        disposition_label = "PENSION ELIGIBLE"
        rationale = (
            f"Work capacity is {capacity}% (below 40% threshold). "
            "All prior rehabilitation measures have been exhausted. "
            "Per DIS-POL-01, the claimant meets the medical incapacity criteria for "
            "full disability pension evaluation. Proceed to medical panel referral."
        )
    elif capacity < 40 and not rehab_exhausted and recovery in ("low", "none"):
        disposition = "pension_eligible"
        disposition_label = "PENSION ELIGIBLE (rehab not viable)"
        rationale = (
            f"Work capacity is {capacity}%. Recovery potential is '{recovery}'. "
            "Rehabilitation is not a realistic pathway. "
            "Proceed to medical panel referral per DIS-POL-01."
        )
    else:
        disposition = "pending_evidence"
        disposition_label = "PENDING FURTHER EVIDENCE"
        rationale = (
            f"Work capacity is {capacity}%. Recovery potential: '{recovery}'. "
            "Rehabilitation status requires further clarification before a disposition "
            "can be made. Obtain updated employer accommodation report and rehab specialist opinion."
        )

    lines = [
        f"### Rehabilitation Eligibility Assessment: `{clean_id}`\n",
        f"- **Work Capacity:** {capacity}% of full capacity",
        f"- **40% Incapacity Threshold:** {'Breached (< 40%)' if capacity < 40 else 'Not yet breached (≥ 40%)'}",
        f"- **Recovery Potential:** {recovery}",
        f"- **Prior Rehab Measures Exhausted:** {'Yes' if rehab_exhausted else 'No'}",
        "",
        f"**Disposition: {disposition_label}**",
        "",
        f"**Rationale:** {rationale}",
    ]

    if dossier.get("prior_rehab_measures"):
        lines.append("\n**Prior Rehabilitation Measures:**")
        for measure in dossier["prior_rehab_measures"]:
            lines.append(f"- {measure}")

    lines += [
        "",
        f"**Employer Duty-to-Accommodate:** {dossier['employer_duty_to_accommodate_report']}",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: pdis_get_medical_summary
# ---------------------------------------------------------------------------
@tool
def pdis_get_medical_summary(claimant_id: str) -> str:
    """Retrieves the medical B-statement summary, diagnosis, work capacity percentage,
    prognosis, and medical panel referral status for a disability pension claimant.

    Use this tool to understand the clinical picture: primary diagnosis, ICD-10 code,
    assessed work capacity percentage, recovery prognosis period, and whether the
    Chief Medical Officer (Asiantuntijalääkäri) referral has been triggered.

    Args:
        claimant_id (str): The claimant identifier, e.g. 'CLM-701'. Case-insensitive.

    Returns:
        str: Medical summary including B-statement details, diagnosis, work capacity,
             prognosis, prior rehabilitation history, and referral readiness flag.
    """
    clean_id = claimant_id.strip().upper() if claimant_id else ""
    dossier = medical_dossiers.get_medical_dossier(clean_id)
    if not dossier:
        valid_ids = medical_dossiers.get_claimant_ids()
        return json.dumps({
            "status": "error",
            "error_code": "MEDICAL_DOSSIER_NOT_FOUND",
            "message": f"Medical dossier not found for claimant '{claimant_id}'.",
            "hint": f"Known claimant IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    prognosis_label = (
        f"{dossier['prognosis_period_months']} months"
        if dossier["prognosis_period_months"]
        else "Indefinite / permanent"
    )

    lines = [
        f"### Medical Summary: `{dossier['claimant_id']}`\n",
        f"- **B-Statement Date:** {dossier['b_statement_date']}",
        f"- **Issuing Physician:** {dossier['issuing_physician']}",
        f"- **Primary Diagnosis:** {dossier['primary_diagnosis']}",
        f"- **ICD-10 Code:** `{dossier['icd10_code']}`",
        f"- **B-Statement Validity:** {dossier['b_statement_validity'].upper()}",
        "",
        f"**Work Capacity Assessment:**",
        f"- Current work capacity: **{dossier['work_capacity_pct']}%**",
        f"- Recovery potential: **{dossier['recovery_potential']}**",
        f"- Prognosis period: {prognosis_label}",
        "",
        f"**Capacity Detail:**",
        f"{dossier['capacity_assessment']}",
    ]

    if dossier.get("prior_rehab_measures"):
        lines.append("\n**Prior Rehabilitation Measures:**")
        for m in dossier["prior_rehab_measures"]:
            lines.append(f"- {m}")

    lines += [
        "",
        f"**Rehabilitation Measures Exhausted:** {'Yes' if dossier['rehab_measures_exhausted'] else 'No'}",
        "",
        f"**Medical Panel Referral Required:** {'Yes' if dossier['medical_panel_referral_required'] else 'No — further evidence needed first'}",
    ]

    if dossier.get("accident_confirmation"):
        lines += [
            "",
            f"**Occupational Accident:** {dossier['accident_confirmation'].upper()}",
            f"- Accident Date: {dossier.get('accident_date', 'N/A')}",
        ]

    if dossier.get("notes"):
        lines += ["", f"*Clinical note: {dossier['notes']}*"]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5: pdis_dispatch_referral  (INTERNAL — called only by pdis_refer_claim flow)
# ---------------------------------------------------------------------------
@tool
def pdis_dispatch_referral(
    claimant_id: str,
    referral_type: str,
    disposition_summary: str,
    policy_ref: str,
) -> str:
    """Records an approved disability pension referral in the case management system.

    NOTE: This is a restricted write tool designed for use exclusively by the
    pdis_refer_claim approval flow after explicit claims handler sign-off.
    The agent must NOT call this tool directly.

    Args:
        claimant_id (str): Claimant identifier (e.g. 'CLM-701').
        referral_type (str): One of 'medical_board', 'vocational_rehab', 'deny_tyelonly'.
        disposition_summary (str): Agent's triage reasoning as approved by the handler.
        policy_ref (str): Policy document ID cited (e.g. 'DIS-POL-01').

    Returns:
        str: Structured confirmation with generated referral ID, destination, and timestamp.
    """
    import hashlib

    clean_id = claimant_id.strip().upper() if claimant_id else ""
    record = claimants.get_claimant(clean_id)
    if not record:
        valid_ids = claimants.get_claimant_ids()
        return json.dumps({
            "status": "error",
            "error_code": "CLAIMANT_NOT_FOUND",
            "message": f"Claimant '{claimant_id}' not found.",
            "hint": f"Known claimant IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    valid_types = ["medical_board", "vocational_rehab", "deny_tyelonly"]
    clean_type = referral_type.strip().lower() if referral_type else ""
    if clean_type not in valid_types:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_REFERRAL_TYPE",
            "message": f"Referral type '{referral_type}' is not valid.",
            "hint": f"Allowed types: {', '.join(valid_types)}.",
        }, indent=2)

    destinations = {
        "medical_board":   "Chief Medical Officer (Asiantuntijalääkäri) — Medical Board Review",
        "vocational_rehab": "Vocational Rehabilitation Unit (Kuntoutusasiantuntija)",
        "deny_tyelonly":    "Case Closure (TyEL) — Claimant referred to Kela",
    }

    hash_seed = f"{clean_id}_{clean_type}_{policy_ref}".encode("utf-8")
    hash_int = int(hashlib.md5(hash_seed).hexdigest()[:5], 16) % 90000 + 10000
    referral_id = f"REF-{hash_int}"

    result = {
        "status": "success",
        "referral_id": referral_id,
        "claimant_id": clean_id,
        "claimant_name": record["name"],
        "referral_type": clean_type,
        "destination": destinations[clean_type],
        "policy_ref": policy_ref,
        "recorded_at": "2025-05-12T10:00:00Z",
        "message": (
            f"Referral {referral_id} submitted for {record['name']} ({clean_id}). "
            f"Destination: {destinations[clean_type]}. "
            f"Policy cited: {policy_ref}."
        ),
        "disposition_summary_preview": disposition_summary[:150] + ("..." if len(disposition_summary) > 150 else ""),
    }
    return json.dumps(result, indent=2)

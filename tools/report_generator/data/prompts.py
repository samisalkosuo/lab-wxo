"""Prompt templates for report generation tools.

Copied verbatim from local/report-generator.py.
"""

REPORT_TYPE_DOCTOR_VISIT = "doctor_visit"
REPORT_TYPE_TRAFFIC_INCIDENT = "traffic_incident"
REPORT_TYPE_BUILDING_INSPECTION = "building_inspection"
REPORT_TYPE_PROJECT_UPDATE = "project_update"
REPORT_TYPE_SOCIAL_SERVICES_VISIT = "social_services_visit"

AVAILABLE_REPORT_TYPES = [
    REPORT_TYPE_DOCTOR_VISIT,
    REPORT_TYPE_TRAFFIC_INCIDENT,
    REPORT_TYPE_BUILDING_INSPECTION,
    REPORT_TYPE_PROJECT_UPDATE,
    REPORT_TYPE_SOCIAL_SERVICES_VISIT,
]

PROMPT_TEMPLATES = {
    REPORT_TYPE_PROJECT_UPDATE: (
        "Write a Quarterly Project Update Report for a large-scale project titled {project_name} in the {industry} industry. "
        "The report covers {quarter}, and the project is currently in the {project_stage}.\n\n"
        "Begin the report by generating a realistic, fictional company name appropriate for the {industry} sector. "
        "Use this company name consistently throughout the report as the organization responsible for the project.\n\n"
        "The report must include:\n\n"
        "    Executive Summary – Overall project status, key progress points, and general sentiment (on track, behind, ahead).\n\n"
        "    Key Milestones Achieved – Completed deliverables, percentage of completion, and impact on company goals.\n\n"
        "    Current Risks and Blockers – Include challenges such as {primary_blocker}, and how they are being managed.\n\n"
        "    Next Quarter Objectives – Specific and realistic goals, including deliverables and timelines.\n\n"
        "    Resource and Budget Overview – Commentary on budget usage, staffing, vendor collaboration, and dependencies.\n\n"
        "Use a professional and structured tone suitable for senior stakeholders. "
        "Ensure the content is realistic and consistent with the project stage, blocker, and industry. "
        "Avoid generic or placeholder text."
    ),

    REPORT_TYPE_SOCIAL_SERVICES_VISIT: (
        "Write a Social Services Visit Report based on the following details:\n\n"
        "    Visit date: {date}\n\n"
        "    Location: {municipality}, {country}\n\n"
        "    Visit type: {visit_type}\n\n"
        "    Household composition: {household_composition}\n\n"
        "    Case severity: {case_severity}\n\n"
        "The report must include:\n\n"
        "    Summary of Visit Purpose – Why the visit was conducted, based on visit type and case context.\n\n"
        "    Observations During the Visit – Interactions, living conditions, behaviors, emotional state, or notable concerns.\n\n"
        "    Assessment – Evaluation of the situation, risks, and family dynamics in light of the case severity.\n\n"
        "    Recommended Actions or Follow-up – Next steps, referrals, support services, or timelines for further visits.\n\n"
        "Generate a realistic client name and address appropriate to the location, and maintain a professional, factual tone throughout. "
        "The report should be self-contained, free of placeholders, and contextually consistent with all given parameters. "
        "Avoid repetition and vary narrative structure between runs."
    ),

    REPORT_TYPE_DOCTOR_VISIT: (
        "You are a professional medical assistant generating a realistic and medically accurate doctor's visit report "
        "(visit summary) based on provided parameters.\n\n"
        "Generate a complete report that includes the following:\n\n"
        "    Visit Date: {date}\n\n"
        "    Clinic or Hospital Location: {location}\n\n"
        "    Severity Level: {severity}\n\n"
        "    (1 = Resuscitation – immediate life threat,\n"
        "    2 = Emergent – potential life threat,\n"
        "    3 = Urgent – stable, needs 2+ resources,\n"
        "    4 = Less-urgent – stable, 1 resource,\n"
        "    5 = Non-urgent – minor complaints)\n\n"
        "    Patient Gender: {patient_gender}\n\n"
        "    Patient Age: {patient_age}\n\n"
        "Required Output Format:\n\n"
        "Write a realistic visit summary that includes the following sections:\n\n"
        "    Chief Complaint – Patient's main reason for visit\n\n"
        "    History of Present Illness (HPI) – Detailed description of symptoms and onset\n\n"
        "    Physical Examination Findings – Based on severity and patient profile\n\n"
        "    Assessment / Diagnosis – Medical evaluation based on findings\n\n"
        "    Plan / Treatment – Medications, procedures, or recommendations\n\n"
        "    Follow-up Instructions – When and how to follow up\n\n"
        "Guidelines:\n\n"
        "    Use realistic data and clinical language; do not use placeholders or generic text.\n\n"
        "    Tailor the content to the provided severity level. For example:\n\n"
        "        Severity 1: Describe immediate life-threatening situations (e.g., cardiac arrest).\n\n"
        "        Severity 5: Describe minor, self-limiting complaints (e.g., mild rash).\n\n"
        "    All content should sound like it was written by a real healthcare provider.\n\n"
        "    Avoid mentioning the parameters directly in the report unless naturally included."
    ),

    REPORT_TYPE_TRAFFIC_INCIDENT: (
        "Generate a detailed and realistic traffic incident report based on the following parameters:\n\n"
        "- Date: {date}\n"
        "- Country: {country}\n"
        "- Municipality: {municipality}\n"
        "- Number of vehicles involved: {number_of_vehicles}\n"
        "- Time of day: {time_of_day} (values: night, morning, day, evening)\n"
        "- Weather conditions: {weather_conditions}\n\n"
        "Write the report in a neutral and professional tone, as if authored by a police officer or accident investigator. "
        "The report must include:\n\n"
        "1. A coherent narrative describing what happened, using realistic names for drivers, passengers, and witnesses.\n"
        "2. Fictional but plausible street names and addresses, based on the provided country and municipality.\n"
        "3. A timeline of the events that is consistent with the given time of day and date.\n"
        "4. Weather and road conditions that match the specified weather conditions and impact the scene as appropriate.\n"
        "5. Realistic but fictional vehicle models, license plates, and damage descriptions.\n"
        "6. No placeholders or parameter names — everything must appear as fully generated, real-world text.\n\n"
        "Ensure that all information in the report logically aligns with the provided parameters. "
        "The output should read as a complete and official report written by a human."
    ),

    REPORT_TYPE_BUILDING_INSPECTION: (
        "Generate an official building inspection report based on the following parameters:\n\n"
        "- Country: {country}\n"
        "- Municipality: {municipality}\n"
        "- Inspection Date: {inspection_date} (format: DD.MM.YYYY)\n"
        "- Building Type: {building_type} (e.g., residential, commercial, industrial, public)\n"
        "- Construction Year: {construction_year}\n\n"
        "Guidelines:\n\n"
        "1. Generate realistic and consistent values for the following:\n"
        "   - **Number of floors**, appropriate for the building type and construction year.\n"
        "   - **Building material**, based on typical materials used in the country and construction era.\n"
        "   - **Inspector name**, use a realistic human name.\n"
        "   - **Weather conditions**, consistent with the country, region, and season based on the inspection date.\n"
        "   - **Noted issues**, relevant to the age, type, and material of the building.\n"
        "   - **Compliance status**, make it realistic based on fictional interpretation of building codes in the given country.\n\n"
        "2. Write the report in a **professional and official tone**, suitable for submission to local or national building authorities.\n\n"
        "3. Include the following sections:\n"
        "   - **1. General Information**: Country, municipality, address (invent one), inspection date, inspector name.\n"
        "   - **2. Building Overview**: Type, construction year, number of floors, primary materials.\n"
        "   - **3. Inspection Context**: Weather conditions on inspection date, purpose of inspection (e.g., routine check, resale, renovation permit).\n"
        "   - **4. Observations and Findings**: Structural, electrical, plumbing, HVAC, fire safety, and accessibility.\n"
        "   - **5. Identified Issues and Recommendations**: List of findings with clear, actionable suggestions.\n"
        "   - **6. Compliance Summary**: Assessment of compliance with local or national building regulations.\n"
        "   - **7. Conclusion**: Overall condition summary, follow-up recommendations if needed, and signature/date.\n\n"
        "4. Do not include placeholders. Use realistic, technically accurate, and country-appropriate content.\n\n"
        "5. Ensure the report reads like an authentic, complete inspection document ready for professional use."
    ),
}

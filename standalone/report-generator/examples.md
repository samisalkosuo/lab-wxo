# report_generator - Examples

Example prompts for the `report_generator` agent, covering the five supported report types, discovery, and refusal behaviour.

1. *"What reports can you generate?"* — Agent calls `list_supported_report_types` and returns a formatted table listing all five supported types (doctor_visit, traffic_incident, building_inspection, project_update, social_services_visit) with descriptions and parameters.

2. *"Generate a doctor visit report for a 45-year-old male patient in Helsinki with severity 3."* — Agent calls `generate_doctor_visit_report` with `location="Helsinki"`, `patient_age=45`, `patient_gender="male"`, `severity=3` and writes a complete clinical visit summary.

3. *"Create a traffic incident report."* — Agent calls `generate_traffic_incident_report` with all parameters left to synthetic defaults (random Finnish municipality, date, number of vehicles, weather conditions) and writes a complete police-style incident report.

4. *"Write a building inspection report for a commercial building in Tampere built in 1995."* — Agent calls `generate_building_inspection_report` with `municipality="Tampere"`, `building_type="commercial"`, `construction_year=1995` and writes a complete official inspection report.

5. *"Generate a quarterly project update report for a healthcare IT project in Q3 2025."* — Agent calls `generate_project_update_report` with `industry="Healthcare"`, `quarter="Q3 2025"` and writes a complete executive stakeholder report.

6. *"Generate a social services visit report for an urgent case in Jyväskylä."* — Agent calls `generate_social_services_visit_report` with `municipality="Jyväskylä"`, `case_severity="Urgent"` and writes a complete social care visit report.

7. *"Write me a financial audit report."* — Agent refuses: explains it only supports the five defined report types and offers to list them. No tool is called and no report is generated.

8. *"Create a random report."* — Agent asks a clarifying question to identify which of the five supported types the user wants, rather than guessing or inventing a new type.

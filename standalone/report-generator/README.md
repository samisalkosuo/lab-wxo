# report_generator — Standalone Agent

Generates realistic structured synthetic reports for five predefined types using the
`tools/report_generator/` tool package. Accepts optional parameters per report type;
missing values are automatically filled with realistic synthetic defaults (Finnish
municipalities, plausible names, dates, industries, etc.). Refuses any request that
does not match one of the five supported types.

## Supported report types

| Type id | Title | Key parameters |
|---|---|---|
| `doctor_visit` | Doctor Visit Summary | location, date, patient_gender, patient_age, severity |
| `traffic_incident` | Traffic Incident Report | date, country, municipality, number_of_vehicles, time_of_day, weather_conditions |
| `building_inspection` | Building Inspection Report | country, municipality, inspection_date, building_type, construction_year |
| `project_update` | Quarterly Project Update Report | project_name, industry, quarter, project_stage, primary_blocker |
| `social_services_visit` | Social Services Visit Report | municipality, country, date, visit_type, household_composition, case_severity |

All parameters are optional. Call `list_supported_report_types` (or just ask the agent
"what reports can you generate?") to see the full parameter list and descriptions.

## Dependencies

The agent uses the shared `tools/report_generator/` package. All six tools from that
package must be imported before deploying the agent:

```bash
# Import the report_generator tool package (run from repo root)
orchestrate tools import --kind python --file tools/report_generator/report_generator.py --upsert
```

`python wxodemo.py deploy report-generator` runs this automatically.

## Deploy

```bash
# Preview
python wxodemo.py deploy report-generator --dry-run

# Deploy (login first)
python wxodemo.py login
python wxodemo.py deploy report-generator

# Confirm it is live
python wxodemo.py status report-generator
```

## Undeploy

```bash
python wxodemo.py undeploy report-generator
```

## Test and evaluate

```bash
# Upload test cases to the WXO Tests tab
python wxodemo.py test-upload report-generator

# Upload and trigger evaluation
python wxodemo.py test-upload report-generator --eval

# Run local ADK evaluation
python wxodemo.py eval report-generator
```

## Examples

See [examples.md](examples.md) for sample prompts covering all five report types,
the discovery path, and refusal behaviour.

## Known limits

- **Synthetic data only.** All generated content is fictional. No real patient,
  incident, or inspection data is used or produced.
- **Finnish defaults.** Random municipalities and person names default to Finnish
  values unless overridden by parameters.
- **No persistence.** Reports are generated in-session and not stored anywhere.
- **Five types only.** Requests for any report type outside the five defined types
  are refused. No new types can be added without updating `tools/report_generator/`.

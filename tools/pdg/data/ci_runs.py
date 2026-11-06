"""Mock CI run history per pipeline (newest first).

Stage values: passed | failed | not_run.
Case B (se-invoice-batch): the tests folder exists, but the CI workflow has no
test stage, so every run shows test = not_run.
"""

from typing import Any, Dict, List

_DATES = [
    "2025-05-11",
    "2025-05-10",
    "2025-05-09",
    "2025-05-08",
    "2025-05-07",
    "2025-05-06",
]


def _runs(pipeline_id: str, build: str, lint: str, test: str) -> List[Dict[str, Any]]:
    return [
        {
            "run_id": f"{pipeline_id}-ci-{len(_DATES) - i}",
            "date": date,
            "branch": "main",
            "stages": {"build": build, "lint": lint, "test": test},
        }
        for i, date in enumerate(_DATES)
    ]


CI_RUNS: Dict[str, List[Dict[str, Any]]] = {
    # No tests exist, so the workflow has nothing to run.
    "fi-customer-ingest": _runs("fi-customer-ingest", "passed", "passed", "not_run"),
    "fi-claims-export": _runs("fi-claims-export", "passed", "passed", "passed"),
    # Case B: tests exist, CI never runs them.
    "se-invoice-batch": _runs("se-invoice-batch", "passed", "passed", "not_run"),
    "se-tax-report": _runs("se-tax-report", "passed", "passed", "passed"),
    "de-payroll-feed": _runs("de-payroll-feed", "passed", "passed", "not_run"),
    "de-sales-rollup": _runs("de-sales-rollup", "passed", "passed", "passed"),
}


def get_runs(pipeline_id: str) -> List[Dict[str, Any]]:
    return CI_RUNS.get(pipeline_id, [])

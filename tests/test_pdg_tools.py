"""Tests for the Pipeline Docs and Test Gap (pdg) tools.

Run with:  pytest tests/test_pdg_tools.py -v

Tools are called via .fn() because @tool wraps the function in a PythonTool object.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tools.pdg.pdg import (  # noqa: E402
    pdg_create_draft_pr,
    pdg_get_ci_history,
    pdg_get_ownership,
    pdg_get_pipeline,
    pdg_list_pipelines,
)


def _call(tool_obj, *args, **kwargs):
    return tool_obj.fn(*args, **kwargs)


def _json(text: str) -> dict:
    return json.loads(text)


def _pr_args(**overrides):
    args = dict(
        repo="fi-customer-data",
        pipeline_id="fi-customer-ingest",
        owner="@aino-virtanen",
        title="Add README and test skeleton",
        readme_path="docs/fi-customer-ingest.md",
        readme_content="# fi-customer-ingest",
        test_path="tests/test_fi_customer_ingest.py",
        test_content="def test_placeholder():\n    assert True\n",
    )
    args.update(overrides)
    return args


# ---------------------------------------------------------------------------
# pdg_list_pipelines
# ---------------------------------------------------------------------------
class TestListPipelines:
    def test_lists_all(self):
        out = _call(pdg_list_pipelines)
        for pid in ("fi-customer-ingest", "se-invoice-batch", "de-payroll-feed", "se-tax-report"):
            assert pid in out
        assert "Showing 6 of 6" in out

    def test_country_filter(self):
        out = _call(pdg_list_pipelines, country="se")
        assert "se-invoice-batch" in out and "fi-customer-ingest" not in out

    def test_case_a_signals(self):
        out = _call(pdg_list_pipelines, gap_type="no_readme")
        assert "fi-customer-ingest" in out and "se-invoice-batch" not in out

    def test_case_b_is_tests_not_in_ci(self):
        out = _call(pdg_list_pipelines, gap_type="tests_not_in_ci")
        assert "se-invoice-batch" in out
        assert "fi-customer-ingest" not in out  # no tests folder: different gap

    def test_case_d_is_no_active_owner(self):
        out = _call(pdg_list_pipelines, gap_type="no_active_owner")
        assert "de-payroll-feed" in out and "se-tax-report" not in out

    def test_healthy_pipelines_have_no_signal(self):
        out = _call(pdg_list_pipelines, country="SE")
        row = [ln for ln in out.splitlines() if "se-tax-report" in ln][0]
        assert row.rstrip().endswith("none |")

    def test_case_c_not_flagged_by_objective_signals(self):
        # Case C needs the country requirement from the KB, not a tool signal.
        row = [ln for ln in _call(pdg_list_pipelines, country="FI").splitlines() if "fi-claims-export" in ln][0]
        assert row.rstrip().endswith("none |")

    def test_bad_country(self):
        err = _json(_call(pdg_list_pipelines, country="NO"))
        assert err["error_code"] == "INVALID_COUNTRY" and "FI" in err["hint"]

    def test_bad_gap_type(self):
        err = _json(_call(pdg_list_pipelines, gap_type="weird"))
        assert err["error_code"] == "INVALID_GAP_TYPE"

    def test_no_match(self):
        out = _call(pdg_list_pipelines, country="SE", gap_type="no_readme")
        assert out.startswith("No pipelines match")


# ---------------------------------------------------------------------------
# pdg_get_pipeline
# ---------------------------------------------------------------------------
class TestGetPipeline:
    def test_case_a(self):
        out = _call(pdg_get_pipeline, "fi-customer-ingest")
        assert "README present: no" in out and "Tests folder present: no" in out

    def test_case_c_readme_lacks_country_section(self):
        out = _call(pdg_get_pipeline, "FI-Claims-Export")
        assert "README present: yes" in out
        assert "Data residency" not in out

    def test_unknown(self):
        err = _json(_call(pdg_get_pipeline, "nope"))
        assert err["error_code"] == "PIPELINE_NOT_FOUND"
        assert "fi-customer-ingest" in err["hint"]


# ---------------------------------------------------------------------------
# pdg_get_ci_history
# ---------------------------------------------------------------------------
class TestCiHistory:
    def test_case_b_tests_never_run(self):
        out = _call(pdg_get_ci_history, "se-invoice-batch")
        assert "did not run in any" in out

    def test_case_e_tests_run(self):
        out = _call(pdg_get_ci_history, "se-tax-report")
        assert "ran in 6 of 6" in out

    def test_limit_is_bounded(self):
        out = _call(pdg_get_ci_history, "se-tax-report", limit=1000)
        assert out.count("se-tax-report-ci-") == 6  # only 6 recorded
        out1 = _call(pdg_get_ci_history, "se-tax-report", limit=0)
        assert out1.count("se-tax-report-ci-") == 1

    def test_unknown(self):
        assert _json(_call(pdg_get_ci_history, "x"))["error_code"] == "PIPELINE_NOT_FOUND"


# ---------------------------------------------------------------------------
# pdg_get_ownership
# ---------------------------------------------------------------------------
class TestOwnership:
    def test_case_d_key_person_risk(self):
        out = _call(pdg_get_ownership, "de-payroll-feed")
        assert "KEY-PERSON RISK" in out
        assert "LEFT THE COMPANY" in out
        assert "`@de-platform-lead`" in out.split("Reviewer to use for a PR:")[1]

    def test_case_e_active_owner(self):
        out = _call(pdg_get_ownership, "se-tax-report")
        assert "Key-person risk:** none" in out
        assert "`@oskar-lund`" in out.split("Reviewer to use for a PR:")[1]

    def test_unknown(self):
        assert _json(_call(pdg_get_ownership, "x"))["error_code"] == "PIPELINE_NOT_FOUND"


# ---------------------------------------------------------------------------
# pdg_create_draft_pr
# ---------------------------------------------------------------------------
class TestCreateDraftPr:
    def test_success_is_draft_and_deterministic(self):
        a = _json(_call(pdg_create_draft_pr, **_pr_args()))
        b = _json(_call(pdg_create_draft_pr, **_pr_args()))
        assert a["status"] == "success" and a["draft"] is True
        assert a["pr_id"] == b["pr_id"] and a["pr_id"].startswith("PR-")
        assert a["reviewer"] == "@aino-virtanen"
        assert a["files"] == ["docs/fi-customer-ingest.md", "tests/test_fi_customer_ingest.py"]

    def test_readme_only_ok(self):
        out = _json(_call(pdg_create_draft_pr, **_pr_args(test_path=None, test_content=None)))
        assert out["status"] == "success" and len(out["files"]) == 1

    def test_empty_strings_mean_not_provided(self):
        # The approval flow passes "" for omitted fields.
        out = _json(_call(pdg_create_draft_pr, **_pr_args(test_path="", test_content="")))
        assert out["status"] == "success" and out["files"] == ["docs/fi-customer-ingest.md"]

    def test_no_parameter_makes_it_ready(self):
        import inspect
        params = inspect.signature(pdg_create_draft_pr.fn).parameters
        assert not any("draft" in name or "ready" in name for name in params)

    def test_fallback_reviewer_for_case_d(self):
        out = _json(_call(
            pdg_create_draft_pr,
            **_pr_args(repo="de-hr-analytics", pipeline_id="de-payroll-feed", owner="@de-platform-lead"),
        ))
        assert out["status"] == "success" and out["reviewer"] == "@de-platform-lead"

    def test_departed_owner_rejected_for_case_d(self):
        err = _json(_call(
            pdg_create_draft_pr,
            **_pr_args(repo="de-hr-analytics", pipeline_id="de-payroll-feed", owner="@jonas-keller"),
        ))
        assert err["error_code"] == "OWNER_MISMATCH" and "@de-platform-lead" in err["hint"]

    def test_unknown_pipeline(self):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(pipeline_id="nope")))
        assert err["error_code"] == "PIPELINE_NOT_FOUND"

    def test_repo_mismatch(self):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(repo="se-billing-platform")))
        assert err["error_code"] == "REPO_MISMATCH" and "fi-customer-data" in err["hint"]

    def test_owner_mismatch(self):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(owner="@elin-berg")))
        assert err["error_code"] == "OWNER_MISMATCH"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"readme_path": "src/main.py"},
            {"readme_path": ".github/workflows/ci.yml"},
            {"readme_path": "docs/../src/main.py"},
            {"readme_path": "/docs/readme.md"},
            {"test_path": "docs/not_tests.py"},
            {"test_path": "tests\\x.py"},
        ],
    )
    def test_path_outside_allowed_prefixes(self, kwargs):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(**kwargs)))
        assert err["error_code"] == "PATH_NOT_ALLOWED"

    def test_path_without_content(self):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(readme_content=None)))
        assert err["error_code"] == "INCOMPLETE_FILE"

    def test_no_files(self):
        err = _json(_call(
            pdg_create_draft_pr,
            **_pr_args(readme_path=None, readme_content=None, test_path=None, test_content=None),
        ))
        assert err["error_code"] == "NO_FILES"

    def test_empty_title(self):
        err = _json(_call(pdg_create_draft_pr, **_pr_args(title="  ")))
        assert err["error_code"] == "MISSING_TITLE"

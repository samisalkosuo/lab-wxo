"""Pipeline Docs and Test Gap tools for watsonx Orchestrate.

Read-only diagnostic tools over a static mock pipeline catalog, plus one mock
write tool (pdg_create_draft_pr) that only the pdg_request_draft_pr approval
flow calls. The write tool is deterministic and stores nothing.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import catalog, ci_runs, ownership
except ImportError:
    from data import catalog, ci_runs, ownership


GAP_TYPES = ["no_readme", "no_tests", "tests_not_in_ci", "no_active_owner"]
MAX_LIST_ROWS = 10
MAX_CI_RUNS = 10
ALLOWED_PATH_PREFIXES = {"readme": "docs/", "test": "tests/"}


def _error(code: str, message: str, hint: str) -> str:
    return json.dumps(
        {"status": "error", "error_code": code, "message": message, "hint": hint},
        indent=2,
    )


def _clean(value: Optional[str]) -> str:
    return value.strip().lower() if value else ""


def _tests_never_run(pipeline_id: str) -> bool:
    runs = ci_runs.get_runs(pipeline_id)
    return bool(runs) and all(r["stages"].get("test") == "not_run" for r in runs)


def _objective_gaps(p: Dict[str, Any]) -> List[str]:
    """Gaps that can be read from catalog, CI history and ownership alone."""
    pid = p["pipeline_id"]
    gaps: List[str] = []
    if not p["readme_present"]:
        gaps.append("no_readme")
    if not p["tests_folder_present"]:
        gaps.append("no_tests")
    elif _tests_never_run(pid):
        gaps.append("tests_not_in_ci")
    if not ownership.active_codeowners(pid):
        gaps.append("no_active_owner")
    return gaps


# ---------------------------------------------------------------------------
# Tool 1: pdg_list_pipelines
# ---------------------------------------------------------------------------
@tool
def pdg_list_pipelines(country: Optional[str] = None, gap_type: Optional[str] = None) -> str:
    """Lists data pipelines in the platform catalog with quick documentation and test signals.

    Use this tool first to get an overview of pipelines, optionally for one country,
    and to see which ones show an objective gap signal. The gap filter only covers
    signals that can be read from the catalog, CI history and ownership: missing README,
    missing tests, tests that exist but never run in CI, and no active owner. It does not
    cover country-specific documentation requirements; check those with the knowledge base.

    Args:
        country (str, optional): Country code 'FI', 'SE' or 'DE'. If omitted, all countries are listed.
        gap_type (str, optional): One of 'no_readme', 'no_tests', 'tests_not_in_ci', 'no_active_owner'.
            If omitted, all pipelines are listed.

    Returns:
        str: A Markdown table (at most 10 rows) with pipeline ID, country, repo, README,
            tests folder, personal-data flag and the objective gap signals, followed by
            summary counts. Returns a structured error for an unknown country or gap_type.
    """
    clean_country = country.strip().upper() if country else None
    if clean_country and clean_country not in catalog.COUNTRIES:
        return _error(
            "INVALID_COUNTRY",
            f"Unknown country '{country}'.",
            f"Valid country codes are: {', '.join(catalog.COUNTRIES)}. Or omit country to see all.",
        )
    clean_gap = _clean(gap_type) or None
    if clean_gap and clean_gap not in GAP_TYPES:
        return _error(
            "INVALID_GAP_TYPE",
            f"Unknown gap_type '{gap_type}'.",
            f"Valid gap types are: {', '.join(GAP_TYPES)}. Or omit gap_type to see all.",
        )

    rows = []
    for p in catalog.list_pipelines(clean_country):
        gaps = _objective_gaps(p)
        if clean_gap and clean_gap not in gaps:
            continue
        rows.append((p, gaps))

    if not rows:
        return "No pipelines match the filters (country={}, gap_type={}).".format(
            clean_country or "ANY", clean_gap or "ANY"
        )

    total = len(rows)
    shown = rows[:MAX_LIST_ROWS]
    lines = [
        "| Pipeline ID | Country | Repo | README | Tests folder | Personal data | Objective gap signals |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for p, gaps in shown:
        lines.append(
            f"| `{p['pipeline_id']}` | {p['country']} | `{p['repo']}` | "
            f"{'yes' if p['readme_present'] else 'no'} | "
            f"{'yes' if p['tests_folder_present'] else 'no'} | "
            f"{'yes' if p['handles_personal_data'] else 'no'} | "
            f"{', '.join(gaps) if gaps else 'none'} |"
        )
    flagged = sum(1 for _, g in rows if g)
    lines.append("")
    lines.append(
        f"Showing {len(shown)} of {total} pipelines; {flagged} with at least one objective gap signal. "
        "Country-specific requirements are not included in these signals."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: pdg_get_pipeline
# ---------------------------------------------------------------------------
@tool
def pdg_get_pipeline(pipeline_id: str) -> str:
    """Retrieves metadata plus documentation and test status for one pipeline.

    Use this tool to inspect a single pipeline: what it does, its inputs, outputs and
    schedule, whether it handles personal data, which README sections exist, and whether
    a tests folder exists. Compare the README sections with the documentation standard
    and the country requirement from the knowledge base. It returns metadata only, never
    source code.

    Args:
        pipeline_id (str): Pipeline ID, e.g. 'fi-customer-ingest'. Case-insensitive.

    Returns:
        str: A structured summary of the pipeline. Returns a structured error listing
            valid pipeline IDs if not found.
    """
    pid = _clean(pipeline_id)
    p = catalog.get_pipeline(pid)
    if not p:
        return _error(
            "PIPELINE_NOT_FOUND",
            f"Pipeline '{pipeline_id}' not found.",
            f"Known pipeline IDs are: {', '.join(catalog.get_pipeline_ids())}.",
        )

    sections = ", ".join(p["readme_sections"]) if p["readme_sections"] else "n/a"
    return (
        f"### Pipeline {p['pipeline_id']}\n\n"
        f"- **Country:** `{p['country']}`\n"
        f"- **Repo:** `{p['repo']}`\n"
        f"- **Description:** {p['description']}\n"
        f"- **Inputs:** {'; '.join(p['inputs'])}\n"
        f"- **Outputs:** {'; '.join(p['outputs'])}\n"
        f"- **Schedule:** {p['schedule']}\n"
        f"- **Handles personal data:** {'yes' if p['handles_personal_data'] else 'no'}\n\n"
        f"**Documentation status:**\n"
        f"- README present: {'yes' if p['readme_present'] else 'no'}\n"
        f"- README sections: {sections}\n\n"
        f"**Test status:**\n"
        f"- Tests folder present: {'yes' if p['tests_folder_present'] else 'no'}\n"
        f"- Test count: {p['test_count']}\n"
        f"- Whether CI runs them: use pdg_get_ci_history"
    )


# ---------------------------------------------------------------------------
# Tool 3: pdg_get_ci_history
# ---------------------------------------------------------------------------
@tool
def pdg_get_ci_history(pipeline_id: str, limit: int = 6) -> str:
    """Retrieves recent CI runs for a pipeline and shows whether its tests are actually executed.

    Use this tool when a pipeline has a tests folder, to check whether the test stage
    runs in CI. A tests folder alone does not mean tests are effective: a test stage
    marked 'not_run' in every recent run means the tests are never executed.

    Args:
        pipeline_id (str): Pipeline ID, e.g. 'se-invoice-batch'. Case-insensitive.
        limit (int): Maximum number of runs to return (default 6, max 10).

    Returns:
        str: A Markdown table of recent runs (newest first) with build, lint and test
            stage results, and a one-line verdict about test execution. Returns a
            structured error if the pipeline is unknown.
    """
    pid = _clean(pipeline_id)
    p = catalog.get_pipeline(pid)
    if not p:
        return _error(
            "PIPELINE_NOT_FOUND",
            f"Pipeline '{pipeline_id}' not found.",
            f"Known pipeline IDs are: {', '.join(catalog.get_pipeline_ids())}.",
        )

    bounded = min(max(limit, 1), MAX_CI_RUNS)
    runs = ci_runs.get_runs(pid)[:bounded]
    if not runs:
        return f"No CI runs recorded for pipeline `{pid}`."

    lines = [
        f"### CI history for `{pid}` (latest {len(runs)} runs)\n",
        "| Run | Date | Branch | Build | Lint | Test |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in runs:
        s = r["stages"]
        lines.append(
            f"| `{r['run_id']}` | {r['date']} | {r['branch']} | {s['build']} | {s['lint']} | {s['test']} |"
        )
    executed = sum(1 for r in runs if r["stages"]["test"] != "not_run")
    if executed == 0:
        verdict = "Test stage did not run in any of these runs."
    else:
        verdict = f"Test stage ran in {executed} of {len(runs)} runs."
    lines.append("")
    lines.append(f"**Verdict:** {verdict}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 4: pdg_get_ownership
# ---------------------------------------------------------------------------
@tool
def pdg_get_ownership(pipeline_id: str) -> str:
    """Retrieves CODEOWNERS and committer activity for a pipeline and flags key-person risk.

    Use this tool to find who should review a change and whether the pipeline has an
    active owner. If no CODEOWNERS entry belongs to an active committer, the pipeline has
    key-person risk and the result names a fallback reviewer.

    Args:
        pipeline_id (str): Pipeline ID, e.g. 'de-payroll-feed'. Case-insensitive.

    Returns:
        str: CODEOWNERS, committers with last commit date and active flag, a key-person
            risk verdict, and the reviewer to use. Returns a structured error if the
            pipeline is unknown.
    """
    pid = _clean(pipeline_id)
    p = catalog.get_pipeline(pid)
    data = ownership.get_ownership(pid)
    if not p or not data:
        return _error(
            "PIPELINE_NOT_FOUND",
            f"Pipeline '{pipeline_id}' not found.",
            f"Known pipeline IDs are: {', '.join(catalog.get_pipeline_ids())}.",
        )

    active = ownership.active_codeowners(pid)
    fallback = ownership.FALLBACK_REVIEWERS[p["country"]]
    committers = "\n".join(
        f"- `{c['handle']}`: last commit {c['last_commit']}, {'active' if c['active'] else 'LEFT THE COMPANY'}"
        for c in data["committers"]
    )
    if active:
        risk = "none (at least one CODEOWNER is an active committer)"
        reviewer = active[0]
    else:
        risk = "KEY-PERSON RISK: no CODEOWNER is an active committer"
        reviewer = fallback
    return (
        f"### Ownership for `{pid}`\n\n"
        f"- **CODEOWNERS:** {', '.join(f'`{o}`' for o in data['codeowners'])}\n"
        f"- **Fallback reviewer ({p['country']}):** `{fallback}`\n\n"
        f"**Committers:**\n{committers}\n\n"
        f"**Key-person risk:** {risk}\n"
        f"**Reviewer to use for a PR:** `{reviewer}`"
    )


# ---------------------------------------------------------------------------
# Tool 5: pdg_create_draft_pr (mock write tool; called only by the approval flow)
# ---------------------------------------------------------------------------
def _path_problem(path: str, label: str) -> Optional[str]:
    if not path or path.startswith("/") or ".." in path.split("/") or "\\" in path:
        return "must be a relative path without '..' or backslashes"
    prefix = ALLOWED_PATH_PREFIXES[label]
    if not path.startswith(prefix):
        return f"a {label} file must start with '{prefix}'"
    return None


@tool
def pdg_create_draft_pr(
    repo: str,
    pipeline_id: str,
    owner: str,
    title: str,
    readme_path: Optional[str] = None,
    readme_content: Optional[str] = None,
    test_path: Optional[str] = None,
    test_content: Optional[str] = None,
) -> str:
    """Creates a DRAFT pull request that adds documentation and/or a test skeleton for a pipeline.

    NOTE: This is a restricted write tool designed for use exclusively by the
    pdg_request_draft_pr approval flow. It must NOT be called directly by agents.
    The pull request is always a draft: there is no parameter to make it ready.
    Review and merge stay with the repository's existing PR process.
    This is a deterministic mock: nothing is stored and no real repository is touched.

    Args:
        repo (str): Repository name; must be the repo of the pipeline in the catalog.
        pipeline_id (str): Pipeline ID; must exist in the catalog.
        owner (str): Reviewer handle; must be an active CODEOWNER of the pipeline, or the
            country fallback reviewer when the pipeline has no active owner.
        title (str): Pull request title.
        readme_path (str, optional): Path of the README to add; must start with 'docs/'.
        readme_content (str, optional): README content.
        test_path (str, optional): Path of the test skeleton to add; must start with 'tests/'.
        test_content (str, optional): Test skeleton content.

    Returns:
        str: A structured draft-PR record with a deterministic ID, or a structured error.
    """
    pid = _clean(pipeline_id)
    p = catalog.get_pipeline(pid)
    if not p:
        return _error(
            "PIPELINE_NOT_FOUND",
            f"Pipeline '{pipeline_id}' not found.",
            f"Known pipeline IDs are: {', '.join(catalog.get_pipeline_ids())}.",
        )

    clean_repo = _clean(repo)
    if clean_repo != p["repo"]:
        return _error(
            "REPO_MISMATCH",
            f"Repo '{repo}' does not belong to pipeline '{pid}'.",
            f"Pipeline '{pid}' lives in repo '{p['repo']}'.",
        )

    active = ownership.active_codeowners(pid)
    fallback = ownership.FALLBACK_REVIEWERS[p["country"]]
    allowed_owners = active if active else [fallback]
    clean_owner = _clean(owner)
    if clean_owner not in [o.lower() for o in allowed_owners]:
        return _error(
            "OWNER_MISMATCH",
            f"'{owner}' is not an allowed reviewer for pipeline '{pid}'.",
            f"Allowed reviewer(s): {', '.join(allowed_owners)}. Call pdg_get_ownership to confirm.",
        )
    reviewer = next(o for o in allowed_owners if o.lower() == clean_owner)

    files: Dict[str, str] = {}
    for label, path, content in (
        ("readme", readme_path or None, readme_content or None),
        ("test", test_path or None, test_content or None),
    ):
        if path is None and content is None:
            continue
        if not path or content is None:
            return _error(
                "INCOMPLETE_FILE",
                f"The {label} file needs both a path and content.",
                f"Provide both {label}_path and {label}_content, or neither.",
            )
        problem = _path_problem(path, label)
        if problem:
            return _error(
                "PATH_NOT_ALLOWED",
                f"Path '{path}' is rejected: {problem}.",
                "Only the README under 'docs/' and the test skeleton under 'tests/' can be written.",
            )
        files[path] = content

    if not files:
        return _error(
            "NO_FILES",
            "The draft PR contains no files.",
            "Provide readme_path with readme_content and/or test_path with test_content.",
        )
    if not title or not title.strip():
        return _error("MISSING_TITLE", "The PR title is empty.", "Provide a short PR title.")

    hash_seed = f"{clean_repo}|{pid}|{reviewer}|{title}|{'|'.join(sorted(files))}".encode("utf-8")
    pr_number = int(hashlib.md5(hash_seed).hexdigest()[:4], 16) % 9000 + 1000
    pr_id = f"PR-{pr_number}"

    result = {
        "status": "success",
        "pr_id": pr_id,
        "draft": True,
        "repo": clean_repo,
        "pipeline_id": pid,
        "title": title,
        "reviewer": reviewer,
        "branch": f"pdg/{pid}-docs-tests",
        "files": sorted(files),
        "created_at": "2025-05-12T14:30:00Z",
        "message": (
            f"Draft PR {pr_id} created in {clean_repo} with {len(files)} file(s) and review "
            f"requested from {reviewer}. It stays a draft: review and merge follow the "
            "repository's existing PR process. (Mock record: no real repository was changed.)"
        ),
    }
    return json.dumps(result, indent=2)

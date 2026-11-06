"""Draft-PR approval flow for the Pipeline Docs and Test Gap demo.

The pipeline_doc_gap agent calls this flow instead of calling
pdg_create_draft_pr directly, so no pull request is created without an explicit
human click. The PR is always a draft; review and merge stay with the
repository's existing PR process.

Flow name (tool name visible to agents): pdg_request_draft_pr

Inputs the agent must supply:
  - repo, pipeline_id, owner : must match the catalog (checked again by the tool)
  - title                    : draft PR title
  - justification            : evidence for the gap, with the standard ID cited
  - readme_path/_content     : optional README under docs/
  - test_path/_content       : optional test skeleton under tests/

Flow behavior:
  1. A user activity shows the proposed draft PR, justification and file contents.
  2. The user clicks "Approve" or "Reject".
  3. Approve  -> tool node calls pdg_create_draft_pr -> result script -> END.
  4. Reject   -> rejection script -> END. Nothing is created.

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/pdg \\
      -f tools/pdg/pdg.py -r tools/pdg/requirements.txt
  orchestrate tools import -k flow -f flows/pipeline_doc_gap/pdg_request_draft_pr.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


class DraftPrRequest(BaseModel):
    """Input the pipeline_doc_gap agent passes to the approval flow."""

    repo: str = Field(description="Repository name of the pipeline, e.g. 'fi-customer-data'.")
    pipeline_id: str = Field(description="Pipeline ID, e.g. 'fi-customer-ingest'.")
    owner: str = Field(
        description=(
            "Reviewer handle: an active CODEOWNER from pdg_get_ownership, or the fallback "
            "reviewer when the pipeline has no active owner."
        )
    )
    title: str = Field(description="Short title for the draft pull request.")
    justification: str = Field(
        description=(
            "Evidence-based reasoning for the PR, citing the standard ID (e.g. STD-DOC-01). "
            "Shown verbatim to the approver."
        )
    )
    readme_path: str = Field(default="", description="README path, must start with 'docs/'. Empty if none.")
    readme_content: str = Field(default="", description="README content. Empty if none.")
    test_path: str = Field(default="", description="Test skeleton path, must start with 'tests/'. Empty if none.")
    test_content: str = Field(default="", description="Test skeleton content. Empty if none.")


class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(default="pending", description="'approved' or 'rejected'.")
    execution_result: str = Field(default="", description="Output of pdg_create_draft_pr on approval.")
    message: str = Field(default="", description="Final message for the agent.")


class CreateDraftPrInput(BaseModel):
    """Arguments of the pdg_create_draft_pr Python tool."""

    repo: str = Field(description="Repository name.")
    pipeline_id: str = Field(description="Pipeline ID.")
    owner: str = Field(description="Reviewer handle.")
    title: str = Field(description="Draft PR title.")
    readme_path: str = Field(default="", description="README path.")
    readme_content: str = Field(default="", description="README content.")
    test_path: str = Field(default="", description="Test skeleton path.")
    test_content: str = Field(default="", description="Test skeleton content.")


class DraftPrResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Human decision: 'approved' or 'rejected'.")
    repo: str = Field(description="Repository the PR was proposed for.")
    pipeline_id: str = Field(description="Pipeline the PR was proposed for.")
    execution_result: str = Field(
        default="",
        description="JSON output of pdg_create_draft_pr on approval. Empty string on rejection.",
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: the draft PR record. On rejection: nothing was created."
        )
    )


@flow(
    name="pdg_request_draft_pr",
    display_name="Request Draft PR Approval",
    description=(
        "Governance gate for opening a draft pull request with documentation and/or a test "
        "skeleton for a pipeline. Shows the proposed PR and justification to a human approver. "
        "On approval, calls pdg_create_draft_pr (always a draft) and returns the PR record. "
        "On rejection, returns a clear 'rejected - nothing created' result. "
        "Always use this flow instead of calling pdg_create_draft_pr directly. "
        "Required inputs: repo, pipeline_id, owner, title, justification, and at least one of "
        "readme_path+readme_content or test_path+test_content."
    ),
    input_schema=DraftPrRequest,
    output_schema=DraftPrResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_pdg_request_draft_pr_flow(aflow: Flow = None) -> Flow:
    """Present a draft PR proposal for human approval; create it only on approval."""

    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Draft PR Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Draft PR Approval Request",
        instructions=(
            "Review the proposed draft pull request below. "
            "Click 'Approve' to open it as a draft, or 'Reject' to cancel with nothing created."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )

    for name, label, expr in (
        ("repo_display", "Repository", "{flow.input.repo}"),
        ("pipeline_display", "Pipeline", "{flow.input.pipeline_id}"),
        ("reviewer_display", "Reviewer", "{flow.input.owner}"),
        ("title_display", "PR Title", "{flow.input.title}"),
        ("justification_display", "Agent Justification", "{flow.input.justification}"),
        ("readme_path_display", "README Path", "{flow.input.readme_path}"),
        ("readme_display", "README Content", "{flow.input.readme_content}"),
        ("test_path_display", "Test Skeleton Path", "{flow.input.test_path}"),
        ("test_display", "Test Skeleton Content", "{flow.input.test_content}"),
    ):
        approval_form.message_output_field(name=name, label=label, message=expr)

    record_approved = user_flow.script(
        name="record_approved",
        script='flow.private.decision = "approved"',
    )
    record_rejected = user_flow.script(
        name="record_rejected",
        script='flow.private.decision = "rejected"',
    )
    reject_btn = user_flow.add_button("Reject")

    user_flow.edge(START, approval_form)
    user_flow.edge(approval_form, record_approved, button_label="Approve")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # Explicit input schema: letting the ADK resolve it from the deployed tool
    # produced an untyped "data" argument in the Incident Triage flow (status 424).
    create_node = aflow.tool(
        "pdg_create_draft_pr",
        input_schema=CreateDraftPrInput,
    )
    for var in (
        "repo",
        "pipeline_id",
        "owner",
        "title",
        "readme_path",
        "readme_content",
        "test_path",
        "test_content",
    ):
        create_node.map_input(input_variable=var, expression=f"flow.input.{var}")

    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
flow.private.decision         = "approved"
flow.private.execution_result = str(flow.nodes['pdg_create_draft_pr'].output)
flow.private.message = (
    "APPROVED by the approver. "
    f"Repo: {flow.input.repo}, pipeline: {flow.input.pipeline_id}. "
    f"pdg_create_draft_pr returned: {flow.private.execution_result}"
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
flow.private.decision         = "rejected"
flow.private.execution_result = ""
flow.private.message = (
    "REJECTED. No pull request was created. "
    f"The proposed draft PR for pipeline '{flow.input.pipeline_id}' "
    f"in repo '{flow.input.repo}' was declined by the approver."
)
""",
    )

    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=create_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(create_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    aflow.map_output(output_variable="decision",         expression="flow.private.decision")
    aflow.map_output(output_variable="repo",             expression="flow.input.repo")
    aflow.map_output(output_variable="pipeline_id",      expression="flow.input.pipeline_id")
    aflow.map_output(output_variable="execution_result", expression="flow.private.execution_result")
    aflow.map_output(output_variable="message",          expression="flow.private.message")

    return aflow

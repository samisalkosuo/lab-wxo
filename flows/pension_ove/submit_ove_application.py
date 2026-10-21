"""OVE Application Submission Flow for watsonx Orchestrate.

Governance gate for formal Partial Early Old-Age Pension (OVE) applications.
Presents the calculated OVE election details to the member or advisor for confirmation.
On approval, registers the official application record and generates a binding application ID.
On rejection, cancels the submission without changes.

Flow name: ove_submit_application
"""

from typing import Optional
from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class OveApplicationRequest(BaseModel):
    """Input the pension advisor agent passes to the approval flow."""

    member_id: str = Field(
        description="Member reference ID (e.g. 'MEM-101', 'MEM-103')."
    )
    draw_percentage: int = Field(
        description="Chosen OVE draw percentage (must be 25 or 50)."
    )
    start_date: str = Field(
        description="Requested OVE commencement date in YYYY-MM-DD format (e.g. '2026-05-01')."
    )
    projected_salary: float = Field(
        default=0.0,
        description="Expected future monthly gross salary if continuing work alongside OVE."
    )
    justification: str = Field(
        description="Summary of calculation findings, reduction percentage, and advisory notes shown to the approver."
    )


# ---------------------------------------------------------------------------
# Private schema — carries the human decision across the userflow boundary
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(
        default="pending",
        description="Human decision written by userflow scripts: 'approved' or 'rejected'."
    )


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class OveApplicationResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Human decision: 'approved' or 'rejected'.")
    application_id: str = Field(default="", description="Generated formal application reference ID on approval.")
    member_id: str = Field(description="Member ID.")
    draw_percentage: str = Field(description="Confirmed draw percentage.")
    start_date: str = Field(description="Confirmed start date.")
    message: str = Field(
        description="Human-readable resolution message that the agent should report verbatim to the user."
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="ove_submit_application",
    display_name="Submit OVE Pension Application",
    description=(
        "Human governance gate for formal Partial Early Old-Age Pension (OVE) application filings. "
        "Presents the proposed draw percentage, start date, and reduction calculations for confirmation. "
        "On approval, registers the official application record and issues an application ID. "
        "On rejection, terminates the process without filing. "
        "Required inputs: member_id, draw_percentage, start_date, justification."
    ),
    input_schema=OveApplicationRequest,
    output_schema=OveApplicationResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_ove_application_flow(aflow: Flow = None) -> Flow:
    """Presents OVE application for confirmation; registers application only on approval."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "OVE Application Confirmation"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Confirm OVE Application Submission",
        instructions=(
            "Please review the Partial Early Old-Age Pension (OVE) calculation details below. "
            "Click 'Approve' to formally submit the application, or 'Reject' to cancel."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )

    approval_form.message_output_field(
        name="member_display",
        label="Member ID",
        message="{flow.input.member_id}",
    )
    approval_form.message_output_field(
        name="draw_display",
        label="Requested Draw Percentage",
        message="{flow.input.draw_percentage}%",
    )
    approval_form.message_output_field(
        name="start_display",
        label="Target Start Date",
        message="{flow.input.start_date}",
    )
    approval_form.message_output_field(
        name="salary_display",
        label="Projected Monthly Salary",
        message="{flow.input.projected_salary} EUR",
    )
    approval_form.message_output_field(
        name="justification_display",
        label="Calculation Summary & Advisory Notes",
        message="{flow.input.justification}",
    )

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

    # ── Result scripts in outer flow ───────────────────────────────────────
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision = "approved"
self.output.application_id = f"OVE-APP-{flow.input.member_id}-2026"
self.output.member_id = flow.input.member_id
self.output.draw_percentage = f"{flow.input.draw_percentage}%"
self.output.start_date = flow.input.start_date
self.output.message = (
    f"OVE application successfully registered under reference ID {self.output.application_id}. "
    "Formal pension decision and payout schedule will be dispatched via official postal/electronic mailbox."
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
self.output.decision = "rejected"
self.output.application_id = ""
self.output.member_id = flow.input.member_id
self.output.draw_percentage = f"{flow.input.draw_percentage}%"
self.output.start_date = flow.input.start_date
self.output.message = (
    "OVE application was rejected/cancelled by the user. "
    "No formal changes or pension elections were submitted."
)
""",
    )

    # ── Branching based on human decision ──────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=approved_result,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Edges ──────────────────────────────────────────────────────────────
    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

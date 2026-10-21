"""Resource reclamation approval flow for the Cloud FinOps demo.

The cloud_finops agent calls this flow instead of calling cf_reclaim_resource
directly. The flow shows the proposed reclamation to a cost owner. Only on
Approve does it call cf_reclaim_resource.

Flow name (tool name visible to the agent): cf_approve_reclaim

Governance rule (Rule 7 — wxo-scenario-authoring):
  The flow script verifies that the resource_id belongs to account_id before
  calling the write tool. A mismatch returns an error; the write tool is
  never called.

Inputs the agent must supply:
  - resource_id   : the resource to reclaim (e.g. 'vm-zombie-01')
  - account_id    : the account that owns it (e.g. 'acct-001')
  - justification : agent's evidence-based reasoning for proposing reclamation
  - policy_ref    : policy document ID cited (e.g. 'CF-POL-01'), optional

Flow behaviour:
  1. A prepare script resolves a display description for the resource.
  2. A userflow form shows the proposal to the cost owner (Approve / Reject).
  3. Each button routes to a script that writes the decision to flow.private.
  4. After the userflow, a conditions branch checks flow.private.decision.
  5. Approve → tool node calls cf_reclaim_resource → result script → END.
  6. Reject  → rejection script → END. Nothing is reclaimed.

Import prerequisites (tool must be imported before this flow):
  orchestrate tools import -k python -p tools/cloud_finops \\
      -f tools/cloud_finops/cloud_finops.py \\
      -r tools/cloud_finops/requirements.txt
  orchestrate tools import -k flow -f flows/cf_approve_reclaim/cf_approve_reclaim.py

Not tested against a live instance. Follows flows/incident_triage/request_remediation.py
and flows/hr_onboarding/hr_request_provisioning.py.
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ReclaimRequest(BaseModel):
    """Input the cloud_finops agent passes to the reclamation approval flow."""

    resource_id: str = Field(
        description=(
            "The cloud resource to reclaim. One of: vm-zombie-01, vm-idle-finance-01, "
            "vm-idle-dev-03. Never vm-batch-weekend-01 (has a scheduled job)."
        )
    )
    account_id: str = Field(
        description="The account that owns the resource. Must be 'acct-001'."
    )
    justification: str = Field(
        description=(
            "Agent's evidence-based reasoning for proposing reclamation. "
            "Cite utilisation data and the policy document ID. "
            "Shown verbatim to the cost owner in the form."
        )
    )
    policy_ref: str = Field(
        default="",
        description="Policy document ID cited as the basis (e.g. 'CF-POL-01' or 'CF-POL-02').",
    )


# ---------------------------------------------------------------------------
# Private schema
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(
        default="pending",
        description="Cost-owner decision: 'approved' or 'rejected'.",
    )


# ---------------------------------------------------------------------------
# Schema for the cf_reclaim_resource tool node
# ---------------------------------------------------------------------------
class ReclaimInput(BaseModel):
    """Arguments of the cf_reclaim_resource Python tool."""

    resource_id: str = Field(description="Resource to reclaim.")
    account_id: str = Field(description="Account the resource belongs to.")
    approved_by: str = Field(description="Approver label.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ReclaimResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="'approved' or 'rejected'.")
    resource_id: str = Field(description="Resource that was acted on.")
    account_id: str = Field(description="Account the resource belongs to.")
    policy_ref: str = Field(description="Policy document cited by the agent.")
    execution_result: str = Field(
        default="",
        description="Output of cf_reclaim_resource on approval. Empty on rejection.",
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: execution outcome. "
            "On rejection: clear statement that nothing was reclaimed."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="cf_approve_reclaim",
    display_name="Approve Resource Reclamation",
    description=(
        "Governance gate for reclaiming an idle or zombie cloud resource. "
        "Shows the proposed reclamation and justification to a cost owner. "
        "On approval, calls cf_reclaim_resource and returns the result. "
        "On rejection, returns 'rejected — nothing reclaimed'. "
        "Always use this flow instead of calling cf_reclaim_resource directly. "
        "Required inputs: resource_id, account_id, justification. "
        "Optional: policy_ref (e.g. CF-POL-01 for idle, CF-POL-02 for zombie)."
    ),
    input_schema=ReclaimRequest,
    output_schema=ReclaimResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_cf_approve_reclaim_flow(aflow: Flow = None) -> Flow:
    """Show a reclamation proposal to a cost owner; reclaim only on approval."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Cost Owner Approval (Reclaim)"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Resource Reclamation Approval",
        instructions=(
            "Approver: Cost Owner. Review the proposed resource reclamation below. "
            "Click 'Approve' to reclaim the resource, or 'Reject' to cancel with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )

    approval_form.message_output_field(
        name="resource_display",
        label="Resource ID",
        message="{flow.input.resource_id}",
    )
    approval_form.message_output_field(
        name="account_display",
        label="Account ID",
        message="{flow.input.account_id}",
    )
    approval_form.message_output_field(
        name="policy_display",
        label="Policy Reference",
        message="{flow.input.policy_ref}",
    )
    approval_form.message_output_field(
        name="justification_display",
        label="Agent Justification",
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

    # ── Tool node for approved path ────────────────────────────────────────
    reclaim_node = aflow.tool("cf_reclaim_resource", input_schema=ReclaimInput)
    reclaim_node.map_input(input_variable="resource_id", expression="flow.input.resource_id")
    reclaim_node.map_input(input_variable="account_id",  expression="flow.input.account_id")
    reclaim_node.map_input(input_variable="approved_by", expression='"Cost Owner"')

    # ── Result scripts ─────────────────────────────────────────────────────
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision         = "approved"
self.output.resource_id      = flow.input.resource_id
self.output.account_id       = flow.input.account_id
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = str(flow.nodes['cf_reclaim_resource'].output)
self.output.message = (
    "APPROVED BY COST OWNER AND EXECUTED. "
    f"Resource: {flow.input.resource_id}, Account: {flow.input.account_id}. "
    f"Policy: {flow.input.policy_ref or 'N/A'}. "
    f"Execution result: {self.output.execution_result}"
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
self.output.decision         = "rejected"
self.output.resource_id      = flow.input.resource_id
self.output.account_id       = flow.input.account_id
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = ""
self.output.message = (
    "REJECTED BY COST OWNER. No resource was reclaimed. "
    f"Resource: {flow.input.resource_id}, Account: {flow.input.account_id}. "
    "No infrastructure changes were made."
)
""",
    )

    # ── Conditions branch ──────────────────────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=reclaim_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Edges ──────────────────────────────────────────────────────────────
    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(reclaim_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

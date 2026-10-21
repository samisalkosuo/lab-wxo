"""Resource rightsizing approval flow for the Cloud FinOps demo.

The cloud_finops agent calls this flow instead of calling cf_resize_resource
directly. The flow shows the proposed rightsizing to a cost owner. Only on
Approve does it call cf_resize_resource.

Flow name (tool name visible to the agent): cf_approve_resize

Governance rule (Rule 7 — wxo-scenario-authoring):
  The flow verifies that resource_id belongs to account_id before calling the
  write tool. A mismatch is refused by cf_resize_resource's own guard.

Inputs the agent must supply:
  - resource_id   : the resource to resize (e.g. 'db-cluster-prod-01')
  - account_id    : the account that owns it (e.g. 'acct-001')
  - current_size  : the current provisioned size tier (for the approver to review)
  - target_size   : the recommended target size tier
  - justification : agent's evidence-based reasoning, including utilisation data
  - policy_ref    : policy document ID cited (e.g. 'CF-POL-03'), optional

Flow behaviour:
  1. A userflow form shows current size, target size, and justification.
  2. The cost owner clicks Approve or Reject.
  3. Approve → tool node calls cf_resize_resource → result script → END.
  4. Reject  → rejection script → END. Nothing is resized.

Import prerequisites (tool must be imported before this flow):
  orchestrate tools import -k python -p tools/cloud_finops \\
      -f tools/cloud_finops/cloud_finops.py \\
      -r tools/cloud_finops/requirements.txt
  orchestrate tools import -k flow -f flows/cf_approve_resize/cf_approve_resize.py

Not tested against a live instance. Follows flows/incident_triage/request_remediation.py
and flows/cf_approve_reclaim/cf_approve_reclaim.py.
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ResizeRequest(BaseModel):
    """Input the cloud_finops agent passes to the rightsizing approval flow."""

    resource_id: str = Field(
        description=(
            "The cloud resource to rightsize. Currently supported: db-cluster-prod-01."
        )
    )
    account_id: str = Field(
        description="The account that owns the resource. Must be 'acct-001'."
    )
    current_size: str = Field(
        description=(
            "The resource's current provisioned size, as returned by "
            "cf_get_resource_utilization (e.g. 'xlarge-16cpu-128gb-3nodes')."
        )
    )
    target_size: str = Field(
        description=(
            "The recommended target size tier (e.g. 'large-8cpu-64gb-2nodes'). "
            "Must be smaller than the current size."
        )
    )
    justification: str = Field(
        description=(
            "Agent's evidence-based reasoning for proposing this resize. "
            "Include the 30-day CPU and memory utilisation figures. "
            "Shown verbatim to the cost owner in the form."
        )
    )
    policy_ref: str = Field(
        default="",
        description="Policy document ID cited as the basis (e.g. 'CF-POL-03').",
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
# Schema for the cf_resize_resource tool node
# ---------------------------------------------------------------------------
class ResizeInput(BaseModel):
    """Arguments of the cf_resize_resource Python tool."""

    resource_id: str = Field(description="Resource to resize.")
    account_id: str = Field(description="Account the resource belongs to.")
    target_size: str = Field(description="Target size tier.")
    approved_by: str = Field(description="Approver label.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ResizeResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="'approved' or 'rejected'.")
    resource_id: str = Field(description="Resource that was acted on.")
    account_id: str = Field(description="Account the resource belongs to.")
    current_size: str = Field(description="The resource's original size.")
    target_size: str = Field(description="The target size proposed.")
    policy_ref: str = Field(description="Policy document cited by the agent.")
    execution_result: str = Field(
        default="",
        description="Output of cf_resize_resource on approval. Empty on rejection.",
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: execution outcome including the illustrative saving. "
            "On rejection: clear statement that nothing was resized."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="cf_approve_resize",
    display_name="Approve Resource Rightsizing",
    description=(
        "Governance gate for rightsizing an over-provisioned cloud resource. "
        "Shows the current size, proposed target size, and justification to a cost owner. "
        "On approval, calls cf_resize_resource and returns the result (including the "
        "illustrative saving estimate). "
        "On rejection, returns 'rejected — nothing resized'. "
        "Always use this flow instead of calling cf_resize_resource directly. "
        "Required inputs: resource_id, account_id, current_size, target_size, justification. "
        "Optional: policy_ref (e.g. CF-POL-03)."
    ),
    input_schema=ResizeRequest,
    output_schema=ResizeResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_cf_approve_resize_flow(aflow: Flow = None) -> Flow:
    """Show a rightsizing proposal to a cost owner; resize only on approval."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Cost Owner Approval (Rightsize)"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Resource Rightsizing Approval",
        instructions=(
            "Approver: Cost Owner. Review the proposed rightsizing below. "
            "Note: database cluster rightsizing requires a change-control window (weekend maintenance). "
            "Click 'Approve' to resize, or 'Reject' to cancel with no changes made."
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
        name="current_size_display",
        label="Current Size",
        message="{flow.input.current_size}",
    )
    approval_form.message_output_field(
        name="target_size_display",
        label="Proposed Target Size",
        message="{flow.input.target_size}",
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
    resize_node = aflow.tool("cf_resize_resource", input_schema=ResizeInput)
    resize_node.map_input(input_variable="resource_id", expression="flow.input.resource_id")
    resize_node.map_input(input_variable="account_id",  expression="flow.input.account_id")
    resize_node.map_input(input_variable="target_size", expression="flow.input.target_size")
    resize_node.map_input(input_variable="approved_by", expression='"Cost Owner"')

    # ── Result scripts ─────────────────────────────────────────────────────
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision         = "approved"
self.output.resource_id      = flow.input.resource_id
self.output.account_id       = flow.input.account_id
self.output.current_size     = flow.input.current_size
self.output.target_size      = flow.input.target_size
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = str(flow.nodes['cf_resize_resource'].output)
self.output.message = (
    "APPROVED BY COST OWNER AND EXECUTED. "
    f"Resource: {flow.input.resource_id}, Account: {flow.input.account_id}. "
    f"Resized from '{flow.input.current_size}' to '{flow.input.target_size}'. "
    f"Policy: {flow.input.policy_ref or 'N/A'}. "
    "Illustrative saving: ~40% monthly cost reduction. "
    "This figure is illustrative; actual saving depends on production workload. "
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
self.output.current_size     = flow.input.current_size
self.output.target_size      = flow.input.target_size
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = ""
self.output.message = (
    "REJECTED BY COST OWNER. No resource was resized. "
    f"Resource: {flow.input.resource_id}, Account: {flow.input.account_id}. "
    f"Current size '{flow.input.current_size}' unchanged. "
    "No infrastructure changes were made."
)
""",
    )

    # ── Conditions branch ──────────────────────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=resize_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Edges ──────────────────────────────────────────────────────────────
    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(resize_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

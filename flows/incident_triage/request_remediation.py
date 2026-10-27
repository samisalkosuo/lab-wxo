"""Remediation approval flow for the incident triage demo.

This flow encodes the mandatory human governance gate for production
remediations.  The incident triage agent calls this flow instead of
calling execute_remediation directly, so that no remediation can be
executed without explicit human approval.

Flow name (tool name visible to agents): request_remediation

Inputs the agent must supply:
  - service          : target service name (e.g. 'checkout')
  - action           : remediation action (e.g. 'rollback')
  - justification    : agent's reasoning for proposing this action
  - incident_id      : incident reference (e.g. 'INC-1001'), optional
  - runbook_ref      : runbook ID cited (e.g. 'RB-DEPLOY-01'), optional

Flow behavior:
  1. A user activity shows the proposed action and justification.
  2. The user clicks "Approve" or "Reject" (buttons on the form).
  3. Each button routes to a script inside the userflow that writes
     the decision to flow.private.decision.
  4. After the userflow exits, a conditions branch in the outer flow
     inspects flow.private.decision.
  5. Approve  → tool node calls execute_remediation → result script → END.
  6. Reject   → rejection script → END.  Nothing is executed.

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/incident_triage \\
      -f tools/incident_triage/incident_triage.py \\
      -r tools/incident_triage/requirements.txt
  orchestrate tools import -k flow -f flows/incident_triage/request_remediation.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class RemediationRequest(BaseModel):
    """Input the incident triage agent passes to the approval flow."""

    service: str = Field(
        description=(
            "Target service name. One of: checkout, payments, auth-gateway, "
            "search-service, notification-service, inventory-db."
        )
    )
    action: str = Field(
        description=(
            "Remediation action to execute on approval. One of: rollback, "
            "db_pool_resize, certificate_rotation, restart, no_action."
        )
    )
    justification: str = Field(
        description=(
            "Agent's evidence-based reasoning for proposing this action. "
            "Shown verbatim to the approver in the form."
        )
    )
    incident_id: str = Field(
        default="",
        description="Incident reference (e.g. 'INC-1001'). Optional but recommended.",
    )
    runbook_ref: str = Field(
        default="",
        description="Runbook ID cited as the basis for this action (e.g. 'RB-DEPLOY-01').",
    )


# ---------------------------------------------------------------------------
# Private schema — carries the human decision across the userflow boundary
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(
        default="pending",
        description="Human decision written by userflow scripts: 'approved' or 'rejected'.",
    )
    execution_result: str = Field(
        default="",
        description="Output of execute_remediation on approval. Empty on rejection.",
    )
    message: str = Field(
        default="",
        description="Final message for the agent, written by the result scripts.",
    )


# ---------------------------------------------------------------------------
# Schemas for the execute_remediation tool node (must match the tool's signature)
# ---------------------------------------------------------------------------
class ExecuteRemediationInput(BaseModel):
    """Arguments of the execute_remediation Python tool."""

    service: str = Field(description="Target service name.")
    action: str = Field(description="Remediation action name.")
    parameters: str = Field(default="", description="Optional JSON string of action parameters.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class RemediationResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(
        description="Human decision: 'approved' or 'rejected'."
    )
    service: str = Field(description="Target service that was acted on.")
    action: str = Field(description="Remediation action that was proposed.")
    incident_id: str = Field(description="Incident reference supplied by the agent.")
    runbook_ref: str = Field(description="Runbook reference supplied by the agent.")
    execution_result: str = Field(
        default="",
        description=(
            "JSON output of execute_remediation on approval. "
            "Empty string on rejection."
        ),
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: execution outcome. "
            "On rejection: clear statement that nothing was executed."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="request_remediation",
    display_name="Request Remediation Approval",
    description=(
        "Governance gate for production remediations. "
        "Presents the proposed action and justification to a human approver. "
        "On approval, calls execute_remediation and returns the execution result. "
        "On rejection, returns a clear 'rejected – nothing executed' result. "
        "Always use this flow instead of calling execute_remediation directly. "
        "Required inputs: service, action, justification. "
        "Optional: incident_id, runbook_ref."
    ),
    input_schema=RemediationRequest,
    output_schema=RemediationResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_request_remediation_flow(aflow: Flow = None) -> Flow:
    """Present a remediation proposal for human approval; execute only on approval."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Remediation Approval"

    # The form shows the proposed action and justification (read-only).
    # submit_button_label="Approve" makes that the primary (default Submit) button.
    # A separate "Reject" button is added via user_flow.add_button().
    approval_form = user_flow.form(
        name="approval_form",
        display_name="Remediation Approval Request",
        instructions=(
            "Review the proposed remediation below. "
            "Click 'Approve' to execute it, or 'Reject' to cancel with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,   # hide default cancel button
    )

    # Read-only display of what the agent proposed
    approval_form.message_output_field(
        name="svc_display",
        label="Target Service",
        message="{flow.input.service}",
    )
    approval_form.message_output_field(
        name="action_display",
        label="Proposed Action",
        message="{flow.input.action}",
    )
    approval_form.message_output_field(
        name="incident_display",
        label="Incident Reference",
        message="{flow.input.incident_id}",
    )
    approval_form.message_output_field(
        name="runbook_display",
        label="Runbook Reference",
        message="{flow.input.runbook_ref}",
    )
    approval_form.message_output_field(
        name="justification_display",
        label="Agent Justification",
        message="{flow.input.justification}",
    )

    # Internal scripts that record the human's decision into flow.private.
    # These live inside the userflow so they can write to flow.private before
    # the userflow exits.
    record_approved = user_flow.script(
        name="record_approved",
        script='flow.private.decision = "approved"',
    )
    record_rejected = user_flow.script(
        name="record_rejected",
        script='flow.private.decision = "rejected"',
    )

    # Add the Reject button via add_button() — this creates an additional button
    # on the form alongside the default "Approve" (submit) button.
    reject_btn = user_flow.add_button("Reject")

    # Wire userflow internal edges:
    #   START  → form
    #   form   --[Approve (default submit)]-→ record_approved → END
    #   reject_btn                          -→ record_rejected → END
    user_flow.edge(START, approval_form)
    user_flow.edge(approval_form, record_approved, button_label="Approve")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # ── Outer flow: tool node for approved path ────────────────────────────
    # Reference execute_remediation by its imported tool name (string) because
    # the function lives in a separate imported package. The input schema is
    # passed explicitly: letting the ADK resolve it from the deployed tool
    # produced a flow schema with a single untyped "data" property, and the
    # runtime then called the tool with an unexpected "data" argument
    # (TypeError, status 424). The tool returns a plain string, so no output
    # schema is forced.
    execute_node = aflow.tool(
        "execute_remediation",
        input_schema=ExecuteRemediationInput,
    )
    execute_node.map_input(input_variable="service", expression="flow.input.service")
    execute_node.map_input(input_variable="action",  expression="flow.input.action")
    # parameters is optional; pass empty string so the tool stays happy
    execute_node.map_input(input_variable="parameters", expression='""')

    # Script: compose approved result for the agent
    # The result scripts write to flow.private and the flow output is mapped
    # explicitly below. Without that mapping the runtime auto-maps the END node
    # from whichever script ran, which failed intermittently
    # ("auto_data_mapping: No available next nodes available", flow_status=failed)
    # and left the agent without the rejection/approval message.
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
flow.private.decision         = "approved"
flow.private.execution_result = str(flow.nodes['execute_remediation'].output)
flow.private.message = (
    "APPROVED AND EXECUTED. "
    f"Service: {flow.input.service}, Action: {flow.input.action}. "
    f"Incident: {flow.input.incident_id or 'N/A'}. "
    f"Runbook: {flow.input.runbook_ref or 'N/A'}. "
    f"Execution result: {flow.private.execution_result}"
)
""",
    )

    # Script: compose rejection result for the agent — nothing was executed
    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
flow.private.decision         = "rejected"
flow.private.execution_result = ""
flow.private.message = (
    "REJECTED. No remediation was executed. "
    f"Proposed action '{flow.input.action}' on service '{flow.input.service}' "
    f"was declined by the approver. "
    f"Incident: {flow.input.incident_id or 'N/A'}. "
    "No infrastructure changes were made."
)
""",
    )

    # ── Outer flow branching on the recorded decision ──────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=execute_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Outer flow edges ───────────────────────────────────────────────────
    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(execute_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    # ── Explicit flow output mapping (no LLM auto-mapping at END) ──────────
    aflow.map_output(output_variable="decision",         expression="flow.private.decision")
    aflow.map_output(output_variable="service",          expression="flow.input.service")
    aflow.map_output(output_variable="action",           expression="flow.input.action")
    aflow.map_output(output_variable="incident_id",      expression="flow.input.incident_id")
    aflow.map_output(output_variable="runbook_ref",      expression="flow.input.runbook_ref")
    aflow.map_output(output_variable="execution_result", expression="flow.private.execution_result")
    aflow.map_output(output_variable="message",          expression="flow.private.message")

    return aflow

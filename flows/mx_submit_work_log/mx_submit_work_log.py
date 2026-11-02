"""Work log approval flow for the Maintenance Field Assistant demo.

This flow is the human gate in front of the (mock) Maximo write. The field_maintenance
agent calls it instead of calling mx_write_work_log directly, so nothing is written
unless the technician approves the drafted work log.

Flow name (tool name visible to agents): mx_submit_work_log

Inputs the agent must supply:
  - assetnum          : asset number (e.g. 'PUMP-L2-03')
  - log_text          : the drafted work log text
  - wonum             : existing OPEN work order to add the log to (optional; empty = new work order)
  - followup_request  : text of a follow-up service request (optional; empty = none)
  - sop_refs          : comma-separated procedure IDs followed (optional)

Flow behavior:
  1. A user activity shows the draft to the technician.
  2. The technician clicks "Submit" or "Reject" (buttons on the form).
  3. Each button routes to a script inside the userflow that records the decision.
  4. After the userflow exits, a conditions branch inspects the decision.
  5. Submit  -> tool node calls mx_write_work_log -> result script -> END.
  6. Reject  -> rejection script -> END. Nothing is written.

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/field_maintenance \\
      -f tools/field_maintenance/field_maintenance.py \\
      -r tools/field_maintenance/requirements.txt
  orchestrate tools import -k flow -f flows/mx_submit_work_log/mx_submit_work_log.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class WorkLogRequest(BaseModel):
    """Input the field maintenance agent passes to the approval flow."""

    assetnum: str = Field(description="Asset number the work log is for, e.g. 'PUMP-L2-03'.")
    log_text: str = Field(
        description=(
            "The drafted work log text. Shown verbatim to the technician in the form."
        )
    )
    wonum: str = Field(
        default="",
        description=(
            "Existing OPEN work order number to add the log to (e.g. 'WO-11002'). "
            "Leave empty to create a new work order. Must belong to the asset."
        ),
    )
    followup_request: str = Field(
        default="",
        description=(
            "Text of a follow-up service request (for example a reliability review for a "
            "repeat failure). Leave empty if none is needed."
        ),
    )
    sop_refs: str = Field(
        default="",
        description="Comma-separated procedure IDs followed, e.g. 'SOP-PUMP-01,SOP-LOTO-01'.",
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
    write_result: str = Field(
        default="",
        description="Output of mx_write_work_log on approval. Empty on rejection.",
    )
    message: str = Field(
        default="",
        description="Final message for the agent, written by the result scripts.",
    )


# ---------------------------------------------------------------------------
# Schema for the mx_write_work_log tool node (must match the tool's signature)
# ---------------------------------------------------------------------------
class WriteWorkLogInput(BaseModel):
    """Arguments of the mx_write_work_log Python tool."""

    assetnum: str = Field(description="Asset number.")
    log_text: str = Field(description="Work log text.")
    wonum: str = Field(default="", description="Existing open work order number, or empty.")
    followup_request: str = Field(default="", description="Follow-up service request text, or empty.")
    sop_refs: str = Field(default="", description="Comma-separated procedure IDs.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class WorkLogResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Technician decision: 'approved' or 'rejected'.")
    assetnum: str = Field(description="Asset the work log was drafted for.")
    wonum: str = Field(description="Work order number supplied by the agent (empty if a new one was requested).")
    write_result: str = Field(
        default="",
        description="JSON output of mx_write_work_log on approval. Empty string on rejection.",
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: what was written. On rejection: clear statement that nothing was written."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="mx_submit_work_log",
    display_name="Submit Work Log for Approval",
    description=(
        "Human approval gate for writing a work log to the maintenance system (Maximo). "
        "Shows the drafted work log to the technician. On Submit, calls mx_write_work_log "
        "and returns the result. On Reject, returns a clear 'nothing was written' result. "
        "Always use this flow instead of calling mx_write_work_log directly. "
        "Required inputs: assetnum, log_text. "
        "Optional: wonum, followup_request, sop_refs."
    ),
    input_schema=WorkLogRequest,
    output_schema=WorkLogResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_mx_submit_work_log_flow(aflow: Flow = None) -> Flow:
    """Present a drafted work log for approval; write only on Submit."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Work Log Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Work Log Approval Request",
        instructions=(
            "Review the drafted work log below. "
            "Click 'Submit' to write it to the maintenance system, or 'Reject' to discard it with nothing written."
        ),
        submit_button_label="Submit",
        cancel_button_label=None,   # hide default cancel button
    )

    # Field labels are not rendered in the chat form (observed in the browser), so each
    # message carries its own label text.
    approval_form.message_output_field(
        name="asset_display",
        label="Asset",
        message="Asset: {flow.input.assetnum}",
    )
    approval_form.message_output_field(
        name="wonum_display",
        label="Work Order",
        message="Work order (empty = new work order): {flow.input.wonum}",
    )
    approval_form.message_output_field(
        name="sop_display",
        label="Procedures Followed",
        message="Procedures followed: {flow.input.sop_refs}",
    )
    approval_form.message_output_field(
        name="log_display",
        label="Drafted Work Log",
        message="Drafted work log: {flow.input.log_text}",
    )
    approval_form.message_output_field(
        name="followup_display",
        label="Follow-up Service Request",
        message="Follow-up service request (empty = none): {flow.input.followup_request}",
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
    user_flow.edge(approval_form, record_approved, button_label="Submit")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # ── Outer flow: tool node for the approved path ────────────────────────
    # Input schema passed explicitly (see flows/incident_triage/request_remediation.py:
    # resolving it from the deployed tool produced a single untyped "data" property).
    write_node = aflow.tool(
        "mx_write_work_log",
        input_schema=WriteWorkLogInput,
    )
    write_node.map_input(input_variable="assetnum", expression="flow.input.assetnum")
    write_node.map_input(input_variable="log_text", expression="flow.input.log_text")
    write_node.map_input(input_variable="wonum", expression="flow.input.wonum")
    write_node.map_input(input_variable="followup_request", expression="flow.input.followup_request")
    write_node.map_input(input_variable="sop_refs", expression="flow.input.sop_refs")

    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Submitted Result",
        script="""
flow.private.decision = "approved"
# Read the write tool's output. A browser run showed that flow.nodes['<tool>'].output alone
# gave "None" here, while this fallback chain returned the real tool JSON. Which of the
# fallback paths matched was not recorded. If no path returns a value, the message names
# the paths that came back empty.
paths = []
write_text = ""
try:
    v1 = flow.nodes['mx_write_work_log'].output
    paths.append("nodes[]=" + ("empty" if v1 is None or str(v1) == "None" else "ok"))
    if v1 is not None and str(v1) != "None":
        write_text = str(v1)
except Exception:
    paths.append("nodes[]=error")
if not write_text:
    try:
        v2 = flow['mx_write_work_log'].output
        paths.append("flow[]=" + ("empty" if v2 is None or str(v2) == "None" else "ok"))
        if v2 is not None and str(v2) != "None":
            write_text = str(v2)
    except Exception:
        paths.append("flow[]=error")
if not write_text:
    try:
        v3 = flow.mx_write_work_log.output
        paths.append("flow.attr=" + ("empty" if v3 is None or str(v3) == "None" else "ok"))
        if v3 is not None and str(v3) != "None":
            write_text = str(v3)
    except Exception:
        paths.append("flow.attr=error")
if not write_text:
    write_text = "NO RESULT FOUND (" + ", ".join(paths) + ")"
flow.private.write_result = write_text
flow.private.message = (
    "SUBMITTED. "
    f"Asset: {flow.input.assetnum}. "
    f"Maximo write result (mock): {write_text}"
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
flow.private.decision     = "rejected"
flow.private.write_result = ""
flow.private.message = (
    "REJECTED. No work log was written. "
    f"The draft for asset {flow.input.assetnum} was discarded by the technician. "
    "Nothing was changed in the maintenance system."
)
""",
    )

    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=write_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(write_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    # Explicit flow output mapping (no LLM auto-mapping at END)
    aflow.map_output(output_variable="decision",     expression="flow.private.decision")
    aflow.map_output(output_variable="assetnum",     expression="flow.input.assetnum")
    aflow.map_output(output_variable="wonum",        expression="flow.input.wonum")
    aflow.map_output(output_variable="write_result", expression="flow.private.write_result")
    aflow.map_output(output_variable="message",      expression="flow.private.message")

    return aflow

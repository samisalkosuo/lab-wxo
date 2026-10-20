"""Standard provisioning approval flow for the HR Onboarding demo.

The hr_onboarding agent calls this flow instead of calling hr_provision_access itself.
The flow shows the proposal to an HR Manager. Only on Approve does it call the internal
write tool hr_provision_access. This flow is for departments WITHOUT a compliance gate.
Finance hires use hr_request_compliance_provisioning instead.

Flow name (tool name visible to agents): hr_request_provisioning

The flow, not the agent, fixes approval_path to 'standard'. The write tool re-checks the
hire, role, department, systems and compliance requirement in code, so an agent that picks
this flow for a Finance hire gets a refusal from the tool (COMPLIANCE_REQUIRED) even after
the HR Manager approved. The result message then says so; access is not granted.

Behaviour:
  1. A script turns the systems list into text for the form.
  2. A user activity shows the proposal to the HR Manager.
  3. The approver clicks Approve or Reject.
  4. Approve -> tool node calls hr_provision_access -> result script -> END.
  5. Reject  -> rejection script -> END. Nothing is provisioned.

The approver is recorded as the role label "HR Manager"; the form does not capture an
individual identity.

Import prerequisites (the tool must exist before this flow is imported):
  orchestrate tools import -k python -p tools/hr_onboarding \\
      -f tools/hr_onboarding/hr_onboarding.py \\
      -r tools/hr_onboarding/requirements.txt
  orchestrate tools import -k flow -f flows/hr_onboarding/hr_request_provisioning.py

Not tested: the form, the buttons, the list-to-text script and the tool-node input mapping
have not been run against an instance. They follow flows/incident_triage/request_remediation.py
and flows/customer_returns/process_return.py.
"""

from typing import List

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ProvisioningRequest(BaseModel):
    """Input the hr_onboarding agent passes to the approval flow."""

    hire_id: str = Field(description="Exactly one hire id such as 'H-1001'. Never a team or a list.")
    hire_name: str = Field(description="The hire's name, for the approver to read.")
    role: str = Field(description="The hire's role id from the hire record, e.g. 'software_engineer'.")
    department: str = Field(description="The hire's department id from the hire record, e.g. 'engineering'.")
    systems: List[str] = Field(
        description=(
            "System ids to grant, from hr_get_role_access 'allowed' only. "
            "One or more of: email, chat, source_code, production_access, finance_ledger, vpn."
        )
    )
    equipment_choice: str = Field(
        default="",
        description=(
            "Equipment the coordinator chose when the record had none: "
            "standard_laptop, developer_laptop or no_equipment. Empty if the record already has one."
        ),
    )
    policy_ref: str = Field(
        default="",
        description="Policy document ID cited as the basis, e.g. 'HR-POL-01'.",
    )
    justification: str = Field(
        description="The agent's evidence-based reasoning. Shown verbatim to the approver."
    )


# ---------------------------------------------------------------------------
# Private schema - carries the human decision across the userflow boundary
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(default="pending", description="'approved' or 'rejected'.")
    systems_text: str = Field(default="", description="Systems list joined for display.")


# ---------------------------------------------------------------------------
# Schema for the hr_provision_access tool node (must match the tool's signature)
# ---------------------------------------------------------------------------
class ProvisionAccessInput(BaseModel):
    """Arguments of the hr_provision_access Python tool."""

    hire_id: str = Field(description="Exactly one hire id.")
    role: str = Field(description="Role; must match the hire record.")
    department: str = Field(description="Department; must match the hire record.")
    systems: List[str] = Field(description="System ids to grant.")
    approval_path: str = Field(description="'standard' or 'compliance'.")
    hr_manager_approver: str = Field(description="HR Manager approval record.")
    compliance_approver: str = Field(default="", description="Compliance Reviewer approval record.")
    equipment_choice: str = Field(default="", description="Equipment choice supplied by the coordinator.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ProvisioningResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Human decision: 'approved' or 'rejected'.")
    hire_id: str = Field(description="Hire the request was for.")
    systems: str = Field(description="Systems that were requested, as text.")
    approval_path: str = Field(description="Always 'standard' for this flow.")
    policy_ref: str = Field(description="Policy document cited by the agent.")
    provisioned: bool = Field(
        description="True only if the human approved AND the provisioning tool reported success."
    )
    execution_result: str = Field(
        default="",
        description="Output of hr_provision_access after approval. Empty on rejection.",
    )
    message: str = Field(
        description="Human-readable summary the agent should report verbatim."
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="hr_request_provisioning",
    display_name="Request Provisioning Approval (standard)",
    description=(
        "Governance gate for granting system access to ONE new hire when the department does "
        "NOT require compliance sign-off (check hr_get_department_config first). "
        "Shows the proposal to an HR Manager. On approval, calls hr_provision_access and returns "
        "its result. On rejection, returns 'rejected - nothing provisioned'. "
        "For a compliance-gated department such as Finance use hr_request_compliance_provisioning "
        "instead. Never use this flow for a team or several hires. "
        "Required inputs: hire_id, hire_name, role, department, systems, justification. "
        "Optional: equipment_choice, policy_ref."
    ),
    input_schema=ProvisioningRequest,
    output_schema=ProvisioningResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_hr_request_provisioning_flow(aflow: Flow = None) -> Flow:
    """Show a provisioning proposal to an HR Manager; provision only on approval."""

    # -- Prepare display text -------------------------------------------------
    prepare = aflow.script(
        name="prepare_display",
        display_name="Prepare Display Text",
        script='flow.private.systems_text = ", ".join(flow.input.systems)',
    )

    # -- User activity: HR Manager approval -----------------------------------
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "HR Manager Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Provisioning Approval Request",
        instructions=(
            "Approver: HR Manager. Review the proposed access below. "
            "Click 'Approve' to grant it, or 'Reject' to cancel with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )
    approval_form.message_output_field(
        name="hire_display", label="Hire ID", message="{flow.input.hire_id}"
    )
    approval_form.message_output_field(
        name="name_display", label="Hire name (as stated by the agent)", message="{flow.input.hire_name}"
    )
    approval_form.message_output_field(
        name="role_display", label="Role", message="{flow.input.role}"
    )
    approval_form.message_output_field(
        name="department_display", label="Department", message="{flow.input.department}"
    )
    approval_form.message_output_field(
        name="systems_display", label="Systems to grant", message="{flow.private.systems_text}"
    )
    approval_form.message_output_field(
        name="equipment_display", label="Equipment choice", message="{flow.input.equipment_choice}"
    )
    approval_form.message_output_field(
        name="policy_display", label="Policy reference", message="{flow.input.policy_ref}"
    )
    approval_form.message_output_field(
        name="justification_display", label="Agent justification", message="{flow.input.justification}"
    )

    record_approved = user_flow.script(
        name="record_approved", script='flow.private.decision = "approved"'
    )
    record_rejected = user_flow.script(
        name="record_rejected", script='flow.private.decision = "rejected"'
    )
    reject_btn = user_flow.add_button("Reject")

    user_flow.edge(START, approval_form)
    user_flow.edge(approval_form, record_approved, button_label="Approve")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # -- Tool node: hr_provision_access ---------------------------------------
    # The flow, not the agent, sets approval_path and the approver record.
    provision_node = aflow.tool("hr_provision_access", input_schema=ProvisionAccessInput)
    provision_node.map_input(input_variable="hire_id", expression="flow.input.hire_id")
    provision_node.map_input(input_variable="role", expression="flow.input.role")
    provision_node.map_input(input_variable="department", expression="flow.input.department")
    provision_node.map_input(input_variable="systems", expression="flow.input.systems")
    provision_node.map_input(input_variable="approval_path", expression='"standard"')
    provision_node.map_input(input_variable="hr_manager_approver", expression='"HR Manager"')
    provision_node.map_input(input_variable="compliance_approver", expression='""')
    provision_node.map_input(input_variable="equipment_choice", expression="flow.input.equipment_choice")

    # -- Result scripts -------------------------------------------------------
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision         = "approved"
self.output.hire_id          = flow.input.hire_id
self.output.systems          = flow.private.systems_text
self.output.approval_path    = "standard"
self.output.policy_ref       = flow.input.policy_ref
tool_out = None
try:
    tool_out = flow['hr_provision_access'].output
except Exception:
    pass
if not tool_out:
    try:
        tool_out = flow.nodes['hr_provision_access'].output
    except Exception:
        pass
self.output.execution_result = str(tool_out) if tool_out else "NO OUTPUT RETURNED BY THE TOOL NODE"
self.output.provisioned      = ("success" in self.output.execution_result) and ("error_code" not in self.output.execution_result)
if self.output.provisioned:
    self.output.message = (
        "APPROVED BY HR MANAGER AND PROVISIONED. "
        f"Hire: {flow.input.hire_id}. Systems: {flow.private.systems_text}. "
        f"Tool result: {self.output.execution_result}"
    )
elif not tool_out:
    diag = []
    try:
        diag.append("node_class=" + flow.nodes['hr_provision_access'].__class__.__name__)
    except Exception as e:
        diag.append("node_err=" + str(e)[:120])
    try:
        diag.append("node=" + str(flow.nodes['hr_provision_access'])[:300])
    except Exception as e:
        diag.append("node_str_err=" + str(e)[:120])
    try:
        diag.append("output_repr=" + repr(flow.nodes['hr_provision_access'].output)[:300])
    except Exception as e:
        diag.append("output_err=" + str(e)[:120])
    try:
        diag.append("alt_output=" + repr(flow['hr_provision_access'].output)[:300])
    except Exception as e:
        diag.append("alt_err=" + str(e)[:120])
    self.output.message = (
        "APPROVED BY HR MANAGER, BUT THE FLOW RECEIVED NO RESULT FROM THE PROVISIONING TOOL. "
        "PROVISIONING IS UNCONFIRMED; DO NOT REPORT ACCESS AS GRANTED. "
        f"Hire: {flow.input.hire_id}. Systems: {flow.private.systems_text}. "
        "DIAGNOSTIC (temporary): " + " | ".join(diag)
    )
else:
    self.output.message = (
        "APPROVED BY HR MANAGER, BUT THE PROVISIONING TOOL REFUSED. NO ACCESS WAS GRANTED. "
        f"Hire: {flow.input.hire_id}. Systems: {flow.private.systems_text}. "
        f"Tool result: {self.output.execution_result}"
    )
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
self.output.decision         = "rejected"
self.output.hire_id          = flow.input.hire_id
self.output.systems          = flow.private.systems_text
self.output.approval_path    = "standard"
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = ""
self.output.provisioned      = False
self.output.message = (
    "REJECTED BY HR MANAGER. No access was provisioned. "
    f"Hire: {flow.input.hire_id}. Requested systems: {flow.private.systems_text}. "
    "No changes have been made."
)
""",
    )

    # -- Branch on the recorded decision --------------------------------------
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=provision_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # -- Edges ----------------------------------------------------------------
    aflow.edge(START, prepare)
    aflow.edge(prepare, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(provision_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

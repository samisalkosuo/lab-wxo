"""Compliance-gated provisioning approval flow for the HR Onboarding demo.

The hr_onboarding agent calls this flow for hires in a department that requires compliance
sign-off (Finance; see hr_get_department_config). Two humans must approve, in order:
the HR Manager first, then the Compliance Reviewer. Only when both approve does the flow
call the internal write tool hr_provision_access.

Flow name (tool name visible to agents): hr_request_compliance_provisioning

Design: two separate user activities (one form each, each with its own Approve and Reject
buttons) joined by a conditions branch, instead of two forms in one user flow. If the HR
Manager rejects, the Compliance Reviewer is never asked.

The flow, not the agent, fixes approval_path to 'compliance'. The write tool re-checks the
hire, role, department, systems and the compliance requirement in code. If an agent picks
this flow for a department that needs no compliance sign-off, the tool still succeeds and
adds a note to its message (user decision).

Behaviour:
  1. A script turns the systems list into text for the forms.
  2. User activity 1: HR Manager. Reject -> rejection script -> END.
  3. User activity 2: Compliance Reviewer. Reject -> rejection script -> END.
  4. Both approved -> tool node calls hr_provision_access -> result script -> END.

Approvers are recorded as the role labels "HR Manager" and "Compliance Reviewer"; the
forms do not capture an individual identity.

Import prerequisites (the tool must exist before this flow is imported):
  orchestrate tools import -k python -p tools/hr_onboarding \\
      -f tools/hr_onboarding/hr_onboarding.py \\
      -r tools/hr_onboarding/requirements.txt
  orchestrate tools import -k flow -f flows/hr_onboarding/hr_request_compliance_provisioning.py

Not tested: the forms, the buttons, the branch between the two user activities, the
list-to-text script and the tool-node input mapping have not been run against an instance.
They follow flows/incident_triage/request_remediation.py and
flows/customer_returns/process_return.py. Two sequential approval forms in one flow are
new in this repo and are the most likely place for a problem.
"""

from typing import List

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema (same fields as hr_request_provisioning)
# ---------------------------------------------------------------------------
class ProvisioningRequest(BaseModel):
    """Input the hr_onboarding agent passes to the approval flow."""

    hire_id: str = Field(description="Exactly one hire id such as 'H-1003'. Never a team or a list.")
    hire_name: str = Field(description="The hire's name, for the approvers to read.")
    role: str = Field(description="The hire's role id from the hire record, e.g. 'finance_analyst'.")
    department: str = Field(description="The hire's department id from the hire record, e.g. 'finance'.")
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
        description="Policy document ID cited as the basis, e.g. 'HR-POL-03'.",
    )
    justification: str = Field(
        description="The agent's evidence-based reasoning. Shown verbatim to both approvers."
    )


# ---------------------------------------------------------------------------
# Private schema - carries the two human decisions across the userflow boundaries
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    hr_decision: str = Field(default="pending", description="HR Manager decision: 'approved' or 'rejected'.")
    compliance_decision: str = Field(
        default="pending", description="Compliance Reviewer decision: 'approved' or 'rejected'."
    )
    systems_text: str = Field(default="", description="Systems list joined for display.")
    decision: str = Field(default="pending", description="Final flow decision written by result scripts.")
    execution_result: str = Field(default="", description="Output of hr_provision_access after approval.")
    provisioned: bool = Field(default=False, description="True when provisioning tool reported success.")
    message: str = Field(default="", description="Final message for the agent, written by result scripts.")


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

    decision: str = Field(
        description=(
            "'approved' (both approved), 'rejected_by_hr_manager' or 'rejected_by_compliance_reviewer'."
        )
    )
    hire_id: str = Field(description="Hire the request was for.")
    systems: str = Field(description="Systems that were requested, as text.")
    approval_path: str = Field(description="Always 'compliance' for this flow.")
    policy_ref: str = Field(description="Policy document cited by the agent.")
    provisioned: bool = Field(
        description="True only if both humans approved AND the provisioning tool reported success."
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
    name="hr_request_compliance_provisioning",
    display_name="Request Provisioning Approval (compliance-gated)",
    description=(
        "Governance gate for granting system access to ONE new hire in a department that requires "
        "compliance sign-off, such as Finance (check hr_get_department_config first: "
        "compliance_signoff_required must be true). Asks the HR Manager first, then the Compliance "
        "Reviewer. Only if both approve does it call hr_provision_access and return its result. "
        "If either rejects, nothing is provisioned. For departments without a compliance gate use "
        "hr_request_provisioning. Never use this flow for a team or several hires. "
        "Required inputs: hire_id, hire_name, role, department, systems, justification. "
        "Optional: equipment_choice, policy_ref."
    ),
    input_schema=ProvisioningRequest,
    output_schema=ProvisioningResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_hr_request_compliance_provisioning_flow(aflow: Flow = None) -> Flow:
    """Ask the HR Manager, then the Compliance Reviewer; provision only if both approve."""

    # -- Prepare display text -------------------------------------------------
    prepare = aflow.script(
        name="prepare_display",
        display_name="Prepare Display Text",
        script='flow.private.systems_text = ", ".join(flow.input.systems)',
    )

    # -- User activity 1: HR Manager -----------------------------------------
    hr_flow = aflow.userflow()
    hr_flow.spec.display_name = "HR Manager Approval"

    hr_form = hr_flow.form(
        name="hr_approval_form",
        display_name="Provisioning Approval Request - Step 1 of 2",
        instructions=(
            "Approver: HR Manager (step 1 of 2). This hire is in a compliance-gated department, "
            "so a Compliance Reviewer must also approve after you. "
            "Click 'Approve' to pass the request on, or 'Reject' to cancel with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )
    hr_form.message_output_field(name="hire_display", label="Hire ID", message="{flow.input.hire_id}")
    hr_form.message_output_field(
        name="name_display", label="Hire name (as stated by the agent)", message="{flow.input.hire_name}"
    )
    hr_form.message_output_field(name="role_display", label="Role", message="{flow.input.role}")
    hr_form.message_output_field(
        name="department_display", label="Department", message="{flow.input.department}"
    )
    hr_form.message_output_field(
        name="systems_display", label="Systems to grant", message="{flow.private.systems_text}"
    )
    hr_form.message_output_field(
        name="equipment_display", label="Equipment choice", message="{flow.input.equipment_choice}"
    )
    hr_form.message_output_field(
        name="policy_display", label="Policy reference", message="{flow.input.policy_ref}"
    )
    hr_form.message_output_field(
        name="justification_display", label="Agent justification", message="{flow.input.justification}"
    )

    hr_approved = hr_flow.script(name="record_hr_approved", script='flow.private.hr_decision = "approved"')
    hr_rejected = hr_flow.script(name="record_hr_rejected", script='flow.private.hr_decision = "rejected"')
    hr_reject_btn = hr_flow.add_button("Reject")

    hr_flow.edge(START, hr_form)
    hr_flow.edge(hr_form, hr_approved, button_label="Approve")
    hr_flow.edge(hr_approved, END)
    hr_flow.edge(hr_reject_btn, hr_rejected)
    hr_flow.edge(hr_rejected, END)

    # -- User activity 2: Compliance Reviewer ---------------------------------
    comp_flow = aflow.userflow()
    comp_flow.spec.display_name = "Compliance Reviewer Approval"

    comp_form = comp_flow.form(
        name="compliance_approval_form",
        display_name="Provisioning Approval Request - Step 2 of 2",
        instructions=(
            "Approver: Compliance Reviewer (step 2 of 2). The HR Manager has approved. "
            "Click 'Approve' to grant the access, or 'Reject' to cancel with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )
    comp_form.message_output_field(name="hire_display", label="Hire ID", message="{flow.input.hire_id}")
    comp_form.message_output_field(
        name="name_display", label="Hire name (as stated by the agent)", message="{flow.input.hire_name}"
    )
    comp_form.message_output_field(name="role_display", label="Role", message="{flow.input.role}")
    comp_form.message_output_field(
        name="department_display", label="Department", message="{flow.input.department}"
    )
    comp_form.message_output_field(
        name="systems_display", label="Systems to grant", message="{flow.private.systems_text}"
    )
    comp_form.message_output_field(
        name="hr_status_display", label="HR Manager decision", message="{flow.private.hr_decision}"
    )
    comp_form.message_output_field(
        name="policy_display", label="Policy reference", message="{flow.input.policy_ref}"
    )
    comp_form.message_output_field(
        name="justification_display", label="Agent justification", message="{flow.input.justification}"
    )

    comp_approved = comp_flow.script(
        name="record_compliance_approved", script='flow.private.compliance_decision = "approved"'
    )
    comp_rejected = comp_flow.script(
        name="record_compliance_rejected", script='flow.private.compliance_decision = "rejected"'
    )
    comp_reject_btn = comp_flow.add_button("Reject")

    comp_flow.edge(START, comp_form)
    comp_flow.edge(comp_form, comp_approved, button_label="Approve")
    comp_flow.edge(comp_approved, END)
    comp_flow.edge(comp_reject_btn, comp_rejected)
    comp_flow.edge(comp_rejected, END)

    # -- Tool node: hr_provision_access ---------------------------------------
    # The flow, not the agent, sets approval_path and the approver records.
    provision_node = aflow.tool("hr_provision_access", input_schema=ProvisionAccessInput)
    provision_node.map_input(input_variable="hire_id", expression="flow.input.hire_id")
    provision_node.map_input(input_variable="role", expression="flow.input.role")
    provision_node.map_input(input_variable="department", expression="flow.input.department")
    provision_node.map_input(input_variable="systems", expression="flow.input.systems")
    provision_node.map_input(input_variable="approval_path", expression='"compliance"')
    provision_node.map_input(input_variable="hr_manager_approver", expression='"HR Manager"')
    provision_node.map_input(input_variable="compliance_approver", expression='"Compliance Reviewer"')
    provision_node.map_input(input_variable="equipment_choice", expression="flow.input.equipment_choice")

    # -- Result scripts -------------------------------------------------------
    # Write to flow.private (not self.output) so that aflow.map_output() below
    # can map private -> output at END. Without explicit map_output the runtime
    # uses auto-mapping which fails intermittently when multiple END paths exist
    # (same issue fixed in flows/incident_triage/request_remediation.py).
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
flow.private.decision         = "approved"
flow.private.execution_result = str(flow.nodes['hr_provision_access'].output)
flow.private.provisioned      = True
flow.private.message = (
    "APPROVED BY HR MANAGER AND COMPLIANCE REVIEWER, AND PROVISIONED. "
    f"Hire: {flow.input.hire_id}. Systems: {flow.private.systems_text}. "
    f"Tool result: {flow.private.execution_result}"
)
""",
    )

    rejected_by_hr = aflow.script(
        name="rejected_by_hr_result",
        display_name="Format Rejected by HR Manager",
        script="""
flow.private.decision         = "rejected_by_hr_manager"
flow.private.execution_result = ""
flow.private.provisioned      = False
flow.private.message = (
    "REJECTED BY HR MANAGER. The Compliance Reviewer was not asked. No access was provisioned. "
    f"Hire: {flow.input.hire_id}. Requested systems: {flow.private.systems_text}. "
    "No changes have been made."
)
""",
    )

    rejected_by_compliance = aflow.script(
        name="rejected_by_compliance_result",
        display_name="Format Rejected by Compliance Reviewer",
        script="""
flow.private.decision         = "rejected_by_compliance_reviewer"
flow.private.execution_result = ""
flow.private.provisioned      = False
flow.private.message = (
    "REJECTED BY COMPLIANCE REVIEWER. The HR Manager had approved, but no access was provisioned. "
    f"Hire: {flow.input.hire_id}. Requested systems: {flow.private.systems_text}. "
    "No changes have been made."
)
""",
    )

    # -- Branches -------------------------------------------------------------
    hr_branch: Branch = aflow.conditions()
    hr_branch.condition(
        expression="flow.private.hr_decision == 'approved'",
        to_node=comp_flow,
    ).condition(
        default=True,
        to_node=rejected_by_hr,
    )

    comp_branch: Branch = aflow.conditions()
    comp_branch.condition(
        expression="flow.private.compliance_decision == 'approved'",
        to_node=provision_node,
    ).condition(
        default=True,
        to_node=rejected_by_compliance,
    )

    # -- Edges ----------------------------------------------------------------
    aflow.edge(START, prepare)
    aflow.edge(prepare, hr_flow)
    aflow.edge(hr_flow, hr_branch)
    aflow.edge(comp_flow, comp_branch)
    aflow.edge(provision_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_by_hr, END)
    aflow.edge(rejected_by_compliance, END)

    # -- Explicit output mapping (avoids intermittent auto_data_mapping failures) --
    aflow.map_output(output_variable="decision",          expression="flow.private.decision")
    aflow.map_output(output_variable="hire_id",           expression="flow.input.hire_id")
    aflow.map_output(output_variable="systems",           expression="flow.private.systems_text")
    aflow.map_output(output_variable="approval_path",     expression='"compliance"')
    aflow.map_output(output_variable="policy_ref",        expression="flow.input.policy_ref")
    aflow.map_output(output_variable="provisioned",       expression="flow.private.provisioned")
    aflow.map_output(output_variable="execution_result",  expression="flow.private.execution_result")
    aflow.map_output(output_variable="message",           expression="flow.private.message")

    return aflow

"""Income determination approval flow for the YEL income assessment demo.

This flow encodes the mandatory human governance gate for issuing a formal
statutory YEL income determination (valituskelpoinen päätös). The YEL income
assessment agent calls this flow instead of calling yel_issue_decision_record
directly, so that no legally binding decision can be issued without explicit
underwriter sign-off.

Flow name (tool name visible to agents): yel_issue_decision

Inputs the agent must supply:
  - entrepreneur_id         : case reference (e.g. 'ENT-801')
  - proposed_income_eur     : agent-recommended YEL income in EUR/yr
  - justification           : agent's evidence-based reasoning
  - policy_ref              : primary policy document cited (e.g. 'YEL-POL-02')
  - underwriter_id          : underwriter identifier (e.g. 'UW-42'), optional

Flow behaviour:
  1. A user activity shows the proposed income, justification, and policy ref.
  2. The underwriter fills in the final_income field (pre-populated with the proposal)
     and selects one of three actions:
       - Confirm Proposed Income  → decision_type = 'CONFIRM'
       - Adjust & Issue           → decision_type = 'ADJUST'
       - Escalate to Appeals      → decision_type = 'ESCALATE'
  3. The chosen button is routed to a script inside the userflow that records the
     decision and final income into flow.private.
  4. After the userflow exits, a conditions branch in the outer flow inspects
     flow.private.decision_type.
  5. CONFIRM / ADJUST  → tool node calls yel_issue_decision_record → result script → END.
  6. ESCALATE          → escalation script → END.  No income change is issued.

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/yel_income \\
      -f tools/yel_income/yel_income.py \\
      -r tools/yel_income/requirements.txt
  orchestrate tools import -k flow -f flows/yel_income/issue_income_decision.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class IncomeDecisionRequest(BaseModel):
    """Input the YEL income assessment agent passes to the approval flow."""

    entrepreneur_id: str = Field(
        description=(
            "Entrepreneur case identifier (e.g. 'ENT-801'). "
            "Must match a record in the YEL case system."
        )
    )
    proposed_income_eur: int = Field(
        description=(
            "Agent-recommended YEL confirmed work income in EUR per year, "
            "after applying the statutory transition cap and sector benchmark analysis. "
            "Round to the nearest whole EUR."
        )
    )
    justification: str = Field(
        description=(
            "Agent's evidence-based reasoning for the proposed income level. "
            "Includes sector benchmark, hours adjustment, transition cap logic, "
            "and any entrepreneur-submitted evidence. Shown verbatim to the underwriter."
        )
    )
    policy_ref: str = Field(
        default="YEL-POL-02",
        description="Primary policy document ID cited as the basis for the proposal (e.g. 'YEL-POL-02').",
    )
    underwriter_id: str = Field(
        default="UW-01",
        description="Identifier of the underwriter authorising the decision (e.g. 'UW-42').",
    )


# ---------------------------------------------------------------------------
# Private schema — carries the underwriter's decision across the userflow boundary
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision_type: str = Field(
        default="pending",
        description="Underwriter's action: 'CONFIRM', 'ADJUST', or 'ESCALATE'.",
    )
    final_income_eur: int = Field(
        default=0,
        description="Final income value confirmed by the underwriter (may equal or differ from proposed).",
    )


# ---------------------------------------------------------------------------
# Schemas for the yel_issue_decision_record tool node
# ---------------------------------------------------------------------------
class IssueDecisionInput(BaseModel):
    """Arguments of the yel_issue_decision_record Python tool."""

    entrepreneur_id: str = Field(description="Entrepreneur case identifier.")
    confirmed_income_eur: int = Field(description="Final confirmed YEL work income in EUR/yr.")
    underwriter_id: str = Field(description="Identifier of the authorising underwriter.")
    decision_type: str = Field(description="Decision type: 'CONFIRM', 'ADJUST', or 'ESCALATE'.")
    justification: str = Field(description="Underwriter's written justification for the decision.")
    policy_ref: str = Field(default="", description="Primary policy document cited (e.g. 'YEL-POL-02').")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class IncomeDecisionResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision_type: str = Field(
        description="Underwriter's action: 'CONFIRM', 'ADJUST', or 'ESCALATE'."
    )
    entrepreneur_id: str = Field(description="Entrepreneur case identifier.")
    final_income_eur: int = Field(description="Final confirmed YEL income in EUR/yr (0 if escalated).")
    policy_ref: str = Field(description="Policy document cited.")
    issue_result: str = Field(
        default="",
        description=(
            "JSON output of yel_issue_decision_record on CONFIRM/ADJUST. "
            "Empty string on ESCALATE."
        ),
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On CONFIRM/ADJUST: the decision record confirmation. "
            "On ESCALATE: clear statement that no income change was issued."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="yel_issue_decision",
    display_name="Issue YEL Income Determination",
    description=(
        "Governance gate for statutory YEL income determinations. "
        "Presents the proposed confirmed work income and assessment reasoning to the "
        "underwriter for review. The underwriter may confirm the proposal, adjust the "
        "income level, or escalate the case to appeals (TELK). "
        "On CONFIRM or ADJUST, calls yel_issue_decision_record and returns the "
        "formal decision record. On ESCALATE, logs the case and returns without "
        "issuing an income change. "
        "Always use this flow instead of calling yel_issue_decision_record directly. "
        "Required inputs: entrepreneur_id, proposed_income_eur, justification. "
        "Optional: policy_ref, underwriter_id."
    ),
    input_schema=IncomeDecisionRequest,
    output_schema=IncomeDecisionResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_yel_issue_decision_flow(aflow: Flow = None) -> Flow:
    """Present an income determination proposal for underwriter sign-off."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "YEL Income Determination Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="YEL Confirmed Work Income — Underwriter Review",
        instructions=(
            "Review the proposed YEL confirmed work income below. "
            "You may confirm the proposal, adjust the income to a different amount, "
            "or escalate to TELK appeals review. "
            "All three actions create a formal case record."
        ),
        submit_button_label="Confirm Proposed Income",
        cancel_button_label=None,
    )

    # Read-only display fields
    approval_form.message_output_field(
        name="ent_display",
        label="Entrepreneur ID",
        message="{flow.input.entrepreneur_id}",
    )
    approval_form.message_output_field(
        name="proposed_display",
        label="Proposed YEL Income (EUR/yr)",
        message="{flow.input.proposed_income_eur}",
    )
    approval_form.message_output_field(
        name="policy_display",
        label="Policy Reference",
        message="{flow.input.policy_ref}",
    )
    approval_form.message_output_field(
        name="justification_display",
        label="Assessment Reasoning",
        message="{flow.input.justification}",
    )

    # Editable income field — underwriter types the confirmed income here.
    # Label shows the proposed figure so they know the starting point.
    approval_form.number_input_field(
        name="final_income_input",
        label="Final Confirmed Income (EUR/yr) — proposed: {flow.input.proposed_income_eur}",
    )

    # Internal scripts recording the decision into flow.private.
    # If the underwriter leaves the field empty (value == 0), fall back to
    # the agent-proposed income so the determination is never recorded as 0.
    record_confirmed = user_flow.script(
        name="record_confirmed",
        script=(
            'flow.private.decision_type = "CONFIRM"\n'
            "entered = flow.nodes['approval_form'].output.final_income_input\n"
            "flow.private.final_income_eur = entered if entered else flow.input.proposed_income_eur"
        ),
    )
    record_adjusted = user_flow.script(
        name="record_adjusted",
        script=(
            'flow.private.decision_type = "ADJUST"\n'
            "entered = flow.nodes['approval_form'].output.final_income_input\n"
            "flow.private.final_income_eur = entered if entered else flow.input.proposed_income_eur"
        ),
    )
    record_escalated = user_flow.script(
        name="record_escalated",
        script=(
            'flow.private.decision_type = "ESCALATE"\n'
            "flow.private.final_income_eur = 0"
        ),
    )

    # Additional buttons
    adjust_btn = user_flow.add_button("Adjust & Issue")
    escalate_btn = user_flow.add_button("Escalate to Appeals")

    # Userflow internal edges
    user_flow.edge(START, approval_form)
    user_flow.edge(approval_form, record_confirmed, button_label="Confirm Proposed Income")
    user_flow.edge(record_confirmed, END)
    user_flow.edge(adjust_btn, record_adjusted)
    user_flow.edge(record_adjusted, END)
    user_flow.edge(escalate_btn, record_escalated)
    user_flow.edge(record_escalated, END)

    # ── Outer flow: tool node for CONFIRM / ADJUST path ────────────────────
    issue_node = aflow.tool(
        "yel_issue_decision_record",
        input_schema=IssueDecisionInput,
    )
    issue_node.map_input(input_variable="entrepreneur_id",    expression="flow.input.entrepreneur_id")
    issue_node.map_input(input_variable="confirmed_income_eur", expression="flow.private.final_income_eur")
    issue_node.map_input(input_variable="underwriter_id",     expression="flow.input.underwriter_id")
    issue_node.map_input(input_variable="decision_type",      expression="flow.private.decision_type")
    issue_node.map_input(input_variable="justification",      expression="flow.input.justification")
    issue_node.map_input(input_variable="policy_ref",         expression="flow.input.policy_ref")

    # Script: compose CONFIRM/ADJUST result for the agent
    issued_result = aflow.script(
        name="issued_result",
        display_name="Format Issued Decision Result",
        script="""
self.output.decision_type    = flow.private.decision_type
self.output.entrepreneur_id  = flow.input.entrepreneur_id
self.output.final_income_eur = flow.private.final_income_eur
self.output.policy_ref       = flow.input.policy_ref
self.output.issue_result     = str(flow.nodes['yel_issue_decision_record'].output)
self.output.message = (
    f"DECISION ISSUED ({flow.private.decision_type}). "
    f"Entrepreneur {flow.input.entrepreneur_id}: confirmed YEL income "
    f"{flow.private.final_income_eur:,.0f} EUR/yr. "
    f"Policy: {flow.input.policy_ref}. "
    f"Full record: {self.output.issue_result}"
)
""",
    )

    # Script: compose ESCALATE result — no income change
    escalated_result = aflow.script(
        name="escalated_result",
        display_name="Format Escalation Result",
        script="""
self.output.decision_type    = "ESCALATE"
self.output.entrepreneur_id  = flow.input.entrepreneur_id
self.output.final_income_eur = 0.0
self.output.policy_ref       = flow.input.policy_ref
self.output.issue_result     = ""
self.output.message = (
    "ESCALATED TO APPEALS REVIEW. No income change has been issued. "
    f"Case for entrepreneur {flow.input.entrepreneur_id} has been referred to TELK. "
    "The entrepreneur will be notified within 5 business days. "
    "The current confirmed income remains in force until TELK issues a ruling. "
    "(YEL-POL-04)"
)
""",
    )

    # ── Outer flow branching on the recorded decision ──────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision_type == 'CONFIRM' or flow.private.decision_type == 'ADJUST'",
        to_node=issue_node,
    ).condition(
        default=True,
        to_node=escalated_result,
    )

    # ── Outer flow edges ───────────────────────────────────────────────────
    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(issue_node, issued_result)
    aflow.edge(issued_result, END)
    aflow.edge(escalated_result, END)

    return aflow

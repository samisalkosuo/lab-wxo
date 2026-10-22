"""Medical board referral approval flow for the Disability Pension Triage demo.

This flow encodes the mandatory human governance gate for formally submitting a
disability pension dossier to the Chief Medical Officer (Asiantuntijalääkäri) or
routing a case to the Vocational Rehabilitation Unit.

The agent presents its triage findings and proposes a referral type; the claims
handler reviews and approves or rejects the referral before any official action
is recorded.

Flow name (tool name visible to agents): pdis_refer_claim

Inputs the agent must supply:
  - claimant_id         : claimant reference (e.g. 'CLM-701')
  - referral_type       : 'medical_board', 'vocational_rehab', or 'deny_tyelonly'
  - disposition_summary : agent's evidence-based triage reasoning (shown on form)
  - policy_ref          : policy document ID cited (e.g. 'DIS-POL-01')
  - b_statement_valid   : 'yes' or 'no' — whether the B-statement meets criteria

Flow behavior:
  1. A user activity form shows the claimant summary, referral type, and reasoning.
  2. The claims handler clicks 'Approve Referral' or 'Reject'.
  3. Each button routes to a script that writes the decision to flow.private.
  4. A conditions branch inspects flow.private.decision:
     - Approved  -> tool node calls pdis_dispatch_referral -> result script -> END.
     - Rejected  -> rejection script -> END (nothing is recorded).

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/pension_disability \\
      -f tools/pension_disability/pension_disability.py \\
      -r tools/pension_disability/requirements.txt
  orchestrate tools import -k flow -f flows/pension_disability/refer_medical_board.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ReferralRequest(BaseModel):
    """Input the disability triage agent passes to the referral approval flow."""

    claimant_id: str = Field(
        description=(
            "Claimant identifier the referral concerns. One of: "
            "CLM-701, CLM-702, CLM-703, CLM-704."
        )
    )
    referral_type: str = Field(
        description=(
            "Type of referral to submit on approval. One of: "
            "'medical_board' (refer to Chief Medical Officer / Asiantuntijalääkäri), "
            "'vocational_rehab' (refer to Vocational Rehabilitation Unit), "
            "'deny_tyelonly' (close TyEL case and refer claimant to Kela)."
        )
    )
    disposition_summary: str = Field(
        description=(
            "Agent's evidence-based triage summary. Include diagnosis, work capacity "
            "percentage, qualifying months status, rehabilitation assessment outcome, "
            "and the policy document(s) cited. Shown verbatim to the claims handler."
        )
    )
    policy_ref: str = Field(
        description=(
            "Primary policy document ID cited as the basis for this referral "
            "(e.g. 'DIS-POL-01', 'DIS-POL-02', 'DIS-POL-04')."
        )
    )
    b_statement_valid: str = Field(
        default="yes",
        description="Whether the B-statement meets validity criteria. 'yes' or 'no'.",
    )


# ---------------------------------------------------------------------------
# Private schema
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(
        default="pending",
        description="Claims handler decision: 'approved' or 'rejected'.",
    )


# ---------------------------------------------------------------------------
# Schema for the pdis_dispatch_referral tool node
# ---------------------------------------------------------------------------
class DispatchReferralInput(BaseModel):
    """Arguments of the pdis_dispatch_referral Python tool."""

    claimant_id: str = Field(description="Claimant identifier.")
    referral_type: str = Field(description="Type of referral: medical_board, vocational_rehab, or deny_tyelonly.")
    disposition_summary: str = Field(description="Agent's triage reasoning.")
    policy_ref: str = Field(description="Policy document ID cited.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ReferralResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Claims handler decision: 'approved' or 'rejected'.")
    claimant_id: str = Field(description="Claimant identifier.")
    referral_type: str = Field(description="Type of referral that was proposed.")
    policy_ref: str = Field(description="Policy reference supplied by the agent.")
    dispatch_result: str = Field(
        default="",
        description="JSON output of pdis_dispatch_referral on approval. Empty on rejection.",
    )
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. "
            "On approval: referral outcome. "
            "On rejection: clear statement that nothing was submitted."
        )
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="pdis_refer_claim",
    display_name="Disability Pension Referral Approval",
    description=(
        "Governance gate for disability pension case referrals. "
        "Presents the agent's triage disposition and evidence summary to the "
        "claims handler for review. On approval, calls pdis_dispatch_referral to "
        "record the referral to the Medical Board (CMO), Vocational Rehab Unit, or Kela. "
        "On rejection, returns a clear rejected result with nothing recorded. "
        "Always use this flow instead of calling pdis_dispatch_referral directly. "
        "Required inputs: claimant_id, referral_type, disposition_summary, policy_ref."
    ),
    input_schema=ReferralRequest,
    output_schema=ReferralResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_pdis_refer_claim_flow(aflow: Flow = None) -> Flow:
    """Present triage referral for claims handler approval; dispatch only on approval."""

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Referral Approval"

    approval_form = user_flow.form(
        name="referral_form",
        display_name="Disability Pension Referral Review",
        instructions=(
            "Review the disability pension triage summary below. "
            "Click 'Approve Referral' to submit the referral, or 'Reject' to cancel "
            "with no action recorded."
        ),
        submit_button_label="Approve Referral",
        cancel_button_label=None,
    )

    approval_form.message_output_field(
        name="claimant_display",
        label="Claimant ID",
        message="{flow.input.claimant_id}",
    )
    approval_form.message_output_field(
        name="referral_type_display",
        label="Referral Type",
        message="{flow.input.referral_type}",
    )
    approval_form.message_output_field(
        name="policy_display",
        label="Policy Reference",
        message="{flow.input.policy_ref}",
    )
    approval_form.message_output_field(
        name="b_statement_display",
        label="B-Statement Valid",
        message="{flow.input.b_statement_valid}",
    )
    approval_form.message_output_field(
        name="disposition_display",
        label="Triage Disposition Summary",
        message="{flow.input.disposition_summary}",
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
    user_flow.edge(approval_form, record_approved, button_label="Approve Referral")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # ── Outer flow: tool node for approved path ────────────────────────────
    dispatch_node = aflow.tool(
        "pdis_dispatch_referral",
        input_schema=DispatchReferralInput,
    )
    dispatch_node.map_input(input_variable="claimant_id",       expression="flow.input.claimant_id")
    dispatch_node.map_input(input_variable="referral_type",     expression="flow.input.referral_type")
    dispatch_node.map_input(input_variable="disposition_summary", expression="flow.input.disposition_summary")
    dispatch_node.map_input(input_variable="policy_ref",        expression="flow.input.policy_ref")

    # Script: compose approved result
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Referral Result",
        script="""
self.output.decision       = "approved"
self.output.claimant_id    = flow.input.claimant_id
self.output.referral_type  = flow.input.referral_type
self.output.policy_ref     = flow.input.policy_ref
self.output.dispatch_result = str(flow.nodes['pdis_dispatch_referral'].output)
self.output.message = (
    "REFERRAL APPROVED AND SUBMITTED. "
    f"Claimant: {flow.input.claimant_id}. "
    f"Referral type: {flow.input.referral_type}. "
    f"Policy cited: {flow.input.policy_ref}. "
    f"Dispatch result: {self.output.dispatch_result}"
)
""",
    )

    # Script: compose rejection result
    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Referral Result",
        script="""
self.output.decision       = "rejected"
self.output.claimant_id    = flow.input.claimant_id
self.output.referral_type  = flow.input.referral_type
self.output.policy_ref     = flow.input.policy_ref
self.output.dispatch_result = ""
self.output.message = (
    "REFERRAL REJECTED. No referral was submitted. "
    f"Proposed referral type '{flow.input.referral_type}' for claimant "
    f"'{flow.input.claimant_id}' was declined by the claims handler. "
    "No action has been recorded in the case management system."
)
""",
    )

    # ── Outer flow branching ───────────────────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=dispatch_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(dispatch_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

"""Refund approval flow for the Customer Returns demo.

Encodes the mandatory human governance gate for issuing refunds and replacements.
The customer returns agent calls this flow instead of calling returns_issue_refund
directly, so that no refund or replacement can be issued without explicit human approval.

Flow name (tool name visible to agents): returns_process_return

The Decisions node in this flow checks eligibility deterministically before presenting
the approval form. This is the teaching point: the agent's open-ended reasoning
identifies what to propose; the flow's Decisions node enforces the rule.

Eligibility rule (encoded in the Decisions node):
  - reason == 'defect' or 'warranty_claim'  → always eligible (warranty path)
  - reason == 'no_reason' and within_window == True  → eligible (30-day window)
  - reason == 'gift_return' and within_window == True  → eligible (gift-return window)
  - all other combinations  → ineligible (return denied without showing the approval form)

Inputs the agent must supply:
  - order_id          : order to refund (e.g. 'ORD-1001')
  - customer_id       : customer ID (must match the order)
  - refund_reason     : one of: defect, no_reason, gift_return, warranty_claim
  - refund_type       : one of: full_refund, replacement, store_credit
  - within_window     : whether the order is within the 30-day return window (bool)
  - policy_ref        : policy document ID cited (e.g. 'RP-WARRANTY-01')
  - justification     : agent's evidence-based reasoning shown to the approver

Flow behavior:
  1. Decisions node checks eligibility from the inputs.
  2. Ineligible  → ineligible_result script → END (no human form shown).
  3. Eligible    → user activity form shows the proposal to the approver.
  4. Approver clicks "Approve" or "Reject".
  5. Approve     → returns_issue_refund tool node → approved_result script → END.
  6. Reject      → rejected_result script → END.

Import prerequisites (must be imported before this flow):
  orchestrate tools import -k python -p tools/customer_returns \\
      -f tools/customer_returns/customer_returns.py \\
      -r tools/customer_returns/requirements.txt
  orchestrate tools import -k flow -f flows/customer_returns/process_return.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ReturnRequest(BaseModel):
    """Input the customer returns agent passes to the approval flow."""

    order_id: str = Field(
        description="Order ID to process, e.g. 'ORD-1001'.",
    )
    customer_id: str = Field(
        description="Customer ID; must match the order. E.g. 'CUST-101'.",
    )
    refund_reason: str = Field(
        description=(
            "Reason for the return. One of: defect, no_reason, gift_return, warranty_claim."
        )
    )
    refund_type: str = Field(
        description=(
            "Type of resolution requested. One of: full_refund, replacement, store_credit."
        )
    )
    within_window: bool = Field(
        description=(
            "True if the order was purchased within the 30-day return window. "
            "Determined by returns_lookup_order (within_30_day_window field)."
        )
    )
    policy_ref: str = Field(
        default="",
        description="Policy document ID cited as the basis (e.g. 'RP-WARRANTY-01').",
    )
    justification: str = Field(
        description=(
            "Agent's evidence-based reasoning for proposing this return. "
            "Shown verbatim to the approver."
        )
    )


# ---------------------------------------------------------------------------
# Private schema
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(
        default="pending",
        description="Human decision: 'approved' or 'rejected'.",
    )


# ---------------------------------------------------------------------------
# Schema for the returns_issue_refund tool node
# ---------------------------------------------------------------------------
class IssueRefundInput(BaseModel):
    """Arguments of the returns_issue_refund Python tool."""

    order_id: str = Field(description="Order ID to refund.")
    customer_id: str = Field(description="Customer ID (must match the order).")
    refund_reason: str = Field(description="Reason: defect, no_reason, gift_return, warranty_claim.")
    refund_type: str = Field(description="Type: full_refund, replacement, store_credit.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ReturnResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="'approved', 'rejected', or 'ineligible'.")
    order_id: str = Field(description="Order that was processed.")
    refund_reason: str = Field(description="Reason supplied by the agent.")
    refund_type: str = Field(description="Resolution type proposed.")
    policy_ref: str = Field(description="Policy document cited.")
    execution_result: str = Field(
        default="",
        description="JSON output of returns_issue_refund on approval. Empty otherwise.",
    )
    message: str = Field(
        description="Human-readable summary the agent should report verbatim.",
    )


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="returns_process_return",
    display_name="Process Return Request",
    description=(
        "Governance gate for customer refunds and replacements. "
        "Checks eligibility with a Decisions node, then presents the proposal "
        "to a human approver. On approval, calls returns_issue_refund and returns "
        "the result. On rejection or ineligibility, returns a clear outcome with no changes made. "
        "Required inputs: order_id, customer_id, refund_reason, refund_type, within_window, justification. "
        "Optional: policy_ref."
    ),
    input_schema=ReturnRequest,
    output_schema=ReturnResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_process_return_flow(aflow: Flow = None) -> Flow:
    """Check eligibility, get human approval, then issue the refund or replacement."""

    # ── Ineligible path: no approval form shown ────────────────────────────
    ineligible_result = aflow.script(
        name="ineligible_result",
        display_name="Return Ineligible",
        script="""
self.output.decision         = "ineligible"
self.output.order_id         = flow.input.order_id
self.output.refund_reason    = flow.input.refund_reason
self.output.refund_type      = flow.input.refund_type
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = ""
self.output.message = (
    "RETURN INELIGIBLE. "
    f"Order: {flow.input.order_id}. "
    f"Reason: {flow.input.refund_reason}. "
    "The order is outside the 30-day return window and does not qualify for a "
    "warranty claim or gift return. "
    f"Policy reference: {flow.input.policy_ref or 'RP-STANDARD-01'}. "
    "No refund or replacement has been issued."
)
""",
    )

    # ── User activity ──────────────────────────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Return Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Return Request Approval",
        instructions=(
            "Review the proposed return below. "
            "Click 'Approve' to issue the refund or replacement, "
            "or 'Reject' to decline with no changes made."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )

    approval_form.message_output_field(
        name="order_display",
        label="Order ID",
        message="{flow.input.order_id}",
    )
    approval_form.message_output_field(
        name="customer_display",
        label="Customer ID",
        message="{flow.input.customer_id}",
    )
    approval_form.message_output_field(
        name="reason_display",
        label="Return Reason",
        message="{flow.input.refund_reason}",
    )
    approval_form.message_output_field(
        name="type_display",
        label="Resolution Type",
        message="{flow.input.refund_type}",
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

    # ── Tool node: returns_issue_refund ────────────────────────────────────
    issue_node = aflow.tool(
        "returns_issue_refund",
        input_schema=IssueRefundInput,
    )
    issue_node.map_input(input_variable="order_id",      expression="flow.input.order_id")
    issue_node.map_input(input_variable="customer_id",   expression="flow.input.customer_id")
    issue_node.map_input(input_variable="refund_reason", expression="flow.input.refund_reason")
    issue_node.map_input(input_variable="refund_type",   expression="flow.input.refund_type")

    # ── Result scripts ─────────────────────────────────────────────────────
    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision         = "approved"
self.output.order_id         = flow.input.order_id
self.output.refund_reason    = flow.input.refund_reason
self.output.refund_type      = flow.input.refund_type
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = str(flow.nodes['returns_issue_refund'].output)
self.output.message = (
    "APPROVED AND PROCESSED. "
    f"Order: {flow.input.order_id}. "
    f"Resolution: {flow.input.refund_type}. "
    f"Policy: {flow.input.policy_ref or 'N/A'}. "
    f"Result: {self.output.execution_result}"
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
self.output.decision         = "rejected"
self.output.order_id         = flow.input.order_id
self.output.refund_reason    = flow.input.refund_reason
self.output.refund_type      = flow.input.refund_type
self.output.policy_ref       = flow.input.policy_ref
self.output.execution_result = ""
self.output.message = (
    "REJECTED. No refund or replacement was issued. "
    f"Proposed resolution '{flow.input.refund_type}' for order '{flow.input.order_id}' "
    "was declined by the approver. No changes have been made."
)
""",
    )

    # ── Decisions node: eligibility check ─────────────────────────────────
    # Eligible if:
    #   reason is 'defect' or 'warranty_claim' (warranty path, no window check needed), OR
    #   reason is 'no_reason' or 'gift_return' AND within_window is True
    eligibility_branch: Branch = aflow.conditions()
    eligibility_branch.condition(
        expression=(
            "flow.input.refund_reason == 'defect' or "
            "flow.input.refund_reason == 'warranty_claim' or "
            "((flow.input.refund_reason == 'no_reason' or "
            "  flow.input.refund_reason == 'gift_return') and "
            " flow.input.within_window == True)"
        ),
        to_node=user_flow,
    ).condition(
        default=True,
        to_node=ineligible_result,
    )

    # ── Outer flow: branch on human decision ──────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'",
        to_node=issue_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Outer flow edges ───────────────────────────────────────────────────
    aflow.edge(START, eligibility_branch)
    aflow.edge(ineligible_result, END)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(issue_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

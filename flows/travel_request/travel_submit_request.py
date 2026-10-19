"""Travel request approval flow for the Travel Request demo.

The travel_request agent decides what approval level a trip needs and then calls this flow
instead of issuing a request id itself. The flow shows the proposal to a human approver,
and only on approval calls the internal write tool travel_issue_request_id. The tool
re-checks traveler, budget and approval level in code, so a wrong agent input cannot
produce an id.

Flow name (tool name visible to agents): travel_submit_request

Import prerequisites (the tool must exist before this flow is imported):
  orchestrate tools import -k python -p tools/travel_request \\
      -f tools/travel_request/travel_request.py \\
      -r tools/travel_request/requirements.txt
  orchestrate tools import -k flow -f flows/travel_request/travel_submit_request.py

Behaviour:
  1. A user activity shows the proposed trip, the required approval level and the justification.
  2. The approver clicks Approve or Reject.
  3. Approve -> tool node calls travel_issue_request_id -> result script -> END.
  4. Reject  -> rejection script -> END. No request id is issued.

Not tested: the form, the buttons, and the tool-node input mapping have not been run
against an instance. They follow flows/incident_triage/request_remediation.py.
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


class TravelRequest(BaseModel):
    """Input the travel_request agent passes to the approval flow."""

    employee_id: str = Field(description="Employee id such as 'E-1001'.")
    destination: str = Field(description="Destination as given by the traveler, for example 'Bryssel'.")
    start_date: str = Field(description="First day of the trip, 'YYYY-MM-DD'.")
    end_date: str = Field(description="Last day of the trip, 'YYYY-MM-DD'.")
    purpose: str = Field(
        description="One of: customer, training, internal_meeting, conference, leisure."
    )
    estimated_total_eur: float = Field(
        description="Estimated total cost in EUR, taken from travel_estimate_reimbursement."
    )
    includes_leave: bool = Field(description="True if leave days are attached to the trip.")
    abroad: bool = Field(description="True for trips outside Finland.")
    required_level: str = Field(
        description="Approval level the trip needs: none, manager or director (from policy TP-APPR-01)."
    )
    justification: str = Field(
        description="The agent's reasoning for the approver, citing policy ids and Finnish section references."
    )


class FlowPrivate(BaseModel):
    """Private state carrying the human decision across the userflow boundary."""

    decision: str = Field(default="pending", description="'approved' or 'rejected'.")


class IssueRequestIdInput(BaseModel):
    """Arguments of the travel_issue_request_id Python tool."""

    employee_id: str = Field(description="Employee id.")
    destination: str = Field(description="Destination.")
    start_date: str = Field(description="Start date.")
    end_date: str = Field(description="End date.")
    purpose: str = Field(description="Trip purpose.")
    estimated_total_eur: float = Field(description="Estimated total cost in EUR.")
    includes_leave: bool = Field(description="Leave attached.")
    abroad: bool = Field(description="Trip abroad.")
    granted_level: str = Field(description="Approval level recorded by the human decision.")


class TravelRequestResult(BaseModel):
    """Structured result the flow returns to the agent."""

    decision: str = Field(description="Human decision: 'approved' or 'rejected'.")
    employee_id: str = Field(description="Employee id supplied by the agent.")
    destination: str = Field(description="Destination supplied by the agent.")
    request_id: str = Field(default="", description="Request id on approval, empty on rejection.")
    issue_result: str = Field(default="", description="Raw output of the issue tool on approval.")
    message: str = Field(
        description=(
            "Human-readable summary the agent should report verbatim. On approval: the issue "
            "outcome including the request id or the validation error. On rejection: a clear "
            "statement that no request id was issued."
        )
    )


@flow(
    name="travel_submit_request",
    display_name="Submit Travel Request for Approval",
    description=(
        "Approval gate for travel requests. Shows the proposed trip, the required approval level "
        "and the justification to a human approver. On approval, issues a request id through the "
        "internal travel_issue_request_id tool and returns the result; on rejection, returns a clear "
        "'rejected - no request id issued' result. Always use this flow instead of any other way of "
        "creating a request id. Required inputs: employee_id, destination, start_date, end_date, "
        "purpose, estimated_total_eur, includes_leave, abroad, required_level, justification."
    ),
    input_schema=TravelRequest,
    output_schema=TravelRequestResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_travel_submit_request_flow(aflow: Flow = None) -> Flow:
    """Present a travel request for human approval; issue the request id only on approval."""

    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Travel Request Approval"

    approval_form = user_flow.form(
        name="approval_form",
        display_name="Travel Request Approval",
        instructions=(
            "Review the proposed trip below. Click 'Approve' to issue a request id, "
            "or 'Reject' to cancel. Nothing is issued on Reject."
        ),
        submit_button_label="Approve",
        cancel_button_label=None,
    )

    for name, label, expr in (
        ("employee_display", "Traveler (employee id)", "{flow.input.employee_id}"),
        ("destination_display", "Destination", "{flow.input.destination}"),
        ("start_display", "Start date", "{flow.input.start_date}"),
        ("end_display", "End date", "{flow.input.end_date}"),
        ("purpose_display", "Purpose", "{flow.input.purpose}"),
        ("estimate_display", "Estimated total (EUR)", "{flow.input.estimated_total_eur}"),
        ("leave_display", "Leave days attached", "{flow.input.includes_leave}"),
        ("abroad_display", "Trip abroad", "{flow.input.abroad}"),
        ("level_display", "Approval level required", "{flow.input.required_level}"),
        ("justification_display", "Agent justification", "{flow.input.justification}"),
    ):
        approval_form.message_output_field(name=name, label=label, message=expr)

    record_approved = user_flow.script(name="record_approved", script='flow.private.decision = "approved"')
    record_rejected = user_flow.script(name="record_rejected", script='flow.private.decision = "rejected"')
    reject_btn = user_flow.add_button("Reject")

    user_flow.edge(START, approval_form)
    user_flow.edge(approval_form, record_approved, button_label="Approve")
    user_flow.edge(record_approved, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # Explicit input schema: the incident flow found that resolving it from the deployed
    # tool produced an untyped "data" argument and a runtime TypeError (status 424).
    issue_node = aflow.tool("travel_issue_request_id", input_schema=IssueRequestIdInput)
    issue_node.map_input(input_variable="employee_id", expression="flow.input.employee_id")
    issue_node.map_input(input_variable="destination", expression="flow.input.destination")
    issue_node.map_input(input_variable="start_date", expression="flow.input.start_date")
    issue_node.map_input(input_variable="end_date", expression="flow.input.end_date")
    issue_node.map_input(input_variable="purpose", expression="flow.input.purpose")
    issue_node.map_input(input_variable="estimated_total_eur", expression="flow.input.estimated_total_eur")
    issue_node.map_input(input_variable="includes_leave", expression="flow.input.includes_leave")
    issue_node.map_input(input_variable="abroad", expression="flow.input.abroad")
    # The approver granted the level the agent asked for; the tool checks it is high enough.
    issue_node.map_input(input_variable="granted_level", expression="flow.input.required_level")

    approved_result = aflow.script(
        name="approved_result",
        display_name="Format Approved Result",
        script="""
self.output.decision = "approved"
self.output.employee_id = flow.input.employee_id
self.output.destination = flow.input.destination
self.output.issue_result = str(flow.nodes['travel_issue_request_id'].output)
self.output.request_id = ""
self.output.message = (
    "APPROVED. Issue result: " + self.output.issue_result
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
self.output.decision = "rejected"
self.output.employee_id = flow.input.employee_id
self.output.destination = flow.input.destination
self.output.request_id = ""
self.output.issue_result = ""
self.output.message = (
    "REJECTED. No request id was issued. "
    f"The trip to '{flow.input.destination}' ({flow.input.start_date} - {flow.input.end_date}) "
    "was declined by the approver."
)
""",
    )

    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'approved'", to_node=issue_node
    ).condition(default=True, to_node=rejected_result)

    aflow.edge(START, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(issue_node, approved_result)
    aflow.edge(approved_result, END)
    aflow.edge(rejected_result, END)

    return aflow

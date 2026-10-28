"""Answer-gap routing flow for the HR Tacit Knowledge demo.

The hr_tk_guide agent calls this flow when a learner's question is not covered by
the KB. The flow notifies the expert (mock), then shows the expert a form to answer.
The expert's answer is submitted as a new KB article via hr_tk_publish_article.
On Decline, nothing is recorded.

Flow name (tool name visible to agents): hr_tk_answer_gap

Governance:
  - The Decline path never reaches the publish node.
  - hr_tk_notify_expert is called first (mock — nothing is actually sent).
  - hr_tk_publish_article is called with action='new' only on Submit answer.

Pattern: result scripts write to flow.private; aflow.map_output() wires private fields
to the output schema explicitly. This matches the proven request_remediation pattern
and avoids the intermittent auto_data_mapping failure seen without explicit map_output().

Import prerequisites:
  orchestrate tools import -k python -p tools/hr_tk -f tools/hr_tk/hr_tk.py -r tools/hr_tk/requirements.txt
  orchestrate tools import -k flow -f flows/hr_tk/hr_tk_answer_gap.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class AnswerGapRequest(BaseModel):
    """Input the hr_tk_guide agent passes to the answer-gap flow."""

    question: str = Field(
        description="The learner's question exactly as asked."
    )
    learner_role: str = Field(
        description="The learner's role, e.g. 'HR Coordinator, Finland desk'."
    )
    expert_id: str = Field(
        description="ID of the expert to notify and ask for an answer, e.g. 'X-102'."
    )
    expert_name: str = Field(
        description="The expert's name, for the form display."
    )
    topic: str = Field(
        description="Short topic label for the notification subject."
    )


# ---------------------------------------------------------------------------
# Private schema — carries state across node boundaries
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(default="pending", description="'submitted' or 'declined'.")
    expert_answer: str = Field(default="", description="The expert's answer text.")
    answer_date: str = Field(default="2025-01-01", description="ISO date the expert answered.")
    publish_result: str = Field(default="", description="Raw output of hr_tk_publish_article.")
    article_id: str = Field(default="", description="Article ID from publish result.")
    message: str = Field(default="", description="Final message for the agent.")


# ---------------------------------------------------------------------------
# Tool node schema: hr_tk_notify_expert
# ---------------------------------------------------------------------------
class NotifyInput(BaseModel):
    """Arguments of the hr_tk_notify_expert Python tool."""

    expert_id: str = Field(description="Expert ID.")
    subject: str = Field(description="Notification subject.")
    message: str = Field(description="Notification body.")


# ---------------------------------------------------------------------------
# Tool node schema: hr_tk_publish_article
# ---------------------------------------------------------------------------
class PublishInput(BaseModel):
    """Arguments of the hr_tk_publish_article Python tool."""

    action: str = Field(description="'new'.")
    title: str = Field(description="Article title.")
    body: str = Field(description="Full article body text.")
    source_ids: str = Field(description="Source: the expert's answer.")
    author_role: str = Field(description="Role of the expert who answered.")
    verified_date: str = Field(description="ISO date the expert answered.")
    status: str = Field(description="'current'.")
    approver: str = Field(description="Who confirmed (the expert).")
    applies_to: str = Field(description="Who the article applies to.")
    article_id: str = Field(default="", description="Empty for new article.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class AnswerGapResult(BaseModel):
    """Structured result the flow returns to the guide agent."""

    decision: str = Field(description="'submitted' or 'declined'.")
    question: str = Field(description="The learner's original question.")
    expert_id: str = Field(description="The expert who was asked.")
    article_id: str = Field(default="", description="Article ID of the new draft (on submitted).")
    live_in_kb: bool = Field(default=False, description="Always false until KB is re-imported.")
    publish_result: str = Field(default="", description="Raw output of publish tool (on submitted).")
    message: str = Field(description="Human-readable summary for the agent to report verbatim.")


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="hr_tk_answer_gap",
    display_name="Route Question to Expert and Capture Answer",
    description=(
        "Used when the KB does not cover the learner's question. "
        "Notifies the right expert (mock), then shows the expert a form with the question "
        "and an answer field. On Submit, the answer is published as a new KB article. "
        "On Decline, nothing is recorded and the learner is told to wait. "
        "Required inputs: question, learner_role, expert_id, expert_name, topic."
    ),
    input_schema=AnswerGapRequest,
    output_schema=AnswerGapResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_hr_tk_answer_gap_flow(aflow: Flow = None) -> Flow:
    """Route an uncovered learner question to an expert and capture the answer."""

    # ── Tool node 1: notify expert (mock) ─────────────────────────────────
    notify_node = aflow.tool("hr_tk_notify_expert", input_schema=NotifyInput)
    notify_node.map_input(
        input_variable="expert_id",
        expression="flow.input.expert_id",
    )
    notify_node.map_input(
        input_variable="subject",
        expression='"Knowledge gap question: " + str(flow.input.topic or "")',
    )
    notify_node.map_input(
        input_variable="message",
        expression=(
            '"A learner (" + str(flow.input.learner_role or "") + ") asked: " '
            '+ str(flow.input.question or "")'
        ),
    )

    # ── User activity: expert answer form ─────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Expert: Answer a Learner Question"

    answer_form = user_flow.form(
        name="answer_form",
        display_name="Answer a Knowledge Gap Question",
        instructions=(
            "A learner has asked a question that is not covered in the knowledge base. "
            "Please provide your answer below, then click 'Submit answer'. "
            "Your answer will be saved as a new KB article. "
            "Click 'Decline' if you cannot answer at this time."
        ),
        submit_button_label="Submit answer",
        cancel_button_label=None,
    )

    # Read-only: the learner's question
    answer_form.message_output_field(
        name="question_display",
        label="Learner question",
        message="{flow.input.question}",
    )
    answer_form.message_output_field(
        name="role_display",
        label="Learner role",
        message="{flow.input.learner_role}",
    )

    # Editable: expert's answer
    answer_form.text_input_field(
        name="expert_answer",
        label="Your answer (this will become a KB article)",
        required=True,
        single_line=False,
        placeholder_text="Write your answer here. It will be published as a new KB article.",
    )

    # Date field: verified date
    answer_form.text_input_field(
        name="answer_date",
        label="Date (YYYY-MM-DD)",
        required=True,
        single_line=True,
        placeholder_text="2025-06-01",
    )

    # Scripts inside the userflow record the decision
    record_submitted = user_flow.script(
        name="record_submitted",
        script='flow.private.decision = "submitted"',
    )
    record_declined = user_flow.script(
        name="record_declined",
        script='flow.private.decision = "declined"',
    )

    decline_btn = user_flow.add_button("Decline")

    user_flow.edge(START, answer_form)
    user_flow.edge(answer_form, record_submitted, button_label="Submit answer")
    user_flow.edge(record_submitted, END)
    user_flow.edge(decline_btn, record_declined)
    user_flow.edge(record_declined, END)

    # ── Outer flow: read form output into flow.private ─────────────────────
    resolve_answer = aflow.script(
        name="resolve_answer",
        display_name="Resolve Expert Answer",
        script="""
answer_text = None
answer_date = None
try:
    node_out = flow.nodes['answer_form'].output
    if hasattr(node_out, 'expert_answer'):
        answer_text = node_out.expert_answer
        answer_date = node_out.answer_date
    elif isinstance(node_out, dict):
        answer_text = node_out.get('expert_answer')
        answer_date = node_out.get('answer_date')
except Exception:
    answer_text = None
    answer_date = None

flow.private.expert_answer = str(answer_text or "")
flow.private.answer_date   = str(answer_date or "2025-01-01").strip() or "2025-01-01"
""",
    )

    # ── Tool node 2: hr_tk_publish_article ────────────────────────────────
    publish_node = aflow.tool("hr_tk_publish_article", input_schema=PublishInput)
    publish_node.map_input(input_variable="action",        expression='"new"')
    publish_node.map_input(
        input_variable="title",
        expression='"Expert answer: " + str(flow.input.topic or flow.input.question or "")[:80]',
    )
    publish_node.map_input(
        input_variable="body",
        expression=(
            '"QUESTION\\n" + str(flow.input.question or "") + '
            '"\\n\\nANSWER\\n" + str(flow.private.expert_answer or "")'
        ),
    )
    publish_node.map_input(
        input_variable="source_ids",
        expression='"Expert answer from " + str(flow.input.expert_id or "")',
    )
    publish_node.map_input(input_variable="author_role",  expression='"Expert"')
    publish_node.map_input(
        input_variable="verified_date",
        expression="flow.private.answer_date",
    )
    publish_node.map_input(input_variable="status",       expression='"current"')
    publish_node.map_input(
        input_variable="approver",
        expression='"Expert: " + str(flow.input.expert_name or flow.input.expert_id or "")',
    )
    publish_node.map_input(
        input_variable="applies_to",
        expression='"Learners asking about " + str(flow.input.topic or "")',
    )
    publish_node.map_input(input_variable="article_id",   expression='""')

    # ── Result scripts — write to flow.private; wired to output via map_output() ──
    # NOTE: import is blocked in script nodes (ValueError: __import__ not found).
    # Extract article_id with string search instead of json.loads.
    submitted_result = aflow.script(
        name="submitted_result",
        display_name="Format Submitted Result",
        script="""
flow.private.decision      = "submitted"
flow.private.publish_result = str(flow.nodes['hr_tk_publish_article'].output)
flow.private.article_id    = ""
try:
    raw = flow.private.publish_result
    marker = '"article_id": "'
    idx = raw.find(marker)
    if idx >= 0:
        start = idx + len(marker)
        end = raw.find('"', start)
        if end > start:
            flow.private.article_id = raw[start:end]
except Exception:
    pass
flow.private.message = (
    "EXPERT ANSWER SUBMITTED AND RECORDED. "
    f"Article {flow.private.article_id} created for: '{flow.input.question}'. "
    f"Expert: {flow.input.expert_id}. "
    "NOTE: the article is NOT yet searchable in the KB. "
    "It will be searchable after the next KB re-import."
)
""",
    )

    declined_result = aflow.script(
        name="declined_result",
        display_name="Format Declined Result",
        script="""
flow.private.decision       = "declined"
flow.private.publish_result = ""
flow.private.article_id     = ""
flow.private.message = (
    "EXPERT DECLINED. No answer was recorded at this time. "
    f"The learner should be told that the question has been noted "
    f"and the expert ({flow.input.expert_id}) will follow up when available."
)
""",
    )

    # ── Conditions branch ─────────────────────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'submitted'",
        to_node=publish_node,
    ).condition(
        default=True,
        to_node=declined_result,
    )

    # ── Outer edges ────────────────────────────────────────────────────────
    aflow.edge(START, notify_node)
    aflow.edge(notify_node, user_flow)
    aflow.edge(user_flow, resolve_answer)
    aflow.edge(resolve_answer, decision_branch)
    aflow.edge(publish_node, submitted_result)
    aflow.edge(submitted_result, END)
    aflow.edge(declined_result, END)

    # ── Explicit output mapping — required to avoid auto_data_mapping failures ──
    # Pattern from flows/incident_triage/request_remediation.py (browser-verified).
    aflow.map_output(output_variable="decision",       expression="flow.private.decision")
    aflow.map_output(output_variable="question",       expression="flow.input.question")
    aflow.map_output(output_variable="expert_id",      expression="flow.input.expert_id")
    aflow.map_output(output_variable="article_id",     expression="flow.private.article_id")
    aflow.map_output(output_variable="live_in_kb",     expression="False")
    aflow.map_output(output_variable="publish_result", expression="flow.private.publish_result")
    aflow.map_output(output_variable="message",        expression="flow.private.message")

    return aflow

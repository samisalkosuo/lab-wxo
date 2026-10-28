"""Review-and-publish approval flow for the HR Tacit Knowledge demo.

The hr_tk_curator agent calls this flow instead of calling hr_tk_publish_article itself.
The flow shows the draft to an expert for review. Only on Confirm does it call the
internal write tool hr_tk_publish_article.

Flow name (tool name visible to agents): hr_tk_review_draft

Governance:
  - status is fixed to 'current' by the flow.
  - approver is fixed to 'Expert reviewer' by the flow.
  - The non-confirm path is the default=True branch: nothing is published.

Pattern: result scripts write to flow.private; aflow.map_output() wires private fields
to the output schema explicitly. This matches the proven request_remediation pattern
and avoids the intermittent auto_data_mapping failure seen without explicit map_output().

Open Items (see plan):
  - Editable draft body field (text_input_field) is documented but not verified.
  - Expert assignment (assign_to) requires a real tenant user.

Import prerequisites:
  orchestrate tools import -k python -p tools/hr_tk -f tools/hr_tk/hr_tk.py -r tools/hr_tk/requirements.txt
  orchestrate tools import -k flow -f flows/hr_tk/hr_tk_review_draft.py
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, Branch


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------
class ReviewDraftRequest(BaseModel):
    """Input the hr_tk_curator agent passes to the review flow."""

    action: str = Field(
        description="'new' to create a new article, 'update' to revise an existing one."
    )
    title: str = Field(
        description="Proposed article title (PII must already be removed)."
    )
    draft_body: str = Field(
        description=(
            "Full proposed article body text. PII must have been removed and the agent must "
            "have called hr_tk_scan_pii to confirm the text is clean before opening this flow."
        )
    )
    source_ids: str = Field(
        description="Comma-separated artifact IDs or document titles that sourced this article."
    )
    author_role: str = Field(
        description="Role label of the expert who owns the content, e.g. 'Senior HR Specialist'."
    )
    verified_date: str = Field(
        description="ISO date (YYYY-MM-DD) the expert verified the content."
    )
    applies_to: str = Field(
        default="All Finland HR staff",
        description="Who this article applies to.",
    )
    article_id: str = Field(
        default="",
        description=(
            "For 'update': the ID of the article to revise, e.g. 'HR-TK-ART-04'. "
            "Empty for 'new'."
        ),
    )
    placement_summary: str = Field(
        default="",
        description=(
            "One or two sentences explaining why this draft belongs here: "
            "new topic, update to a named article, or duplicate of an existing one."
        ),
    )
    pii_summary: str = Field(
        default="PII scan: clean.",
        description="Summary of the PII scan result, e.g. 'PII scan: clean.'",
    )


# ---------------------------------------------------------------------------
# Private schema — carries state across node boundaries
# ---------------------------------------------------------------------------
class FlowPrivate(BaseModel):
    """Private state not exposed to users."""

    decision: str = Field(default="pending", description="'confirmed' or 'rejected'.")
    publish_result: str = Field(default="", description="Raw output of hr_tk_publish_article.")
    article_id: str = Field(default="", description="Article ID from publish result.")
    message: str = Field(default="", description="Final message for the agent.")
    draft_preview: str = Field(
        default="",
        description=(
            "Brace-escaped copy of draft_body for safe display in message_output_field. "
            "Set by init_preview script before the userflow."
        ),
    )


# ---------------------------------------------------------------------------
# Tool node schema (must match hr_tk_publish_article signature)
# ---------------------------------------------------------------------------
class PublishInput(BaseModel):
    """Arguments of the hr_tk_publish_article Python tool."""

    action: str = Field(description="'new' or 'update'.")
    title: str = Field(description="Article title.")
    body: str = Field(description="Full article body text.")
    source_ids: str = Field(description="Source artifact IDs.")
    author_role: str = Field(description="Role of the content owner.")
    verified_date: str = Field(description="ISO date of verification.")
    status: str = Field(description="'current' or 'superseded'.")
    approver: str = Field(description="Who confirmed the draft.")
    applies_to: str = Field(description="Who the article applies to.")
    article_id: str = Field(default="", description="Required for 'update'.")


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
class ReviewDraftResult(BaseModel):
    """Structured result the flow returns to the curator agent."""

    decision: str = Field(description="'confirmed' or 'rejected'.")
    title: str = Field(description="Article title from the draft.")
    action: str = Field(description="'new' or 'update'.")
    article_id: str = Field(default="", description="Article ID returned by publish tool.")
    live_in_kb: bool = Field(
        default=False,
        description="Always false: articles need a KB re-import to become searchable.",
    )
    publish_result: str = Field(
        default="",
        description="Raw output of hr_tk_publish_article. Empty on rejection.",
    )
    message: str = Field(description="Human-readable summary for the agent to report verbatim.")


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------
@flow(
    name="hr_tk_review_draft",
    display_name="Expert Review: Tacit Knowledge Draft",
    description=(
        "Governance gate for publishing a tacit-knowledge article. "
        "Shows the draft title, body, source IDs, placement summary, and PII scan result "
        "to an expert for review. On Confirm, calls hr_tk_publish_article and returns the result. "
        "On Reject, nothing is published. "
        "IMPORTANT: the curator must call hr_tk_scan_pii on the title + body and confirm clean "
        "BEFORE calling this flow. The publish tool also re-checks PII. "
        "Required inputs: action, title, draft_body, source_ids, author_role, verified_date. "
        "Optional: applies_to, article_id (for update), placement_summary, pii_summary."
    ),
    input_schema=ReviewDraftRequest,
    output_schema=ReviewDraftResult,
    private_schema=FlowPrivate,
    suppress_agent_summarization=False,
)
def build_hr_tk_review_draft_flow(aflow: Flow = None) -> Flow:
    """Show a tacit-knowledge draft to an expert for confirmation or rejection."""

    # ── Init script: copy draft_body into flow.private.draft_preview with
    # curly braces replaced so message_output_field {}-substitution can't crash.
    init_preview = aflow.script(
        name="init_preview",
        display_name="Prepare Draft Preview",
        script=(
            "flow.private.draft_preview = "
            "str(flow.input.draft_body or '').replace('{', '(').replace('}', ')')"
        ),
    )

    # ── User activity: expert review form ─────────────────────────────────
    user_flow = aflow.userflow()
    user_flow.spec.display_name = "Expert Review: Tacit Knowledge Draft"

    review_form = user_flow.form(
        name="review_form",
        display_name="Draft Article for Expert Review",
        instructions=(
            "Please review the proposed article below. "
            "You may edit the article text before confirming. "
            "Click 'Confirm' to publish, or 'Reject' to discard. "
            "Nothing is published until you click Confirm."
        ),
        submit_button_label="Confirm",
        cancel_button_label=None,
    )

    # Read-only display fields
    review_form.message_output_field(
        name="action_display",
        label="Action",
        message="{flow.input.action}",
    )
    review_form.message_output_field(
        name="title_display",
        label="Proposed Title",
        message="{flow.input.title}",
    )
    review_form.message_output_field(
        name="placement_display",
        label="Placement",
        message="{flow.input.placement_summary}",
    )
    review_form.message_output_field(
        name="sources_display",
        label="Sources",
        message="{flow.input.source_ids}",
    )
    review_form.message_output_field(
        name="pii_display",
        label="PII Scan",
        message="{flow.input.pii_summary}",
    )
    review_form.message_output_field(
        name="author_display",
        label="Author Role",
        message="{flow.input.author_role}",
    )
    review_form.message_output_field(
        name="date_display",
        label="Verified Date",
        message="{flow.input.verified_date}",
    )
    # Draft body displayed via message_output_field referencing flow.private.draft_preview.
    # draft_preview has { } replaced with ( ) so the template substitution cannot crash.
    review_form.message_output_field(
        name="body_display",
        label="Article Draft (read-only — review before confirming)",
        message="{flow.private.draft_preview}",
    )

    # Single-line scripts only inside userflow (multiline is not supported).
    record_confirmed = user_flow.script(
        name="record_confirmed",
        script='flow.private.decision = "confirmed"',
    )
    record_rejected = user_flow.script(
        name="record_rejected",
        script='flow.private.decision = "rejected"',
    )

    reject_btn = user_flow.add_button("Reject")

    user_flow.edge(START, review_form)
    user_flow.edge(review_form, record_confirmed, button_label="Confirm")
    user_flow.edge(record_confirmed, END)
    user_flow.edge(reject_btn, record_rejected)
    user_flow.edge(record_rejected, END)

    # ── Tool node: hr_tk_publish_article ──────────────────────────────────
    # draft_body is mapped directly from flow.input — no intermediate script needed.
    publish_node = aflow.tool("hr_tk_publish_article", input_schema=PublishInput)
    publish_node.map_input(input_variable="action",        expression="flow.input.action")
    publish_node.map_input(input_variable="title",         expression="flow.input.title")
    publish_node.map_input(input_variable="body",          expression="flow.input.draft_body")
    publish_node.map_input(input_variable="source_ids",    expression="flow.input.source_ids")
    publish_node.map_input(input_variable="author_role",   expression="flow.input.author_role")
    publish_node.map_input(input_variable="verified_date", expression="flow.input.verified_date")
    publish_node.map_input(input_variable="status",        expression='"current"')
    publish_node.map_input(input_variable="approver",      expression='"Expert reviewer"')
    publish_node.map_input(input_variable="applies_to",    expression="flow.input.applies_to")
    publish_node.map_input(input_variable="article_id",    expression="flow.input.article_id")

    # ── Result scripts — write to flow.private; wired to output via map_output() ──
    # NOTE: import is blocked in script nodes (ValueError: __import__ not found).
    # Extract article_id with string search instead of json.loads.
    confirmed_result = aflow.script(
        name="confirmed_result",
        display_name="Format Confirmed Result",
        script="""
flow.private.decision       = "confirmed"
flow.private.publish_result = str(flow.nodes['hr_tk_publish_article'].output)
flow.private.article_id     = ""
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
    "CONFIRMED AND RECORDED. "
    f"Article {flow.private.article_id} ({flow.input.action}): '{flow.input.title}'. "
    "NOTE: the article is NOT yet searchable in the KB. "
    f"To make it searchable, save it to "
    f"knowledge/hr-tacit-knowledge/articles/{flow.private.article_id}.txt "
    "and re-import the KB. "
    f"Full publish result: {flow.private.publish_result}"
)
""",
    )

    rejected_result = aflow.script(
        name="rejected_result",
        display_name="Format Rejected Result",
        script="""
flow.private.decision       = "rejected"
flow.private.publish_result = ""
flow.private.article_id     = ""
flow.private.message = (
    "REJECTED BY EXPERT. Nothing was published. "
    f"Draft '{flow.input.title}' was discarded. No changes have been made."
)
""",
    )

    # ── Conditions branch ─────────────────────────────────────────────────
    decision_branch: Branch = aflow.conditions()
    decision_branch.condition(
        expression="flow.private.decision == 'confirmed'",
        to_node=publish_node,
    ).condition(
        default=True,
        to_node=rejected_result,
    )

    # ── Outer edges ────────────────────────────────────────────────────────
    aflow.edge(START, init_preview)
    aflow.edge(init_preview, user_flow)
    aflow.edge(user_flow, decision_branch)
    aflow.edge(publish_node, confirmed_result)
    aflow.edge(confirmed_result, END)
    aflow.edge(rejected_result, END)

    # ── Explicit output mapping — required to avoid auto_data_mapping failures ──
    # Pattern from flows/incident_triage/request_remediation.py (browser-verified).
    aflow.map_output(output_variable="decision",       expression="flow.private.decision")
    aflow.map_output(output_variable="title",          expression="flow.input.title")
    aflow.map_output(output_variable="action",         expression="flow.input.action")
    aflow.map_output(output_variable="article_id",     expression="flow.private.article_id")
    aflow.map_output(output_variable="live_in_kb",     expression="False")
    aflow.map_output(output_variable="publish_result", expression="flow.private.publish_result")
    aflow.map_output(output_variable="message",        expression="flow.private.message")

    return aflow

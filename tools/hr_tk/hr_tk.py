"""HR Tacit Knowledge tools for watsonx Orchestrate.

Read-only tools for the curator and guide agents.
Write tools (hr_tk_publish_article, hr_tk_notify_expert) are in this file
but are NOT attached to any agent — only the review and answer-gap flows call them.

Tool names are prefixed hr_tk_ to keep them unique across the WXO instance.
All data is fictional and static; nothing depends on today's date.
"""

import json
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import artifacts, articles, experts, employees
    from . import pii as pii_mod
except ImportError:
    from data import artifacts, articles, experts, employees
    import pii as pii_mod

_CHAR_CAP = 8000  # maximum characters returned in any tool output


def _error(code: str, message: str, hint: str) -> str:
    return json.dumps({"status": "error", "error_code": code, "message": message, "hint": hint},
                      indent=2)


def _cap(text: str) -> str:
    if len(text) <= _CHAR_CAP:
        return text
    return text[:_CHAR_CAP] + f"\n[... truncated to {_CHAR_CAP} characters]"


# ---------------------------------------------------------------------------
# Tool 1: hr_tk_list_new_artifacts
# ---------------------------------------------------------------------------
@tool
def hr_tk_list_new_artifacts() -> str:
    """List all harvested artifacts waiting for curator review.

    Use this first to see what has come in. Returns a short summary of each artifact
    (id, source, date, author role, title). Retrieve the full text with hr_tk_get_artifact.

    Returns:
        str: JSON list of artifact summaries, up to 10.
    """
    items = artifacts.list_new_artifacts()
    if not items:
        return json.dumps({"status": "none", "total": 0, "artifacts": []}, indent=2)
    return json.dumps({
        "status": "found",
        "total": len(items),
        "artifacts": [
            {
                "artifact_id": a["artifact_id"],
                "source": a["source"],
                "date": a["date"],
                "author_role": a["author_role"],
                "title": a["title"],
            }
            for a in items
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: hr_tk_get_artifact
# ---------------------------------------------------------------------------
@tool
def hr_tk_get_artifact(artifact_id: str) -> str:
    """Retrieve the full text and metadata of one harvested artifact.

    Use this after hr_tk_list_new_artifacts to read the content of a specific item.
    The text may contain PII; run hr_tk_scan_pii before drafting any article from it.

    Args:
        artifact_id (str): Artifact id such as 'A-101'.

    Returns:
        str: JSON with the full artifact record, or a structured error.
    """
    a = artifacts.get_artifact(artifact_id)
    if not a:
        return _error(
            "ARTIFACT_NOT_FOUND",
            f"Artifact '{artifact_id}' was not found.",
            f"Known artifact IDs: {', '.join(artifacts.artifact_ids())}.",
        )
    return json.dumps({"status": "found", "artifact": a}, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: hr_tk_scan_pii
# ---------------------------------------------------------------------------
@tool
def hr_tk_scan_pii(text: str) -> str:
    """Scan a text for personally identifiable information (PII).

    Use this on the full artifact text (or on a draft article body) before sending it
    to the expert for review. The scan is deterministic: it uses regex patterns and a
    fixed list of fictional names. It does not catch everything; the publish tool runs
    the same check again as a safety net.

    The findings include a 'suggestion' field with the redaction replacement. Paste the
    redacted text into your draft, then rewrite any awkward phrase in general terms.

    Args:
        text (str): The text to scan. Capped at 8000 characters. Returns up to 50 findings.

    Returns:
        str: JSON with clean (bool), findings list, and truncated flag.
    """
    if not (text or "").strip():
        return _error("EMPTY_TEXT", "No text was provided to scan.", "Pass the text to scan.")
    result = pii_mod.scan(text)
    return _cap(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Tool 4: hr_tk_find_related_articles
# ---------------------------------------------------------------------------
@tool
def hr_tk_find_related_articles(topic_keywords: str) -> str:
    """Search the KB article index for articles related to a set of topic keywords.

    Use this before drafting a NEW article to check whether a related article already
    exists (near-duplicate or update candidate). Requires at least two topic keyword hits
    before an article is considered related; avoids over-matching on single generic words.

    Args:
        topic_keywords (str): Space-separated keywords drawn from the artifact content,
            for example 'retroactive leave payroll correction'. Avoid single generic words
            such as 'form', 'manager' or 'email'.

    Returns:
        str: JSON with up to 3 matching articles (id, title, status, relevance score),
             or 'none' if nothing matches the threshold.
    """
    if not (topic_keywords or "").strip():
        return _error("EMPTY_QUERY", "topic_keywords must not be empty.",
                      "Pass at least one non-generic keyword from the artifact text.")

    # Stop-list: topics that are too generic to be meaningful in matching
    _GENERIC = {"form", "manager", "email", "process", "hr", "request", "change",
                "date", "record", "note", "ticket", "chat", "document", "portal",
                "employee", "team", "new", "update", "review"}

    words = [
        w.lower() for w in topic_keywords.strip().split()
        if w.lower() not in _GENERIC and len(w) > 2
    ]

    if not words:
        return json.dumps({"status": "none", "query": topic_keywords,
                           "reason": "all keywords were too generic", "articles": []}, indent=2)

    SCORE_THRESHOLD = 2  # require at least 2 topic hits

    scored: list[tuple[int, dict]] = []
    for art in articles.list_articles():
        score = sum(
            1 for topic in art["topics"]
            if any(w in topic.lower() for w in words)
        )
        if score >= SCORE_THRESHOLD:
            scored.append((score, art))

    scored.sort(key=lambda x: -x[0])
    top = scored[:3]

    if not top:
        return json.dumps({
            "status": "none",
            "query": topic_keywords,
            "articles": [],
        }, indent=2)

    return json.dumps({
        "status": "found",
        "query": topic_keywords,
        "total": len(top),
        "articles": [
            {
                "article_id": art["article_id"],
                "title": art["title"],
                "status": art["status"],
                "owner_role": art["owner_role"],
                "last_verified": art["last_verified"],
                "applies_to": art["applies_to"],
                "relevance_score": score,
                "successor_id": art.get("successor_id", None),
            }
            for score, art in top
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 5 (shared): hr_tk_find_expert
# ---------------------------------------------------------------------------
@tool
def hr_tk_find_expert(topic: str) -> str:
    """Find the right expert(s) for a given HR topic.

    Use this (a) in the curator, to identify who to notify for a draft review, and
    (b) in the guide, when the KB does not cover the learner's question and the question
    must be routed to a human expert.

    Args:
        topic (str): A description of the topic, for example 'retroactive leave correction'
            or 'work permit letter for a new employee'.

    Returns:
        str: JSON with up to 3 matching experts (id, name, role, topics),
             or a structured error if topic is empty.
    """
    if not (topic or "").strip():
        return _error("EMPTY_TOPIC", "topic must not be empty.",
                      "Describe the subject area to find the right expert.")

    found = experts.find_experts(topic)
    if not found:
        return json.dumps({
            "status": "none",
            "topic": topic,
            "message": "No expert matched this topic.",
            "known_expert_ids": experts.expert_ids(),
        }, indent=2)

    return json.dumps({
        "status": "found",
        "topic": topic,
        "total": len(found),
        "experts": [
            {
                "expert_id": e["expert_id"],
                "name": e["name"],
                "role": e["role"],
                "topics": e["topics"],
            }
            for e in found
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 6: hr_tk_get_employee_profile
# ---------------------------------------------------------------------------
@tool
def hr_tk_get_employee_profile(employee_id_or_name: str) -> str:
    """Retrieve a learner's profile: role, desk, tenure, and a brief description.

    Use this only when the question depends on who is asking — for example when the
    learner's role or desk determines which procedure applies. Do not call this tool
    for every question; call it only when the answer differs by role or tenure.

    Args:
        employee_id_or_name (str): Employee ID such as 'L-201', or a name.

    Returns:
        str: JSON with the employee profile, or a structured error.
    """
    matches = employees.find_employee_by_name(employee_id_or_name)
    if not matches:
        return _error(
            "EMPLOYEE_NOT_FOUND",
            f"No employee matches '{employee_id_or_name}'.",
            f"Known employee IDs: {', '.join(employees.employee_ids())}.",
        )
    if len(matches) > 1:
        return json.dumps({
            "status": "ambiguous",
            "message": f"{len(matches)} employees match '{employee_id_or_name}'. Please specify.",
            "candidates": [{"employee_id": e["employee_id"], "name": e["name"]} for e in matches],
        }, indent=2)
    return json.dumps({"status": "found", "employee": matches[0]}, indent=2)


# ---------------------------------------------------------------------------
# Tool 7 (write — flow only): hr_tk_publish_article
# ---------------------------------------------------------------------------
@tool
def hr_tk_publish_article(
    action: str,
    title: str,
    body: str,
    source_ids: str,
    author_role: str,
    verified_date: str,
    status: str,
    approver: str,
    applies_to: str,
    article_id: Optional[str] = "",
) -> str:
    """Write or update a KB article after expert review.

    RESTRICTED: this tool must only be called by hr_tk_review_draft or hr_tk_answer_gap
    after expert confirmation. It must never be attached to any agent.

    Governance rules enforced in code:
      - action must be 'new' or 'update'.
      - For 'update': article_id must name an existing article; a superseded article
        cannot be updated (ARTICLE_SUPERSEDED — use the successor instead).
      - title, body, source_ids, author_role, and approver must not be empty.
      - verified_date must be an ISO date (YYYY-MM-DD).
      - status must be 'current' or 'superseded'.
      - PII re-check on title + body: if any PII is found the tool refuses (PII_REMAINING).

    On success: returns the article_id, the target file path, the final formatted text,
    and live_in_kb: false (articles become searchable only after the next KB re-import).

    Args:
        action (str): 'new' to create a new article, 'update' to revise an existing one.
        title (str): Article title.
        body (str): Full article body text (PII must already be removed by the curator).
        source_ids (str): Comma-separated artifact IDs or document titles that sourced this article.
        author_role (str): Role label of the expert who owns the content.
        verified_date (str): ISO date (YYYY-MM-DD) when the expert verified the content.
        status (str): 'current' or 'superseded'.
        approver (str): Name or role label of the person who confirmed the draft.
        applies_to (str): Who this article applies to (e.g. 'Finland HR Coordinators').
        article_id (str): Required for 'update'. The ID of the article to revise.

    Returns:
        str: JSON with the article_id, file path, final text, live_in_kb flag, and message.
    """
    from datetime import date as _date_cls

    # Validate action
    act = (action or "").strip().lower()
    if act not in ("new", "update"):
        return _error("INVALID_ACTION",
                      f"action '{action}' is not valid.",
                      "Use 'new' to create a new article or 'update' to revise an existing one.")

    # Validate update target
    target_article = None
    if act == "update":
        aid = (article_id or "").strip().upper()
        if not aid:
            return _error("ARTICLE_NOT_FOUND",
                          "article_id is required for action 'update'.",
                          "Pass the ID of the article to update, e.g. 'HR-TK-ART-01'.")
        target_article = articles.get_article(aid)
        if not target_article:
            return _error("ARTICLE_NOT_FOUND",
                          f"Article '{aid}' does not exist in the seeded article set.",
                          f"Known article IDs: {', '.join(articles.article_ids())}.")
        if target_article["status"] == "superseded":
            successor = target_article.get("successor_id", "")
            hint = (f"Update the successor article '{successor}' instead."
                    if successor else "Create a new article instead.")
            return _error("ARTICLE_SUPERSEDED",
                          f"Article '{aid}' is superseded and cannot be updated.",
                          hint)

    # Required field checks
    def _blank(v):
        return not (v or "").strip()

    if _blank(title):
        return _error("MISSING_METADATA", "title must not be empty.",
                      "Provide a descriptive article title.")
    if _blank(body):
        return _error("MISSING_METADATA", "body must not be empty.",
                      "Provide the full article text.")
    if _blank(source_ids):
        return _error("MISSING_METADATA", "source_ids must not be empty.",
                      "List the artifact IDs or document titles that sourced this article.")
    if _blank(author_role):
        return _error("MISSING_METADATA", "author_role must not be empty.",
                      "State the role of the expert who owns the content.")
    if _blank(approver):
        return _error("MISSING_METADATA", "approver must not be empty.",
                      "State who confirmed the draft.")

    # Validated ISO date
    vd = (verified_date or "").strip()
    try:
        _date_cls.fromisoformat(vd)
        if len(vd) != 10:
            raise ValueError
    except ValueError:
        return _error("MISSING_METADATA",
                      f"verified_date '{verified_date}' is not a valid ISO date.",
                      "Use 'YYYY-MM-DD', for example 2025-06-01.")

    # Status check
    st = (status or "").strip().lower()
    if st not in ("current", "superseded"):
        return _error("MISSING_METADATA",
                      f"status '{status}' is not valid.",
                      "Use 'current' for a live article or 'superseded' for a retired one.")

    # PII re-check
    combined = title + "\n" + body
    pii_result = pii_mod.scan(combined)
    if not pii_result["clean"]:
        count = len(pii_result["findings"])
        return _error("PII_REMAINING",
                      f"PII check failed: {count} finding(s) remain in the title and body.",
                      "Run hr_tk_scan_pii on the draft, apply the suggested redactions, "
                      "rewrite any awkward phrases in general terms, and resubmit.")

    # Determine article ID
    if act == "new":
        new_id = articles.next_article_id()
    else:
        new_id = target_article["article_id"]

    # Format the final article text
    applies = (applies_to or "").strip() or "All HR staff"
    final_text = (
        f"ARTICLE ID: {new_id}\n"
        f"TITLE: {title.strip()}\n"
        f"STATUS: {st}\n"
        f"OWNER ROLE: {author_role.strip()}\n"
        f"LAST VERIFIED: {vd}\n"
        f"APPLIES TO: {applies}\n"
        f"APPROVED BY: {approver.strip()}\n"
        f"SOURCES: {source_ids.strip()}\n"
        f"\n"
        f"{body.strip()}\n"
    )

    target_path = (
        f"knowledge/hr-tacit-knowledge/articles/{new_id}.txt"
    )

    return json.dumps({
        "status": "success",
        "article_id": new_id,
        "action": act,
        "file_path": target_path,
        "live_in_kb": False,
        "next_step": (
            "The article text is returned in 'final_text'. "
            "Approved drafts must be saved to knowledge/hr-tacit-knowledge/articles/ "
            "and the KB re-imported before they are searchable. "
            "The publish tool does NOT write to disk automatically."
        ),
        "final_text": final_text,
        "message": (
            f"APPROVED AND RECORDED. Article {new_id} ({act}): '{title.strip()}'. "
            f"Approved by {approver.strip()}. "
            f"NOTE: the article is NOT yet searchable in the KB. "
            f"To make it searchable, save it to {target_path} and re-import the KB."
        ),
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 8 (write — flow only): hr_tk_notify_expert
# ---------------------------------------------------------------------------
@tool
def hr_tk_notify_expert(expert_id: str, subject: str, message: str) -> str:
    """Send a notification to an expert. Mock: returns simulated, nothing is delivered.

    RESTRICTED: this tool must only be called by hr_tk_review_draft or hr_tk_answer_gap.
    It must never be attached to any agent.

    In a real deployment this would send an email or Teams message. In this demo it
    records the notification as simulated and returns immediately.

    Args:
        expert_id (str): Expert ID such as 'X-101'.
        subject (str): Notification subject.
        message (str): Notification body. Must not be empty.

    Returns:
        str: JSON with simulated: true, delivered: false, and a note.
    """
    eid = (expert_id or "").strip().upper()
    if not eid:
        return _error("EXPERT_NOT_FOUND", "expert_id must not be empty.",
                      f"Known expert IDs: {', '.join(experts.expert_ids())}.")
    expert = experts.get_expert(eid)
    if not expert:
        return _error("EXPERT_NOT_FOUND",
                      f"Expert '{expert_id}' does not exist.",
                      f"Known expert IDs: {', '.join(experts.expert_ids())}.")
    if not (message or "").strip():
        return _error("EMPTY_MESSAGE", "message must not be empty.",
                      "Provide the notification body.")

    return json.dumps({
        "status": "success",
        "simulated": True,
        "delivered": False,
        "expert_id": eid,
        "expert_name": expert["name"],
        "expert_email": expert["email"],
        "subject": (subject or "").strip(),
        "note": (
            "This is a simulated notification. In this demo, no message is actually sent. "
            "A real deployment would integrate with email or a messaging platform."
        ),
    }, indent=2)

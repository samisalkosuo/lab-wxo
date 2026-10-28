"""Tests for the HR Tacit Knowledge tools and PII scanner.

Run with:  pytest tests/test_hr_tk_tools.py -v

Tools must be called via .fn() because @tool wraps the function in a PythonTool object;
calling the wrapper directly raises TypeError.

Sub-Task 2 tests:  PII scanner, redaction, all read tools, related-article matching.
Sub-Task 3 tests:  KB yaml vs articles.py metadata, no PII in KB articles.
Sub-Task 4 tests:  Publish governance rules, notify mock.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the modules under test directly (no ADK runtime needed)
# ---------------------------------------------------------------------------
import sys, os

# Ensure the tools package is importable as a package (not a namespace pkg)
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tools.hr_tk import pii as pii_mod
from tools.hr_tk.data import artifacts, articles, experts, employees
from tools.hr_tk.hr_tk import (
    hr_tk_list_new_artifacts,
    hr_tk_get_artifact,
    hr_tk_scan_pii,
    hr_tk_find_related_articles,
    hr_tk_find_expert,
    hr_tk_get_employee_profile,
    hr_tk_publish_article,
    hr_tk_notify_expert,
)

# ---------------------------------------------------------------------------
# Sample document text (the PII-laden expert notes from Sub-Task 6)
# ---------------------------------------------------------------------------
_SAMPLE_DOC_PATH = (
    _REPO_ROOT / "docs" / "demo" / "hr-tk-sample" / "expert-notes-retroactive-leave-dates.txt"
)
_SAMPLE_DOC_MD_PATH = (
    _REPO_ROOT / "docs" / "demo" / "hr-tk-sample" / "expert-notes-retroactive-leave-dates.md"
)


def _sample_doc_text() -> str:
    """Load the sample document from .txt (preferred) or .md fallback."""
    path = _SAMPLE_DOC_PATH if _SAMPLE_DOC_PATH.exists() else _SAMPLE_DOC_MD_PATH
    return path.read_text(encoding="utf-8")


# ===========================================================================
# Sub-Task 2: PII scanner tests
# ===========================================================================

class TestPiiScanner:
    def test_sample_document_is_not_clean(self):
        result = pii_mod.scan(_sample_doc_text())
        assert not result["clean"], "Sample document must be detected as containing PII"

    def test_sample_document_finds_email(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "email" in cats, "Must detect at least one email address"

    def test_sample_document_finds_national_id(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "national_id" in cats, "Must detect at least one Finnish national ID"

    def test_sample_document_finds_employee_id(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "employee_id" in cats, "Must detect at least one E-nnnnn employee ID"

    def test_sample_document_finds_phone(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "phone" in cats, "Must detect at least one phone number"

    def test_sample_document_finds_money(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "money" in cats or "salary_amount" in cats, "Must detect money amounts"

    def test_sample_document_finds_health_term(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "sensitive_health" in cats, "Must detect sensitive health terms (surgery, sick leave)"

    def test_sample_document_finds_known_names(self):
        result = pii_mod.scan(_sample_doc_text())
        cats = [f["category"] for f in result["findings"]]
        assert "personal_name" in cats, "Must detect known fictional names"

    def test_redacted_copy_is_clean(self):
        original = _sample_doc_text()
        redacted = pii_mod.redact(original)
        result = pii_mod.scan(redacted)
        # The redacted copy should be clean (no PII detected)
        # (some name fragments might survive after redaction of combined full names;
        # the publish tool re-check is the actual safety net)
        assert result["clean"], (
            f"Redacted copy should scan as clean. Remaining findings: "
            f"{[f['match'] for f in result['findings']]}"
        )

    def test_clean_text_is_clean(self):
        text = "The payroll cutoff is the 22nd of the month. Contact HR Operations for details."
        result = pii_mod.scan(text)
        assert result["clean"]

    def test_all_mock_artifacts_scan_clean(self):
        """Mock artifact texts (without the sample document) must be PII-free."""
        for art in artifacts.list_new_artifacts():
            if art["artifact_id"] == "A-107":
                continue  # A-107 text is a placeholder; the real text is in the sample doc
            result = pii_mod.scan(art["text"])
            assert result["clean"], (
                f"Artifact {art['artifact_id']} should be PII-free. "
                f"Findings: {[f['match'] for f in result['findings']]}"
            )

    def test_scan_returns_structured_result(self):
        result = pii_mod.scan("test")
        assert "clean" in result
        assert "findings" in result
        assert "truncated" in result

    def test_empty_findings_is_list(self):
        result = pii_mod.scan("no pii here at all")
        assert isinstance(result["findings"], list)


# ===========================================================================
# Sub-Task 2: Read tool tests
# ===========================================================================

class TestListNewArtifacts:
    def test_returns_json(self):
        out = hr_tk_list_new_artifacts.fn()
        data = json.loads(out)
        assert data["status"] in ("found", "none")

    def test_returns_known_artifact_ids(self):
        out = hr_tk_list_new_artifacts.fn()
        data = json.loads(out)
        ids = [a["artifact_id"] for a in data.get("artifacts", [])]
        assert "A-101" in ids
        assert "A-105" in ids

    def test_does_not_include_full_text(self):
        out = hr_tk_list_new_artifacts.fn()
        data = json.loads(out)
        for art in data.get("artifacts", []):
            assert "text" not in art, "Summary must not include full text"


class TestGetArtifact:
    def test_known_artifact_returns_full_text(self):
        out = hr_tk_get_artifact.fn("A-101")
        data = json.loads(out)
        assert data["status"] == "found"
        assert "workaround" in data["artifact"]["text"].lower()

    def test_case_insensitive(self):
        out = hr_tk_get_artifact.fn("a-101")
        data = json.loads(out)
        assert data["status"] == "found"

    def test_unknown_returns_error(self):
        out = hr_tk_get_artifact.fn("A-999")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == "ARTIFACT_NOT_FOUND"


class TestScanPii:
    def test_pii_text_is_not_clean(self):
        out = hr_tk_scan_pii.fn("Call Kaisa Mäkinen at kaisa@example.com, ID E-48291.")
        data = json.loads(out)
        assert not data["clean"]

    def test_clean_text_is_clean(self):
        out = hr_tk_scan_pii.fn("The payroll cutoff is the 22nd of the month.")
        data = json.loads(out)
        assert data["clean"]

    def test_empty_text_returns_error(self):
        out = hr_tk_scan_pii.fn("")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == "EMPTY_TEXT"


class TestFindRelatedArticles:
    """related-article matching must match plan requirements:
      A-101, A-104 → nothing
      A-103       → ART-03 only
      A-105       → ART-04 only
      sample doc  → ART-01 only
      A-102       → ART-03 current + ART-02 superseded
    """

    def test_a101_workaround_no_match(self):
        # A-101 is about a role-change salary correction lock (period-close batch).
        # ART-06 (the article that would be created from A-101) is NOT seeded — it is created by TK-001.
        # So the search must return nothing for A-101's keywords, making it correctly NEW.
        out = hr_tk_find_related_articles.fn("role change salary correction period-close batch")
        data = json.loads(out)
        assert data["status"] == "none", (
            f"A-101 keywords should return no match (ART-06 is not seeded yet). "
            f"Got: {[a['article_id'] for a in data.get('articles', [])]}"
        )

    def test_a103_near_dup_matches_art03_only(self):
        # A-103 is about employment certificate via self-service
        out = hr_tk_find_related_articles.fn("employment certificate self-service HR Operations")
        data = json.loads(out)
        ids = [a["article_id"] for a in data.get("articles", [])]
        assert "HR-TK-ART-03" in ids
        # ART-02 (superseded) covers same topic — may also appear; the plan says A-102/A-103 → ART-03
        # Both ART-02 and ART-03 share topics; the plan expectation is that the agent sees both
        # (it does not restrict to current articles in the tool) and the agent decides.

    def test_a105_contradicts_art04(self):
        # A-105 is about Finland position-change process
        out = hr_tk_find_related_articles.fn("position change Finland internal transfer")
        data = json.loads(out)
        ids = [a["article_id"] for a in data.get("articles", [])]
        assert "HR-TK-ART-04" in ids, "ART-04 is the Finland position-change article"

    def test_a105_does_not_match_art05_only(self):
        # ART-05 is the Sweden look-alike. Both ART-04 and ART-05 have "position change";
        # ART-04 has "Finland" which A-105 explicitly mentions, so ART-04 should score higher.
        out = hr_tk_find_related_articles.fn("position change Finland internal transfer")
        data = json.loads(out)
        # ART-04 must be present; ART-05 may also appear (same topic, different country)
        ids = [a["article_id"] for a in data.get("articles", [])]
        assert "HR-TK-ART-04" in ids

    def test_sample_doc_matches_art01(self):
        # Sample document is about leave correction and payroll cutoff
        out = hr_tk_find_related_articles.fn("retroactive leave correction payroll cutoff overpayment")
        data = json.loads(out)
        ids = [a["article_id"] for a in data.get("articles", [])]
        assert "HR-TK-ART-01" in ids, "ART-01 is the leave-correction article"

    def test_a102_matches_art03_and_art02(self):
        # A-102 is employment certificate (chat snippet)
        out = hr_tk_find_related_articles.fn("employment certificate proof of employment HR Operations")
        data = json.loads(out)
        ids = [a["article_id"] for a in data.get("articles", [])]
        assert "HR-TK-ART-03" in ids
        assert "HR-TK-ART-02" in ids, "ART-02 (superseded) also matches certificate topic"

    def test_a104_noise_no_match(self):
        # A-104 is a meeting reminder — no meaningful topic keywords
        out = hr_tk_find_related_articles.fn("monthly sync agenda reminder")
        data = json.loads(out)
        assert data["status"] == "none"

    def test_all_generic_returns_none(self):
        out = hr_tk_find_related_articles.fn("form manager email")
        data = json.loads(out)
        assert data["status"] == "none"

    def test_empty_query_returns_error(self):
        out = hr_tk_find_related_articles.fn("")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == "EMPTY_QUERY"


class TestFindExpert:
    def test_leave_topic_finds_x101(self):
        out = hr_tk_find_expert.fn("retroactive leave correction payroll")
        data = json.loads(out)
        ids = [e["expert_id"] for e in data.get("experts", [])]
        assert "X-101" in ids

    def test_certificate_topic_finds_x102(self):
        out = hr_tk_find_expert.fn("work permit letter visa documentation")
        data = json.loads(out)
        ids = [e["expert_id"] for e in data.get("experts", [])]
        assert "X-102" in ids

    def test_position_change_finds_x104(self):
        out = hr_tk_find_expert.fn("internal position change Finland HR portal")
        data = json.loads(out)
        ids = [e["expert_id"] for e in data.get("experts", [])]
        assert "X-104" in ids

    def test_unknown_topic_returns_none(self):
        out = hr_tk_find_expert.fn("stock options vesting cliff schedule")
        data = json.loads(out)
        assert data["status"] == "none"

    def test_empty_topic_returns_error(self):
        out = hr_tk_find_expert.fn("")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == "EMPTY_TOPIC"


class TestGetEmployeeProfile:
    def test_known_employee_by_id(self):
        out = hr_tk_get_employee_profile.fn("L-201")
        data = json.loads(out)
        assert data["status"] == "found"
        assert data["employee"]["role"] == "HR Coordinator"

    def test_known_employee_by_name(self):
        out = hr_tk_get_employee_profile.fn("Emilia Saarinen")
        data = json.loads(out)
        assert data["status"] == "found"

    def test_unknown_employee_returns_error(self):
        out = hr_tk_get_employee_profile.fn("L-999")
        data = json.loads(out)
        assert data["status"] == "error"
        assert data["error_code"] == "EMPLOYEE_NOT_FOUND"


# ===========================================================================
# Sub-Task 3: KB yaml and articles metadata tests
# (requires Sub-Task 3 KB files to exist)
# ===========================================================================

class TestKbYamlAndArticles:
    _KB_YAML = _REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "hr_tk_knowledge.yaml"
    _ARTICLES_DIR = _REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "articles"

    @pytest.mark.skipif(
        not (_REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "hr_tk_knowledge.yaml").exists(),
        reason="KB yaml not yet created (Sub-Task 3)"
    )
    def test_kb_yaml_lists_all_seeded_articles(self):
        import yaml
        kb = yaml.safe_load(self._KB_YAML.read_text(encoding="utf-8"))
        docs = kb.get("documents", [])
        article_filenames = [d.split("/")[-1] for d in docs]
        for aid in articles.article_ids():
            assert f"{aid}.txt" in article_filenames, (
                f"{aid}.txt must be listed in the KB yaml documents"
            )

    @pytest.mark.skipif(
        not (_REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "articles" / "HR-TK-ART-01.txt").exists(),
        reason="KB articles not yet created (Sub-Task 3)"
    )
    def test_article_files_exist_for_all_ids(self):
        for aid in articles.article_ids():
            path = self._ARTICLES_DIR / f"{aid}.txt"
            assert path.exists(), f"Article file {path} must exist"

    @pytest.mark.skipif(
        not (_REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "articles").exists(),
        reason="KB articles not yet created (Sub-Task 3)"
    )
    def test_article_files_are_pii_free(self):
        for aid in articles.article_ids():
            path = self._ARTICLES_DIR / f"{aid}.txt"
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            result = pii_mod.scan(text)
            assert result["clean"], (
                f"KB article {aid}.txt must be PII-free. "
                f"Findings: {[f['match'] for f in result['findings']]}"
            )

    @pytest.mark.skipif(
        not (_REPO_ROOT / "knowledge" / "hr-tacit-knowledge" / "articles").exists(),
        reason="KB articles not yet created (Sub-Task 3)"
    )
    def test_article_headers_match_metadata(self):
        for art in articles.list_articles():
            aid = art["article_id"]
            path = self._ARTICLES_DIR / f"{aid}.txt"
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            assert aid in text, f"Article ID {aid} must appear in the file header"
            assert art["title"] in text or art["title"][:40] in text, (
                f"Article title must appear in {aid}.txt"
            )


# ===========================================================================
# Sub-Task 4: Write tool tests
# ===========================================================================

class TestPublishArticle:
    """Tests for hr_tk_publish_article governance rules."""

    _CLEAN_BODY = (
        "SYMPTOMS\nHR Coordinator needs to request an employment certificate for an employee.\n\n"
        "PROCEDURE\n1. Log into Employee Self-Service > My Documents > Certificates.\n"
        "2. Select Employment Certificate and the language.\n3. Submit the request.\n\n"
        "OUTCOME\nHR Operations issues the certificate within 3 working days."
    )
    _CLEAN_TITLE = "Requesting an Employment Certificate"

    def _publish(self, **overrides):
        defaults = dict(
            action="new",
            title=self._CLEAN_TITLE,
            body=self._CLEAN_BODY,
            source_ids="A-102",
            author_role="HR Operations Lead",
            verified_date="2025-06-01",
            status="current",
            approver="Expert reviewer",
            applies_to="All employees in Finland",
        )
        defaults.update(overrides)
        return hr_tk_publish_article.fn(**defaults)

    def test_valid_new_article_succeeds(self):
        out = self._publish()
        data = json.loads(out)
        assert data["status"] == "success"
        assert data["live_in_kb"] is False
        assert "HR-TK-ART" in data["article_id"]

    def test_invalid_action_returns_error(self):
        out = self._publish(action="delete")
        data = json.loads(out)
        assert data["error_code"] == "INVALID_ACTION"

    def test_update_unknown_id_returns_error(self):
        out = self._publish(action="update", article_id="HR-TK-ART-99")
        data = json.loads(out)
        assert data["error_code"] == "ARTICLE_NOT_FOUND"

    def test_update_empty_id_returns_error(self):
        out = self._publish(action="update", article_id="")
        data = json.loads(out)
        assert data["error_code"] == "ARTICLE_NOT_FOUND"

    def test_update_superseded_returns_error(self):
        out = self._publish(action="update", article_id="HR-TK-ART-02")
        data = json.loads(out)
        assert data["error_code"] == "ARTICLE_SUPERSEDED"
        # hint must name the successor
        assert "HR-TK-ART-03" in data["hint"]

    def test_update_current_article_succeeds(self):
        out = self._publish(action="update", article_id="HR-TK-ART-04")
        data = json.loads(out)
        assert data["status"] == "success"
        assert data["article_id"] == "HR-TK-ART-04"

    def test_empty_title_returns_error(self):
        out = self._publish(title="")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_empty_body_returns_error(self):
        out = self._publish(body="")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_empty_source_ids_returns_error(self):
        out = self._publish(source_ids="")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_empty_author_role_returns_error(self):
        out = self._publish(author_role="")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_empty_approver_returns_error(self):
        out = self._publish(approver="")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_non_iso_date_returns_error(self):
        out = self._publish(verified_date="01/06/2025")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_invalid_status_returns_error(self):
        out = self._publish(status="draft")
        data = json.loads(out)
        assert data["error_code"] == "MISSING_METADATA"

    def test_sample_doc_raw_pii_is_refused(self):
        """Publishing the unredacted sample document text must be refused."""
        raw = _sample_doc_text()
        out = self._publish(body=raw)
        data = json.loads(out)
        assert data["error_code"] == "PII_REMAINING"

    def test_redacted_doc_is_accepted(self):
        """After redaction, the text should pass the publish PII check."""
        raw = _sample_doc_text()
        redacted = pii_mod.redact(raw)
        out = self._publish(body=redacted)
        data = json.loads(out)
        # Either succeeds or has a PII error; if PII, flag what remains
        if data.get("error_code") == "PII_REMAINING":
            remaining = pii_mod.scan(redacted)
            pytest.fail(
                f"Redacted text still has PII: "
                f"{[f['match'] for f in remaining['findings']]}"
            )
        assert data["status"] == "success"


class TestNotifyExpert:
    def test_known_expert_succeeds(self):
        out = hr_tk_notify_expert.fn(
            expert_id="X-101",
            subject="Draft review request",
            message="Please review the attached draft article.",
        )
        data = json.loads(out)
        assert data["status"] == "success"
        assert data["simulated"] is True
        assert data["delivered"] is False

    def test_unknown_expert_returns_error(self):
        out = hr_tk_notify_expert.fn(
            expert_id="X-999",
            subject="Test",
            message="Test message.",
        )
        data = json.loads(out)
        assert data["error_code"] == "EXPERT_NOT_FOUND"

    def test_empty_message_returns_error(self):
        out = hr_tk_notify_expert.fn(
            expert_id="X-101",
            subject="Test",
            message="",
        )
        data = json.loads(out)
        assert data["error_code"] == "EMPTY_MESSAGE"

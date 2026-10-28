"""Deterministic PII scanner for the HR Tacit Knowledge scenario.

Detects PII in text using regex patterns and a fixed list of fictional names
that appear in the demo data. Returns a structured result with findings and
suggested redactions. Pure function, no state.

Patterns covered:
  - E-mail addresses (generic)
  - Finnish and Nordic national ID numbers (DDMMYY-NNNC or DDMMYYANNC)
  - Employee IDs (E-nnnnn)
  - Phone numbers (+358..., international, local with extension NNNN)
  - Money amounts (€NNN, NNN EUR, NNN euros)
  - Health/medical sensitive terms
  - Known fictional names from the demo PII document
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, str, str]] = [
    # (category, regex_pattern, redact_template)
    (
        "email",
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        "[EMAIL REDACTED]",
    ),
    (
        "national_id",
        # Finnish / Nordic: DDMMYY[-+A]NNNC  (with or without the separator variants)
        r"\b\d{6}[-+A]\d{3}[0-9A-Za-z]\b",
        "[NATIONAL ID REDACTED]",
    ),
    (
        "employee_id",
        r"\bE-\d{4,6}\b",
        "[EMPLOYEE ID REDACTED]",
    ),
    (
        "phone",
        # International: +<country> digits (spaces / dashes optional)
        r"\+\d[\d\s\-]{6,14}\d",
        "[PHONE REDACTED]",
    ),
    (
        "phone_extension",
        # "extension NNNN" or "ext. NNNN" or "ext NNNN"
        r"(?i)\bext(?:ension)?\.?\s+\d{3,6}\b",
        "[PHONE REDACTED]",
    ),
    (
        "money",
        # €NNN or NNN EUR or NNN euros (including decimals and thousands separators)
        r"(?:€\s?\d[\d\s,.']*(?:\.\d{1,2})?|\d[\d\s,.']*\s*(?:EUR|euros?))\b",
        "[AMOUNT REDACTED]",
    ),
    (
        "salary_amount",
        # "salary of NNN" or "gross NNN" patterns
        r"(?i)\b(?:salary|gross|overpayment|net pay)\s+(?:of\s+)?[\d,.]+",
        "[AMOUNT REDACTED]",
    ),
]

# Sensitive health / medical terms that, when they appear next to a name, flag
# a sensitive category. We redact the whole surrounding clause.
_HEALTH_TERMS = [
    "medical leave",
    "sick leave",
    "surgery",
    "surgical",
    "hospital",
    "health condition",
    "mental health",
    "disability",
    "maternity leave",
    "paternity leave",
]

# Known fictional names in the demo PII document.
# Use full names only — single first/last names are too prone to false positives
# and cause redaction loops when both "Kaisa Mäkinen" and "Kaisa" are in the list.
_KNOWN_NAMES = [
    "Kaisa Mäkinen",
    "Tero Virtanen",
    "Sanna Lehtinen",
    "Eero Salonen",
    # Expert names (should not appear in published articles)
    "Maarit Virtanen",
    "Janne Korhonen",
    "Aino Mäkinen",
    "Petri Leinonen",
]

# Maximum number of findings to return
_MAX_FINDINGS = 50
# Maximum text length to scan (the scan is O(n*patterns))
_MAX_SCAN_CHARS = 8000


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan(text: str) -> dict[str, Any]:
    """Scan text for PII.  Returns::

        {
            "clean": bool,
            "findings": [
                {
                    "category": str,
                    "match": str,        # the matched substring
                    "start": int,        # character offset in (truncated) text
                    "end": int,
                    "suggestion": str,   # suggested replacement
                },
                ...
            ],
            "truncated": bool,           # True if input > _MAX_SCAN_CHARS
        }
    """
    truncated = len(text) > _MAX_SCAN_CHARS
    chunk = text[:_MAX_SCAN_CHARS]

    findings: list[dict] = []

    # Regex patterns
    for category, pattern, suggestion in _PATTERNS:
        for m in re.finditer(pattern, chunk):
            findings.append({
                "category": category,
                "match": m.group(0),
                "start": m.start(),
                "end": m.end(),
                "suggestion": suggestion,
            })
            if len(findings) >= _MAX_FINDINGS:
                break
        if len(findings) >= _MAX_FINDINGS:
            break

    # Health-term detection: flag whole line
    if len(findings) < _MAX_FINDINGS:
        for term in _HEALTH_TERMS:
            pattern_obj = re.compile(rf"(?i)(?:[^\n]*\b{re.escape(term)}\b[^\n]*)")
            for m in pattern_obj.finditer(chunk):
                findings.append({
                    "category": "sensitive_health",
                    "match": m.group(0)[:120],
                    "start": m.start(),
                    "end": m.end(),
                    "suggestion": "[HEALTH INFORMATION REDACTED]",
                })
                if len(findings) >= _MAX_FINDINGS:
                    break
            if len(findings) >= _MAX_FINDINGS:
                break

    # Known names
    if len(findings) < _MAX_FINDINGS:
        for name in _KNOWN_NAMES:
            # Match whole word / phrase, case-insensitive
            escaped = re.escape(name)
            # For multi-word names, allow flexible whitespace
            if " " in name:
                escaped = r"\s+".join(re.escape(p) for p in name.split())
            for m in re.finditer(rf"(?i)\b{escaped}\b", chunk):
                findings.append({
                    "category": "personal_name",
                    "match": m.group(0),
                    "start": m.start(),
                    "end": m.end(),
                    "suggestion": "[NAME REDACTED]",
                })
                if len(findings) >= _MAX_FINDINGS:
                    break
            if len(findings) >= _MAX_FINDINGS:
                break

    # Deduplicate overlapping findings (keep the earlier one)
    findings = _deduplicate(findings)

    return {
        "clean": len(findings) == 0,
        "findings": findings[:_MAX_FINDINGS],
        "truncated": truncated,
    }


def redact(text: str) -> str:
    """Return a copy of text with all detected PII replaced by the suggestion strings."""
    result = scan(text)
    # Apply replacements from end to start so offsets stay valid
    chunk = text[:_MAX_SCAN_CHARS]
    for finding in sorted(result["findings"], key=lambda f: -f["start"]):
        chunk = chunk[: finding["start"]] + finding["suggestion"] + chunk[finding["end"]:]
    # Append any tail that was not scanned
    return chunk + text[_MAX_SCAN_CHARS:]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deduplicate(findings: list[dict]) -> list[dict]:
    """Remove findings whose character ranges overlap a finding that started earlier."""
    kept: list[dict] = []
    for f in sorted(findings, key=lambda x: (x["start"], -x["end"])):
        if any(k["start"] <= f["start"] < k["end"] for k in kept):
            continue
        kept.append(f)
    return kept

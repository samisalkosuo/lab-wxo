"""Deterministic (regex-based) entity extraction for the entity_extractor agent.

Covers the entities that follow a recognisable format: email addresses, URLs, phone numbers,
dates, monetary amounts, percentages and identifiers (IBAN, UUID, IPv4, labelled reference
numbers). Semantic entities (person, organization, location, product, ...) are left to the
agent's language model.
"""

import re
from datetime import date
from typing import List, Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

PATTERN_ENTITY_TYPES = [
    "email_address",
    "url",
    "date",
    "monetary_amount",
    "percentage",
    "phone_number",
    "identifier",
]

_MONTHS = {
    m: i + 1
    for i, names in enumerate(
        [
            ("january", "jan"),
            ("february", "feb"),
            ("march", "mar"),
            ("april", "apr"),
            ("may",),
            ("june", "jun"),
            ("july", "jul"),
            ("august", "aug"),
            ("september", "sep", "sept"),
            ("october", "oct"),
            ("november", "nov"),
            ("december", "dec"),
        ]
    )
    for m in names
}
_MONTH_RE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\.?"

_CURRENCY_CODES = "EUR|USD|GBP|SEK|NOK|DKK|CHF|JPY|CNY|INR|CAD|AUD"
_NUM = r"(?:\d{1,3}(?:[ ,.\u00a0]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
_SCALE = r"(?:\s?(?:thousand|million|billion|bn|k|m)\b)?"

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>\"')\]]+[^\s<>\"')\].,;:!?]")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
_LABELLED_ID_RE = re.compile(
    r"\b(?:invoice|order|ticket|case|reference|ref|account|customer|employee|policy|claim|"
    r"tracking|serial|passport|VAT|PO|ID)\b\s*(?:no\.?|number|#|id|code)?\s*[:#]?\s*"
    r"(?P<id>(?=[A-Za-z0-9-]*\d)[A-Za-z0-9][A-Za-z0-9-]{2,})",
    re.I,
)
_BARE_ID_RE = re.compile(r"\b[A-Z]{2,6}-\d{2,}(?:-\d+)*\b|\b\d{7}-\d\b")

_DATE_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DATE_NUM_RE = re.compile(r"\b(\d{1,2})([./])(\d{1,2})\2(\d{4})\b")
_DATE_DMY_RE = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_RE})\s*,?\s*(\d{{4}})\b", re.I)
_DATE_MDY_RE = re.compile(rf"\b({_MONTH_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(\d{{4}})\b", re.I)
_DATE_MY_RE = re.compile(rf"\b({_MONTH_RE})\s+(\d{{4}})\b", re.I)

_MONEY_PREFIX_RE = re.compile(rf"(?P<cur>[$€£¥]|\b(?:{_CURRENCY_CODES})\b)\s?(?P<num>{_NUM}){_SCALE}")
_MONEY_SUFFIX_RE = re.compile(
    rf"(?P<num>{_NUM}){_SCALE}\s?(?P<cur>[$€£¥]|\b(?:{_CURRENCY_CODES})\b|\b(?:euros?|dollars?|pounds?)\b)",
    re.I,
)
_PERCENT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:%|percent\b|per cent\b)")

_PHONE_PLUS_RE = re.compile(r"(?<![\w+])\+\d[\d\s().-]{6,18}\d")
_PHONE_PLAIN_RE = re.compile(r"(?<![\w.,/-])\(?\d{2,4}\)?(?:[\s.-]\d{2,4}){2,4}(?![\w/-])")

_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "euro": "EUR", "euros": "EUR",
            "dollar": "USD", "dollars": "USD", "pound": "GBP", "pounds": "GBP"}


def _to_number(raw: str) -> Optional[float]:
    s = raw.replace("\u00a0", " ").strip()
    if re.fullmatch(r"\d{1,3}(?:[ ,.]\d{3})+", s):
        return float(re.sub(r"[ ,.]", "", s))
    if re.fullmatch(r"\d{1,3}(?:[ .]\d{3})+,\d{1,2}", s):
        return float(s.replace(".", "").replace(" ", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:[ ,]\d{3})+\.\d{1,2}", s):
        return float(s.replace(",", "").replace(" ", ""))
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def _scale_of(match_text: str) -> float:
    m = re.search(r"(thousand|million|billion|bn|k|m)\b", match_text, re.I)
    if not m:
        return 1.0
    return {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9}[m.group(1).lower()]


def _iso(year: int, month: int, day: int) -> Optional[str]:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _month(name: str) -> Optional[int]:
    return _MONTHS.get(name.lower().rstrip("."))


def _collect(text: str, wanted: set) -> list:
    """Return non-overlapping hits as dicts with type/text/start/end (+ optional extras)."""
    hits: list = []

    def free(s: int, e: int) -> bool:
        return all(e <= h["start"] or s >= h["end"] for h in hits)

    # Every type claims its span (wanted or not) so that, e.g., an IBAN is never reported as a
    # phone number. Earlier patterns win overlaps; unwanted types are filtered out at the end.
    def claim(kind: str, s: int, e: int, **extra) -> None:
        if free(s, e):
            hits.append({"type": kind, "text": text[s:e], "start": s, "end": e, **extra})

    for m in _EMAIL_RE.finditer(text):
        claim("email_address", m.start(), m.end())
    for m in _URL_RE.finditer(text):
        claim("url", m.start(), m.end())
    for rx, label in ((_UUID_RE, "uuid"), (_IBAN_RE, "iban"), (_IPV4_RE, "ipv4")):
        for m in rx.finditer(text):
            claim("identifier", m.start(), m.end(), id_kind=label)

    for m in _DATE_ISO_RE.finditer(text):
        claim("date", m.start(), m.end(), normalized=_iso(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in _DATE_NUM_RE.finditer(text):
        day, sep, mon, year = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
        # dd.mm.yyyy is unambiguous day-first; with "/" only normalise when one reading is impossible.
        norm = None
        if sep == "." or day > 12:
            norm = _iso(year, mon, day)
        elif mon > 12:
            norm = _iso(year, day, mon)
        claim("date", m.start(), m.end(), normalized=norm)
    for m in _DATE_DMY_RE.finditer(text):
        mon = _month(m.group(2))
        claim("date", m.start(), m.end(), normalized=_iso(int(m.group(3)), mon, int(m.group(1))) if mon else None)
    for m in _DATE_MDY_RE.finditer(text):
        mon = _month(m.group(1))
        claim("date", m.start(), m.end(), normalized=_iso(int(m.group(3)), mon, int(m.group(2))) if mon else None)
    for m in _DATE_MY_RE.finditer(text):
        claim("date", m.start(), m.end(), normalized=None)

    for rx in (_MONEY_PREFIX_RE, _MONEY_SUFFIX_RE):
        for m in rx.finditer(text):
            cur = m.group("cur")
            code = _SYMBOLS.get(cur.lower(), _SYMBOLS.get(cur, cur.upper()))
            num = _to_number(m.group("num"))
            claim(
                "monetary_amount",
                m.start(),
                m.end(),
                normalized={"amount": None if num is None else num * _scale_of(m.group(0)), "currency": code},
            )
    for m in _PERCENT_RE.finditer(text):
        claim("percentage", m.start(), m.end())

    for rx in (_PHONE_PLUS_RE, _PHONE_PLAIN_RE):
        for m in rx.finditer(text):
            digits = re.sub(r"\D", "", m.group(0))
            if 7 <= len(digits) <= 15:
                claim("phone_number", m.start(), m.end())

    for m in _LABELLED_ID_RE.finditer(text):
        claim("identifier", m.start("id"), m.end("id"), id_kind="labelled")
    for m in _BARE_ID_RE.finditer(text):
        claim("identifier", m.start(), m.end(), id_kind="code")

    return [h for h in hits if h["type"] in wanted]


@tool
def extract_pattern_entities(text: str, entity_types: Optional[List[str]] = None) -> dict:
    """
    Deterministically extract format-based entities from text using regular expressions.
    Call this tool for every extraction request that includes any of these entity types:
    email_address, url, date, monetary_amount, percentage, phone_number, identifier.
    It does not find people, organizations, locations, products or custom entities.

    Args:
        text (str): The full source text to scan, exactly as the user provided it.
        entity_types (Optional[List[str]]): Entity types to extract, chosen from email_address,
            url, date, monetary_amount, percentage, phone_number, identifier. Omit or pass an
            empty list to extract all of them.

    Returns:
        dict: {"entities": {<entity_type>: [{"text", ...}]}, "scanned_types": [...]}.
            Every scanned type is present, with an empty list when nothing was found. "date" hits
            may carry "normalized" (ISO date or null), "monetary_amount" hits carry "normalized"
            ({"amount", "currency"}), and "identifier" hits carry "id_kind".
    """
    wanted = {t.strip().lower() for t in (entity_types or []) if t and t.strip()} or set(PATTERN_ENTITY_TYPES)
    wanted &= set(PATTERN_ENTITY_TYPES)
    hits = _collect(text or "", wanted)
    result = {t: [] for t in PATTERN_ENTITY_TYPES if t in wanted}
    for h in sorted(hits, key=lambda x: x["start"]):
        item = {k: v for k, v in h.items() if k not in ("type", "start", "end") and v is not None}
        result[h["type"]].append(item)
    return {"entities": result, "scanned_types": sorted(wanted)}

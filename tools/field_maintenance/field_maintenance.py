"""Field maintenance tools for watsonx Orchestrate (mock Maximo backend).

Seven deterministic, read-only tools over a static mock plant, plus one mock write tool
(mx_write_work_log) that is NOT attached to the agent: only the mx_submit_work_log flow
calls it, after the technician approves the draft.

Field names follow IBM Maximo (ASSETNUM, WONUM, WORKTYPE, STATUS, FAILURECODE, PMNUM, ITEMNUM).
In real life only the bodies of these tools change (Maximo REST/OSLC calls); the agent,
flow and knowledge base stay the same. Nothing here talks to a real Maximo.
"""

import hashlib
import json
import re
from datetime import date, timedelta
from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import assets, inventory, meters, pm_schedules, work_orders
except ImportError:
    from data import assets, inventory, meters, pm_schedules, work_orders


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "its", "has", "have", "need", "needs",
    "check", "looks", "look", "inside", "something", "wrong", "keeps", "again", "very",
    "from", "into", "onto", "our", "are", "was", "not", "but", "can", "got", "get",
}


def _err(code: str, message: str, hint: str) -> str:
    return json.dumps({"status": "error", "error_code": code, "message": message, "hint": hint}, indent=2)


def _clean_id(value: Optional[str]) -> str:
    return value.strip().upper() if value else ""


def _asset_or_error(assetnum: Optional[str]):
    """Return (asset, None) or (None, error_json)."""
    clean = _clean_id(assetnum)
    asset = assets.get_asset(clean)
    if asset:
        return asset, None
    return None, _err(
        "ASSET_NOT_FOUND",
        f"Asset '{assetnum}' not found.",
        "Use mx_find_asset with the technician's description to get a valid ASSETNUM. "
        f"Known ASSETNUMs: {', '.join(assets.asset_ids())}.",
    )


def _terms(text: str) -> set:
    """Lower-case word tokens plus adjacent-pair compounds ('line' + '2' -> 'line2')."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    terms = set()
    for w in words:
        if w not in _STOPWORDS and (len(w) >= 3 or w.isdigit()):
            terms.add(w)
    for a, b in zip(words, words[1:]):
        terms.add(a + b)
    return terms


# ---------------------------------------------------------------------------
# Tool 1: mx_find_asset
# ---------------------------------------------------------------------------
@tool
def mx_find_asset(description: str, location: Optional[str] = None) -> str:
    """Finds candidate assets in the maintenance system (Maximo) from a technician's free-text description.

    Use this FIRST when the technician names an asset loosely (for example "cooling pump on line 2",
    "conveyor motor 4", "tank 12", "something in the boiler room"). It returns up to 5 candidates
    ranked by match, with operating status and criticality. If several candidates tie and more than
    one is operating, 'ambiguous' is true: ask the technician one question. If only one tied
    candidate is operating, 'ambiguous' is false: use it and say which others were ignored and why.

    Args:
        description (str): Free-text asset description or fault report, e.g. 'cooling pump line 2'.
        location (str, optional): Location code or name to narrow the search, e.g. 'LINE2' or 'Boiler Room'.

    Returns:
        str: JSON with 'candidates' (assetnum, description, location, operating_status, criticality,
            score), an 'ambiguous' flag and a 'resolution_note'. When several assets match equally but
            only one is OPERATING, 'ambiguous' is false and the note names it. An error object with a
            hint if nothing matches.
    """
    if not description or not description.strip():
        return _err("EMPTY_DESCRIPTION", "No description given.",
                    "Pass the technician's words, e.g. 'cooling pump on line 2'.")

    loc_filter = None
    if location and location.strip():
        loc_terms = _terms(location) - {"room", "hall", "yard"}
        for code, name in assets.LOCATIONS.items():
            if code.lower() in loc_terms or (_terms(name) - {"room", "hall", "yard"}) & loc_terms:
                loc_filter = code
                break
        if loc_filter is None:
            return _err("UNKNOWN_LOCATION", f"Location '{location}' not recognised.",
                        f"Known locations: {', '.join(f'{c} ({n})' for c, n in assets.LOCATIONS.items())}.")

    query = _terms(description)
    scored = []
    for a in assets.ASSETS.values():
        if loc_filter and a["location"] != loc_filter:
            continue
        kw = set(a["keywords"])
        desc_terms = _terms(a["description"])
        loc_terms_a = _terms(assets.LOCATIONS[a["location"]])
        score = 0
        for t in query:
            if t in kw:
                score += 2
            if t in desc_terms:
                score += 1
            if t in loc_terms_a:
                score += 1
        if score > 0:
            scored.append((score, a))

    if not scored:
        return _err("NO_MATCH", f"No asset matches '{description}'.",
                    "Ask the technician for the equipment type and area, or an ASSETNUM / tag number.")

    # Higher score first; on ties, OPERATING assets before STANDBY, then by ASSETNUM.
    scored.sort(key=lambda s: (-s[0], s[1]["operating_status"] != "OPERATING", s[1]["assetnum"]))
    top = scored[:5]
    best = top[0][0]
    tied = [s for s in top if s[0] == best]
    # A fault report is about a running asset: if exactly one tied candidate is OPERATING
    # (the rest are standby or out of service), it is the match, not an ambiguity.
    tied_operating = [s for s in tied if s[1]["operating_status"] == "OPERATING"]
    ambiguous = len(tied) > 1 and len(tied_operating) != 1
    note = ""
    if len(tied) > 1 and not ambiguous:
        chosen = tied_operating[0][1]["assetnum"]
        others = ", ".join(
            f"{a['assetnum']} ({a['operating_status']})" for _, a in tied if a["assetnum"] != chosen
        )
        note = (
            f"{chosen} is the only matching asset in OPERATING status; the other match(es) "
            f"are not running: {others}. Proceed with {chosen} and say so."
        )
    return json.dumps({
        "status": "ok",
        "ambiguous": ambiguous,
        "resolution_note": note,
        "candidates": [
            {
                "assetnum": a["assetnum"],
                "description": a["description"],
                "location": f"{a['location']} ({assets.LOCATIONS[a['location']]})",
                "operating_status": a["operating_status"],
                "criticality": a["criticality"],
                "score": s,
            }
            for s, a in top
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: mx_get_asset
# ---------------------------------------------------------------------------
@tool
def mx_get_asset(assetnum: str) -> str:
    """Retrieves the maintenance-system (Maximo) record of one asset by ASSETNUM.

    Use this after mx_find_asset to read the location, operating status, criticality (1 = highest)
    and hazard class (rotating_equipment, electrical, confined_space). The hazard class tells you
    which safety procedure applies (lockout/tagout, electrical work, confined-space permit).

    Args:
        assetnum (str): Asset number, e.g. 'PUMP-L2-03'. Case-insensitive.

    Returns:
        str: JSON asset record, or an error object listing valid ASSETNUMs.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    return json.dumps({
        "status": "ok",
        "assetnum": asset["assetnum"],
        "description": asset["description"],
        "location": f"{asset['location']} ({assets.LOCATIONS[asset['location']]})",
        "operating_status": asset["operating_status"],
        "criticality": asset["criticality"],
        "hazard_class": asset["hazard_class"],
        "model": asset["model"],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: mx_get_work_order_history
# ---------------------------------------------------------------------------
@tool
def mx_get_work_order_history(assetnum: str, months: int = 12) -> str:
    """Lists the CLOSED work orders of an asset in the last N months, with failure codes.

    Use this to see whether the same fault happened before. The result includes a
    'repeat_failures' list: failure codes that occurred two or more times in the window.
    Open work orders are not included; use mx_list_open_work_orders for those.

    Args:
        assetnum (str): Asset number, e.g. 'PUMP-L2-03'.
        months (int): Look-back window in months (1 to 36). Default 12.

    Returns:
        str: JSON with up to 10 closed work orders (newest first) and 'repeat_failures'.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    if not isinstance(months, int) or months < 1 or months > 36:
        return _err("INVALID_MONTHS", f"months must be 1 to 36, got {months!r}.", "Use 12 for a one-year history.")

    cutoff = date.fromisoformat(assets.TODAY) - timedelta(days=30 * months)
    closed = [
        w for w in work_orders.by_asset(asset["assetnum"])
        if w["status"] == "CLOSE" and date.fromisoformat(w["reportdate"]) >= cutoff
    ]
    closed.sort(key=lambda w: w["reportdate"], reverse=True)

    counts = {}
    for w in closed:
        if w["failurecode"]:
            counts[w["failurecode"]] = counts.get(w["failurecode"], 0) + 1
    repeats = [
        {"failurecode": code, "occurrences": n}
        for code, n in sorted(counts.items()) if n >= 2
    ]
    return json.dumps({
        "status": "ok",
        "assetnum": asset["assetnum"],
        "window_months": months,
        "closed_work_orders": [
            {k: w[k] for k in ("wonum", "worktype", "description", "failurecode", "reportdate", "actfinish", "notes")}
            for w in closed[:10]
        ],
        "repeat_failures": repeats,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: mx_list_open_work_orders
# ---------------------------------------------------------------------------
@tool
def mx_list_open_work_orders(assetnum: str) -> str:
    """Lists OPEN work orders (waiting approval, approved, waiting material, in progress) for an asset.

    Use this before proposing any new work: if an open work order already covers the reported
    fault, add the work log to that WONUM instead of creating a duplicate.

    Args:
        assetnum (str): Asset number, e.g. 'MTR-CV-04'.

    Returns:
        str: JSON with 'open_work_orders' (wonum, worktype, status, description, failurecode,
            reportdate, notes). Empty list if none.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    open_wos = [w for w in work_orders.by_asset(asset["assetnum"]) if w["status"] in work_orders.OPEN_STATUSES]
    return json.dumps({
        "status": "ok",
        "assetnum": asset["assetnum"],
        "open_work_orders": [
            {k: w[k] for k in ("wonum", "worktype", "status", "description", "failurecode", "reportdate", "notes")}
            for w in open_wos
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: mx_get_pm_schedule
# ---------------------------------------------------------------------------
@tool
def mx_get_pm_schedule(assetnum: str) -> str:
    """Retrieves the preventive maintenance (PM) schedule of an asset and whether a PM is overdue.

    Args:
        assetnum (str): Asset number, e.g. 'MTR-CV-04'.

    Returns:
        str: JSON with PM records (pmnum, description, frequency_days, last_done, next_due,
            overdue, days_overdue). Empty list if the asset has no PM.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    today = date.fromisoformat(assets.TODAY)
    records = []
    for p in pm_schedules.by_asset(asset["assetnum"]):
        days_over = (today - date.fromisoformat(p["next_due"])).days
        records.append({
            **p,
            "overdue": days_over > 0,
            "days_overdue": max(days_over, 0),
        })
    return json.dumps({"status": "ok", "assetnum": asset["assetnum"], "as_of": assets.TODAY, "pm_schedules": records}, indent=2)


# ---------------------------------------------------------------------------
# Tool 6: mx_check_spares
# ---------------------------------------------------------------------------
@tool
def mx_check_spares(assetnum: str) -> str:
    """Checks stock of the spare parts normally used on an asset (Maximo inventory).

    Use this when a repair is likely, to tell the technician which parts are on hand,
    where they are (storeroom and bin), and which are out of stock with an expected date.

    Args:
        assetnum (str): Asset number, e.g. 'PUMP-L2-03'.

    Returns:
        str: JSON with 'parts' (itemnum, description, qty_on_hand, storeroom, bin, in_stock, eta).
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    parts = []
    for itemnum in inventory.ASSET_PARTS.get(asset["assetnum"], []):
        item = inventory.ITEMS[itemnum]
        parts.append({**item, "in_stock": item["qty_on_hand"] > 0})
    return json.dumps({
        "status": "ok",
        "assetnum": asset["assetnum"],
        "parts": parts,
        "note": "" if parts else "No spare parts are registered for this asset.",
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 7: mx_get_meter_readings
# ---------------------------------------------------------------------------
@tool
def mx_get_meter_readings(assetnum: str, metric: Optional[str] = None) -> str:
    """Reads the latest condition-monitoring values (vibration, temperature, current, ...) of an asset.

    Use this to check a technician's report ("it is vibrating and hot") against data. Each metric
    returns the latest value, warning and alarm thresholds, a status (normal, warning, alarm) and
    a 24-hour trend. A standby asset with normal values does not support a fault report.

    Args:
        assetnum (str): Asset number, e.g. 'PUMP-L2-03'.
        metric (str, optional): One metric name, e.g. 'vibration_mm_s' or 'bearing_temp_c'. If omitted, all metrics.

    Returns:
        str: JSON with readings per metric, or an error object listing the metrics the asset has.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    available = meters.METERS.get(asset["assetnum"], {})
    if not available:
        return json.dumps({"status": "ok", "assetnum": asset["assetnum"], "readings": {},
                           "note": "No meters registered for this asset."}, indent=2)
    chosen = available
    if metric and metric.strip():
        key = metric.strip().lower()
        if key not in available:
            return _err("UNKNOWN_METRIC", f"Asset {asset['assetnum']} has no metric '{metric}'.",
                        f"Available metrics: {', '.join(available)}. Or omit metric for all.")
        chosen = {key: available[key]}

    readings = {}
    for name, m in chosen.items():
        latest = m["latest"]
        state = "alarm" if latest >= m["alarm"] else "warning" if latest >= m["warn"] else "normal"
        readings[name] = {
            "unit": m["unit"], "latest": latest, "warning_at": m["warn"], "alarm_at": m["alarm"],
            "status": state, "trend_24h": m["trend_24h"],
        }
    return json.dumps({"status": "ok", "assetnum": asset["assetnum"],
                       "operating_status": asset["operating_status"], "readings": readings}, indent=2)


# ---------------------------------------------------------------------------
# Tool 8: mx_write_work_log (mock write tool for the approval flow ONLY)
# ---------------------------------------------------------------------------
@tool
def mx_write_work_log(
    assetnum: str,
    log_text: str,
    wonum: Optional[str] = None,
    followup_request: Optional[str] = None,
    sop_refs: Optional[str] = None,
) -> str:
    """Writes a work log to the maintenance system (Maximo), optionally with a follow-up service request.

    NOTE: This is a restricted write tool for use exclusively by the mx_submit_work_log approval flow.
    It must NOT be called directly by an agent without the technician's approval.

    If wonum is given, the log is added to that OPEN work order (it must belong to the asset).
    If wonum is empty, a new corrective work order is created for the asset with the log.
    Nothing is persisted: this is a mock that returns deterministic identifiers.

    Args:
        assetnum (str): Asset number the work was done on.
        log_text (str): The work log text.
        wonum (str, optional): Existing open work order number to add the log to.
        followup_request (str, optional): If set, a follow-up service request is created with this text.
        sop_refs (str, optional): Comma-separated procedure IDs followed, e.g. 'SOP-PUMP-01,SOP-LOTO-01'.

    Returns:
        str: JSON with the work order, work log id and optional service request id, or an error object.
    """
    asset, err = _asset_or_error(assetnum)
    if err:
        return err
    if not log_text or not log_text.strip():
        return _err("EMPTY_LOG", "Work log text is empty.", "Provide the drafted work log text.")

    target_wo = _clean_id(wonum)
    created_new = False
    if target_wo:
        wo = work_orders.get_work_order(target_wo)
        if wo is None:
            return _err("WORKORDER_NOT_FOUND", f"Work order '{wonum}' not found.",
                        "Use mx_list_open_work_orders for this asset to get a valid WONUM, or leave it empty to create one.")
        if wo["assetnum"] != asset["assetnum"]:
            return _err("WORKORDER_ASSET_MISMATCH",
                        f"Work order {target_wo} belongs to asset {wo['assetnum']}, not {asset['assetnum']}.",
                        f"Use a WONUM that belongs to {asset['assetnum']}, or leave it empty to create a new one.")
        if wo["status"] not in work_orders.OPEN_STATUSES:
            return _err("WORKORDER_NOT_OPEN", f"Work order {target_wo} is {wo['status']}, not open.",
                        "Logs can only be added to open work orders. Leave wonum empty to create a new one.")
    else:
        seed = hashlib.sha1(f"{asset['assetnum']}|{log_text}".encode()).hexdigest()
        target_wo = f"WO-{int(seed[:6], 16) % 90000 + 10000 + 1000000 // 100}"
        created_new = True

    seed = hashlib.sha1(f"{target_wo}|{log_text}".encode()).hexdigest()
    result = {
        "status": "ok",
        "assetnum": asset["assetnum"],
        "wonum": target_wo,
        "work_order_created": created_new,
        "worklog_id": f"WL-{int(seed[:6], 16) % 90000 + 10000}",
        "sop_refs": [s.strip() for s in (sop_refs or "").split(",") if s.strip()],
        "service_request": None,
        "note": "MOCK: nothing was written to a real Maximo.",
    }
    if followup_request and followup_request.strip():
        sr_seed = hashlib.sha1(f"{asset['assetnum']}|{followup_request}".encode()).hexdigest()
        result["service_request"] = {"ticketid": f"SR-{int(sr_seed[:6], 16) % 9000 + 1000}", "text": followup_request.strip()}
    return json.dumps(result, indent=2)

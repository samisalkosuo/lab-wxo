"""Direct check of the field_maintenance mock tools (no agent involved).

Run: python tests/check_field_maintenance_tools.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "field_maintenance"))
import field_maintenance as fm  # noqa: E402


def call(tool_obj, *a, **k):
    fn = getattr(tool_obj, "__wrapped__", None) or getattr(tool_obj, "fn", None) or tool_obj
    return json.loads(fn(*a, **k))


def top(res):
    return [c["assetnum"] for c in res["candidates"]]


def main():
    ok = 0

    def check(cond, label):
        nonlocal ok
        assert cond, f"FAILED: {label}"
        ok += 1

    # FM-001: resolve pump, no ambiguity with standby (operating wins) -> but both match; check ranking
    r = call(fm.mx_find_asset, "cooling pump on line 2 is vibrating and hot")
    check(top(r)[0] == "PUMP-L2-03", "FM-001 operating pump ranked first")
    check("PUMP-L2-04" in top(r), "FM-001 standby pump is a candidate (red herring)")
    check(r["ambiguous"] is False, "FM-001 not ambiguous: only one matching pump is OPERATING")
    check("PUMP-L2-03" in r["resolution_note"] and "PUMP-L2-04 (STANDBY)" in r["resolution_note"],
          "FM-001 resolution note names the chosen pump and the standby one")

    r = call(fm.mx_get_meter_readings, "PUMP-L2-03")
    check(r["readings"]["vibration_mm_s"]["status"] == "alarm", "P-203 vibration alarm")
    check(r["readings"]["bearing_temp_c"]["status"] == "alarm", "P-203 bearing temp alarm")
    r = call(fm.mx_get_meter_readings, "PUMP-L2-04")
    check(all(m["status"] == "normal" for m in r["readings"].values()), "P-204 readings normal")

    r = call(fm.mx_get_work_order_history, "PUMP-L2-03", 12)
    check(r["repeat_failures"] == [{"failurecode": "BRG-WEAR", "occurrences": 2}], "P-203 repeat BRG-WEAR x2")
    r = call(fm.mx_get_work_order_history, "PUMP-L2-04", 12)
    check(r["repeat_failures"] == [] and r["closed_work_orders"][0]["failurecode"] == "SEAL-LEAK", "P-204 seal leak, no repeat")

    r = call(fm.mx_check_spares, "PUMP-L2-03")
    stock = {p["itemnum"]: p["in_stock"] for p in r["parts"]}
    check(stock["BRG-6310"] and not stock["CPL-INS-14"], "bearing in stock, coupling insert out of stock")

    # FM-002
    r = call(fm.mx_find_asset, "conveyor motor 4 keeps tripping")
    check(top(r)[0] == "MTR-CV-04", "FM-002 conveyor motor found")
    r = call(fm.mx_list_open_work_orders, "MTR-CV-04")
    check([w["wonum"] for w in r["open_work_orders"]] == ["WO-11002"], "FM-002 existing open WO-11002")
    r = call(fm.mx_get_pm_schedule, "MTR-CV-04")
    check(r["pm_schedules"][0]["overdue"] and r["pm_schedules"][0]["days_overdue"] > 0, "FM-002 PM overdue")
    r = call(fm.mx_get_meter_readings, "MTR-CV-04", "motor_current_a")
    check(r["readings"]["motor_current_a"]["status"] == "alarm", "FM-002 current above alarm")

    # FM-003
    r = call(fm.mx_find_asset, "check the valve inside tank 12")
    check(top(r)[0] == "TNK-12", "FM-003 tank found")
    r = call(fm.mx_get_asset, "TNK-12")
    check(r["hazard_class"] == "confined_space", "FM-003 confined space hazard")

    # FM-004: vague boiler room -> ambiguous
    r = call(fm.mx_find_asset, "something is wrong in the boiler room")
    check(r["ambiguous"] and len(r["candidates"]) >= 3, "FM-004 ambiguous boiler room")
    check({"BLR-01", "BLR-02", "BLR-03"} <= set(top(r)), "FM-004 all boiler assets listed")
    r = call(fm.mx_find_asset, "pump", "Boiler Room")
    check(top(r) == ["BLR-01"], "location filter narrows to boiler feedwater pump")

    # error paths
    check(call(fm.mx_get_asset, "NOPE")["error_code"] == "ASSET_NOT_FOUND", "asset not found error")
    check("hint" in call(fm.mx_find_asset, "zzzz qqqq"), "no match has hint")
    check(call(fm.mx_find_asset, "pump", "Mars")["error_code"] == "UNKNOWN_LOCATION", "unknown location")
    check(call(fm.mx_get_work_order_history, "PUMP-L2-03", 99)["error_code"] == "INVALID_MONTHS", "bad months")
    check(call(fm.mx_get_meter_readings, "PUMP-L2-03", "pressure")["error_code"] == "UNKNOWN_METRIC", "bad metric")

    # write tool
    r = call(fm.mx_write_work_log, "MTR-CV-04", "Checked contactor", "WO-11002")
    check(r["wonum"] == "WO-11002" and not r["work_order_created"], "log added to existing WO")
    r = call(fm.mx_write_work_log, "PUMP-L2-03", "Mismatch", "WO-11002")
    check(r["error_code"] == "WORKORDER_ASSET_MISMATCH", "wrong asset/WONUM rejected")
    r = call(fm.mx_write_work_log, "PUMP-L2-03", "Old wo", "WO-10234")
    check(r["error_code"] == "WORKORDER_NOT_OPEN", "closed WO rejected")
    r = call(fm.mx_write_work_log, "PUMP-L2-03", "Bearing check", "", "Review alignment practice", "SOP-PUMP-01, SOP-LOTO-01")
    check(r["work_order_created"] and r["service_request"]["ticketid"].startswith("SR-"), "new WO + service request")
    check(r["sop_refs"] == ["SOP-PUMP-01", "SOP-LOTO-01"], "sop refs parsed")
    check(call(fm.mx_write_work_log, "PUMP-L2-03", "  ")["error_code"] == "EMPTY_LOG", "empty log rejected")

    print(f"OK: {ok} checks passed")


if __name__ == "__main__":
    main()

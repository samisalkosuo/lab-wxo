"""Customer Returns tools for watsonx Orchestrate.

Read-only tools the agent uses to investigate return requests.
The write tool (returns_issue_refund) is in this file but is NOT attached to
the agent -- only the returns_process_return flow calls it after human approval.

Tool names are prefixed returns_ to guarantee uniqueness across the WXO instance.
"""

from __future__ import annotations

import json
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import orders, warranties, return_history, products
except ImportError:
    from data import orders, warranties, return_history, products

# Reference date used for all age / expiry calculations (mock "today")
_REF_DATE = "2025-06-03"
_NO_REASON_WINDOW_DAYS = 30


# ---------------------------------------------------------------------------
# Tool 1: returns_lookup_order
# ---------------------------------------------------------------------------
@tool
def returns_lookup_order(order_id: str) -> str:
    """Look up an order by its order ID to retrieve product, purchase date, and customer details.

    Use this tool when the customer provides an order ID (e.g. 'ORD-1001').
    It returns the product, purchase date, channel, and age in days relative
    to the current date, which determines eligibility for the 30-day no-reason return window.

    Args:
        order_id (str): The order identifier, e.g. 'ORD-1001'. Case-insensitive.

    Returns:
        str: Structured order details including product, purchase date, age in days,
             and channel. Returns a structured error with valid IDs if not found.
    """
    clean_id = order_id.strip().upper() if order_id else ""
    order = orders.get_order(clean_id)
    if not order:
        valid = orders.get_order_ids()
        return json.dumps({
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order '{order_id}' not found.",
            "hint": f"Known order IDs: {', '.join(valid)}.",
        }, indent=2)

    age_days = orders.get_order_age_days(clean_id, _REF_DATE)
    within_window = age_days is not None and age_days <= _NO_REASON_WINDOW_DAYS

    result = {
        "status": "found",
        "order_id": order["order_id"],
        "customer_id": order["customer_id"],
        "customer_name": order["customer_name"],
        "product_sku": order["product_sku"],
        "product_name": order["product_name"],
        "quantity": order["quantity"],
        "unit_price_eur": order["unit_price_eur"],
        "purchase_date": order["purchase_date"],
        "age_days": age_days,
        "within_30_day_window": within_window,
        "purchase_channel": order["purchase_channel"],
        "delivery_status": order["status"],
        "notes": order["notes"],
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: returns_check_warranty
# ---------------------------------------------------------------------------
@tool
def returns_check_warranty(order_id: str) -> str:
    """Check whether the product in a given order has an active manufacturer warranty.

    Use this tool when the customer reports a defect or broken product.
    An active warranty makes the item eligible for replacement even outside
    the 30-day no-reason return window.

    Note: there may be multiple warranty records for the same customer (different SKUs).
    Always verify that the warranty matches the specific order and SKU being discussed.

    Args:
        order_id (str): The order ID to check warranty coverage for, e.g. 'ORD-1001'.

    Returns:
        str: Warranty details including serial number, SKU, expiry, and coverage,
             or a structured result indicating no warranty is on file.
    """
    clean_id = order_id.strip().upper() if order_id else ""
    order = orders.get_order(clean_id)
    if not order:
        valid = orders.get_order_ids()
        return json.dumps({
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order '{order_id}' not found.",
            "hint": f"Known order IDs: {', '.join(valid)}.",
        }, indent=2)

    warranties_for_order = warranties.get_warranties_by_order(clean_id)
    if not warranties_for_order:
        return json.dumps({
            "status": "no_warranty",
            "order_id": clean_id,
            "product_sku": order["product_sku"],
            "message": "No warranty record found for this order.",
        }, indent=2)

    records = []
    for w in warranties_for_order:
        active = warranties.is_warranty_active(w["serial_number"], _REF_DATE)
        records.append({
            "serial_number": w["serial_number"],
            "product_sku": w["product_sku"],
            "product_name": w["product_name"],
            "warranty_type": w["warranty_type"],
            "warranty_start": w["warranty_start"],
            "warranty_end": w["warranty_end"],
            "status": w["status"],
            "is_active": active,
            "coverage": w["coverage"],
        })

    return json.dumps({
        "status": "found",
        "order_id": clean_id,
        "warranties": records,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: returns_get_return_history
# ---------------------------------------------------------------------------
@tool
def returns_get_return_history(order_id: str) -> str:
    """Check whether a return request has already been filed for a given order.

    Use this tool to avoid creating duplicate return requests and to inform
    the customer of the current status of a prior request.

    Args:
        order_id (str): The order ID to check, e.g. 'ORD-1001'.

    Returns:
        str: The most recent return record for this order, or a message
             indicating no prior return has been filed.
    """
    clean_id = order_id.strip().upper() if order_id else ""
    record = return_history.get_return_by_order(clean_id)
    if not record:
        return json.dumps({
            "status": "no_prior_return",
            "order_id": clean_id,
            "message": "No return request has been filed for this order.",
        }, indent=2)
    return json.dumps({"status": "found", "return_record": record}, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: returns_lookup_by_serial
# ---------------------------------------------------------------------------
@tool
def returns_lookup_by_serial(serial_number: str) -> str:
    """Look up an order by product serial number, for customers who received a gift and have no order ID.

    Use this tool when the customer provides a serial number from the product
    packaging or device but does not have an order confirmation.

    Args:
        serial_number (str): The product serial number, e.g. 'SN-KTCH-780-C103'.

    Returns:
        str: The linked order ID, product details, and purchase date, or a structured
             error with example serial number format if not found.
    """
    clean_sn = serial_number.strip().upper() if serial_number else ""
    product = products.get_product_by_serial(clean_sn)
    if not product:
        examples = products.get_serial_numbers()[:3]
        return json.dumps({
            "status": "error",
            "error_code": "SERIAL_NOT_FOUND",
            "message": f"Serial number '{serial_number}' not found in the product registry.",
            "hint": (
                "Serial numbers are printed on the product packaging and the device label. "
                f"Example format: {examples[0] if examples else 'SN-XXXX-NNNNN'}."
            ),
        }, indent=2)

    order = orders.get_order(product["order_id"])
    age_days = orders.get_order_age_days(product["order_id"], _REF_DATE) if order else None
    within_window = age_days is not None and age_days <= _NO_REASON_WINDOW_DAYS

    return json.dumps({
        "status": "found",
        "serial_number": clean_sn,
        "product_sku": product["product_sku"],
        "product_name": product["product_name"],
        "linked_order_id": product["order_id"],
        "purchase_date": product["purchase_date"],
        "purchase_channel": product["purchase_channel"],
        "age_days": age_days,
        "within_30_day_window": within_window,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: returns_list_orders
# ---------------------------------------------------------------------------
@tool
def returns_list_orders() -> str:
    """List all orders available in the demo system so the user can identify their order ID.

    Use this tool when the user says they do not know their order ID, asks to 'show my
    orders', 'list orders', or similar. This is a demo convenience tool — in a real system
    this would require customer authentication.

    Returns:
        str: A Markdown table of all orders with order ID, product name, purchase date,
             purchase channel, and delivery status.
    """
    all_orders = orders.list_all_orders()
    lines = [
        "| Order ID | Product | Purchase Date | Channel | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for o in all_orders:
        lines.append(
            f"| `{o['order_id']}` | {o['product_name']} | {o['purchase_date']} "
            f"| {o['purchase_channel']} | {o['status']} |"
        )
    lines.append("\nPlease provide the order ID you would like to return.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 6 (write — flow only): returns_issue_refund
# ---------------------------------------------------------------------------
@tool
def returns_issue_refund(
    order_id: str,
    customer_id: str,
    refund_reason: str,
    refund_type: str,
) -> str:
    """Issue a refund or replacement for an approved return request.

    RESTRICTED: This tool must only be called by the returns_process_return flow
    after human approval. It must never be attached to an agent directly.

    The tool validates that the order_id belongs to customer_id before proceeding
    (Rule 7: validate in code what a prompt cannot guarantee).

    Args:
        order_id (str): The order to refund, e.g. 'ORD-1001'.
        customer_id (str): The customer ID; must match the order's customer_id.
        refund_reason (str): One of: 'defect', 'no_reason', 'gift_return', 'warranty_claim'.
        refund_type (str): One of: 'full_refund', 'replacement', 'store_credit'.

    Returns:
        str: Structured confirmation with a generated refund reference and next steps,
             or a structured error if validation fails.
    """
    import hashlib

    clean_order = order_id.strip().upper() if order_id else ""
    clean_cust = customer_id.strip().upper() if customer_id else ""

    order = orders.get_order(clean_order)
    if not order:
        return json.dumps({
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"Order '{order_id}' not found.",
        }, indent=2)

    # Rule 7: validate ownership before issuing
    if order["customer_id"] != clean_cust:
        return json.dumps({
            "status": "error",
            "error_code": "CUSTOMER_MISMATCH",
            "message": (
                f"Order '{clean_order}' belongs to customer '{order['customer_id']}', "
                f"not '{clean_cust}'. Refund not issued."
            ),
        }, indent=2)

    valid_reasons = ["defect", "no_reason", "gift_return", "warranty_claim"]
    valid_types = ["full_refund", "replacement", "store_credit"]
    if refund_reason not in valid_reasons:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_REASON",
            "message": f"refund_reason must be one of: {', '.join(valid_reasons)}.",
        }, indent=2)
    if refund_type not in valid_types:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_TYPE",
            "message": f"refund_type must be one of: {', '.join(valid_types)}.",
        }, indent=2)

    # Deterministic refund reference
    seed = f"{clean_order}_{clean_cust}_{refund_reason}_{refund_type}".encode()
    ref_num = int(hashlib.md5(seed).hexdigest()[:5], 16) % 90000 + 10000
    refund_ref = f"REF-{ref_num}"

    amount = order["unit_price_eur"] if refund_type == "full_refund" else 0.0
    next_steps = {
        "full_refund": f"€{amount:.2f} will be credited to the original payment method within 5-7 business days.",
        "replacement": f"A replacement {order['product_name']} will be shipped within 3-5 business days.",
        "store_credit": f"€{order['unit_price_eur']:.2f} store credit has been added to the account.",
    }

    result = {
        "status": "success",
        "refund_reference": refund_ref,
        "order_id": clean_order,
        "customer_id": clean_cust,
        "product_name": order["product_name"],
        "refund_reason": refund_reason,
        "refund_type": refund_type,
        "amount_eur": amount if refund_type == "full_refund" else None,
        "processed_at": "2025-06-03T10:00:00Z",
        "next_steps": next_steps[refund_type],
        "message": (
            f"APPROVED AND PROCESSED. Refund reference: {refund_ref}. "
            f"Order: {clean_order}, Product: {order['product_name']}. "
            f"Type: {refund_type}. {next_steps[refund_type]}"
        ),
    }
    return json.dumps(result, indent=2)

from datetime import datetime


def build_variables(
    request_data: dict,
    item_data: dict,
    seller_data: dict | None,
    fulfillment_path: str,
) -> dict:
    """Build the 15-variable dict for rule evaluation."""
    ts = request_data.get("timestamp")
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)

    context = request_data.get("context") or {}

    variables = {
        "market_state": request_data["customer_location"]["state"],
        "compliance_tags": item_data.get("compliance_tags", []),
        "category_path": item_data.get("category_path", ""),
        "item_weight_lbs": item_data.get("attributes", {}).get("weight_lbs", 0),
        "request_month": ts.month if ts else 1,
        "request_hour": ts.hour if ts else 12,
        "fulfillment_path": fulfillment_path,
        "county": request_data["customer_location"].get("county"),
        # Seller variables (None if no seller)
        "seller_defect_rate": float(seller_data["defect_rate"]) if seller_data else None,
        "seller_trust_tier": seller_data.get("trust_tier") if seller_data else None,
        "seller_on_time_rate": float(seller_data["on_time_rate"]) if seller_data else None,
        "seller_total_orders": seller_data.get("total_orders", 0) if seller_data else None,
        # Context variables (optional, for REQUIRE resolution)
        "customer_age": context.get("customer_age"),
        "requested_quantity": context.get("requested_quantity"),
        "background_check_status": context.get("background_check_status"),
    }
    return variables

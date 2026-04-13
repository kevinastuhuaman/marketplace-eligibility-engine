from datetime import datetime


def build_variables(
    request_data: dict,
    item_data: dict,
    seller_data: dict | None,
    fulfillment_path: str,
    market_data: dict | None = None,
    matched_zone_codes: list[str] | None = None,
) -> dict:
    """Build the rule-evaluation variable dict."""
    ts = request_data.get("timestamp")
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)

    context = request_data.get("context") or {}
    item_attributes = item_data.get("attributes", {})
    market_data = market_data or {}

    variables = {
        "market_code": request_data.get("market_code"),
        "market_state": request_data["customer_location"]["state"],
        "market_country_code": market_data.get("country_code"),
        "market_region_code": market_data.get("region_code"),
        "market_language_codes": market_data.get("language_codes", []),
        "compliance_tags": item_data.get("compliance_tags", []),
        "category_path": item_data.get("category_path", ""),
        "item_weight_lbs": item_attributes.get("weight_lbs", 0),
        "item_risk_tier": item_attributes.get("risk_tier", "medium"),
        "item_requires_nom": item_attributes.get("requires_nom", False),
        "item_has_nom_certificate": item_attributes.get("has_nom_certificate", False),
        "item_has_spanish_label": item_attributes.get("has_spanish_label", False),
        "item_has_bilingual_label": item_attributes.get("has_bilingual_label", False),
        "item_uses_metric_units": item_attributes.get("uses_metric_units", False),
        "item_has_black_label": item_attributes.get("has_black_label", False),
        "item_has_import_certificate": item_attributes.get("has_import_certificate", False),
        "item_has_vat_registration": item_attributes.get("has_vat_registration", False),
        "request_month": ts.month if ts else 1,
        "request_hour": ts.hour if ts else 12,
        "fulfillment_path": fulfillment_path,
        "county": request_data["customer_location"].get("county"),
        "latitude": request_data["customer_location"].get("latitude"),
        "longitude": request_data["customer_location"].get("longitude"),
        "matched_zone_codes": matched_zone_codes or [],
        # Seller variables (None if no seller)
        "seller_defect_rate": float(seller_data.get("defect_rate", 0)) if seller_data else None,
        "seller_trust_tier": seller_data.get("trust_tier") if seller_data else None,
        "seller_on_time_rate": float(seller_data.get("on_time_rate", 0)) if seller_data else None,
        "seller_total_orders": seller_data.get("total_orders", 0) if seller_data else None,
        "seller_in_stock_rate": float(seller_data.get("in_stock_rate", 0)) if seller_data and seller_data.get("in_stock_rate") is not None else None,
        "seller_cancellation_rate": float(seller_data.get("cancellation_rate", 0)) if seller_data and seller_data.get("cancellation_rate") is not None else None,
        "seller_valid_tracking_rate": float(seller_data.get("valid_tracking_rate", 0)) if seller_data and seller_data.get("valid_tracking_rate") is not None else None,
        "seller_response_rate": float(seller_data.get("seller_response_rate", 0)) if seller_data and seller_data.get("seller_response_rate") is not None else None,
        "seller_return_rate": float(seller_data.get("return_rate", 0)) if seller_data and seller_data.get("return_rate") is not None else None,
        "seller_item_not_received_rate": float(seller_data.get("item_not_received_rate", 0)) if seller_data and seller_data.get("item_not_received_rate") is not None else None,
        "seller_negative_feedback_rate": float(seller_data.get("negative_feedback_rate", 0)) if seller_data and seller_data.get("negative_feedback_rate") is not None else None,
        "seller_uses_wfs": bool(seller_data.get("uses_wfs")) if seller_data else None,
        "seller_ipi_score": seller_data.get("ipi_score") if seller_data else None,
        "seller_vat_registered": bool(seller_data.get("vat_registered")) if seller_data else None,
        # Context variables (optional, for REQUIRE resolution)
        "customer_age": context.get("customer_age"),
        "requested_quantity": context.get("requested_quantity"),
        "background_check_status": context.get("background_check_status"),
        "primary_node_id": context.get("primary_node_id"),
        "nearby_nodes": context.get("nearby_nodes") or [],
    }
    return variables

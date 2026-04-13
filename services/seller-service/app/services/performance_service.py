from __future__ import annotations

from typing import Any

STANDARDS_LAST_UPDATED = "2026-03-25"

SELLER_PERFORMANCE_STANDARDS: tuple[dict[str, Any], ...] = (
    {
        "code": "cancellation_rate",
        "label": "Cancellation Rate",
        "threshold": 0.02,
        "direction": "max",
        "window_days": 30,
        "recommendation": "Avoid out-of-stock, pricing, and ship-window-expired cancellations.",
    },
    {
        "code": "on_time_delivery_rate",
        "label": "On-Time Delivery Rate",
        "threshold": 0.90,
        "direction": "min",
        "window_days": 30,
        "recommendation": "Tighten lag time, carrier choice, and promised delivery estimates.",
    },
    {
        "code": "valid_tracking_rate",
        "label": "Valid Tracking Rate",
        "threshold": 0.99,
        "direction": "min",
        "window_days": 30,
        "recommendation": "Only share tracking after carrier hand-off and ensure the carrier is supported.",
    },
    {
        "code": "seller_response_rate",
        "label": "Seller Response Rate",
        "threshold": 0.95,
        "direction": "min",
        "window_days": 30,
        "recommendation": "Respond to customer inquiries within 48 hours or mark no response needed.",
    },
    {
        "code": "return_rate",
        "label": "Return Rate",
        "threshold": 0.06,
        "direction": "max",
        "window_days": 60,
        "recommendation": "Improve inventory accuracy, packaging quality, and item descriptions.",
    },
    {
        "code": "item_not_received_rate",
        "label": "Item Not Received Rate",
        "threshold": 0.02,
        "direction": "max",
        "window_days": 60,
        "recommendation": "Reduce lost parcels and incorrect-item issues through stronger fulfillment controls.",
    },
    {
        "code": "negative_feedback_rate",
        "label": "Negative Feedback Rate",
        "threshold": 0.02,
        "direction": "max",
        "window_days": 60,
        "recommendation": "Investigate low ratings quickly and fix quality or description issues.",
    },
)

WFS_ASSISTED_METRICS = {
    "cancellation_rate",
    "on_time_delivery_rate",
    "valid_tracking_rate",
    "seller_response_rate",
    "return_rate",
    "item_not_received_rate",
}


def _actual_value(seller: Any, code: str) -> float:
    if code == "on_time_delivery_rate":
        return float(seller.on_time_rate)
    return float(getattr(seller, code))


def _metric_status(actual: float, threshold: float, direction: str) -> str:
    if direction == "max":
        return "meets_standard" if actual <= threshold else "action_required"
    return "meets_standard" if actual >= threshold else "action_required"


def build_performance_snapshot(seller: Any) -> dict[str, Any]:
    metrics: list[dict[str, Any]] = []
    for standard in SELLER_PERFORMANCE_STANDARDS:
        actual = _actual_value(seller, standard["code"])
        metrics.append(
            {
                "code": standard["code"],
                "label": standard["label"],
                "actual": round(actual, 4),
                "threshold": standard["threshold"],
                "direction": standard["direction"],
                "window_days": standard["window_days"],
                "status": _metric_status(actual, standard["threshold"], standard["direction"]),
                "recommendation": standard["recommendation"],
                "wfs_assisted": bool(getattr(seller, "uses_wfs", False))
                and standard["code"] in WFS_ASSISTED_METRICS,
            }
        )

    good_standing = all(metric["status"] == "meets_standard" for metric in metrics)
    return {
        "seller_id": seller.seller_id,
        "seller_name": seller.name,
        "overall_status": "good_standing" if good_standing else "action_required",
        "pro_seller_eligible": good_standing,
        "uses_wfs": bool(getattr(seller, "uses_wfs", False)),
        "standards_last_updated": STANDARDS_LAST_UPDATED,
        "account_risk": (
            "In good standing with Marketplace seller performance standards."
            if good_standing
            else "One or more Marketplace seller performance standards miss policy thresholds and may trigger suppression, suspension, or termination."
        ),
        "metrics": metrics,
        "source": "Marketplace Seller Performance Standards",
    }

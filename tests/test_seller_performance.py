"""Unit tests for Walmart seller performance standards helpers."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "services",
        "seller-service",
    ),
)

from app.services.performance_service import build_performance_snapshot


def test_performance_snapshot_marks_good_standing_when_all_metrics_meet_standard():
    seller = SimpleNamespace(
        seller_id="seller-1",
        name="Trusted Seller",
        on_time_rate=0.96,
        cancellation_rate=0.01,
        valid_tracking_rate=0.995,
        seller_response_rate=0.99,
        return_rate=0.04,
        item_not_received_rate=0.01,
        negative_feedback_rate=0.01,
        uses_wfs=True,
    )

    snapshot = build_performance_snapshot(seller)

    assert snapshot["overall_status"] == "good_standing"
    assert snapshot["pro_seller_eligible"] is True
    assert any(metric["wfs_assisted"] for metric in snapshot["metrics"])


def test_performance_snapshot_requires_action_when_any_metric_misses_standard():
    seller = SimpleNamespace(
        seller_id="seller-2",
        name="Risky Seller",
        on_time_rate=0.88,
        cancellation_rate=0.05,
        valid_tracking_rate=0.97,
        seller_response_rate=0.9,
        return_rate=0.08,
        item_not_received_rate=0.03,
        negative_feedback_rate=0.04,
        uses_wfs=False,
    )

    snapshot = build_performance_snapshot(seller)

    assert snapshot["overall_status"] == "action_required"
    assert snapshot["pro_seller_eligible"] is False
    assert all(metric["status"] == "action_required" for metric in snapshot["metrics"])

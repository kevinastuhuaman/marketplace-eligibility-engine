"""Unit tests for seller IPI helpers."""

import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "services",
        "seller-service",
    ),
)

from app.services.ipi_service import compute_ipi, ipi_tier, rank_adjustment_pct


def test_compute_ipi_returns_score_and_breakdown():
    score, breakdown = compute_ipi(
        in_stock_rate=0.98,
        defect_rate=0.01,
        on_time_rate=0.97,
        cancellation_rate=0.01,
    )
    assert score > 0
    assert breakdown["in_stock_rate"] == 0.98


def test_ipi_tiers_and_rank_adjustment():
    assert ipi_tier(480) == "elite"
    assert ipi_tier(250) == "risky"
    assert ipi_tier(150) == "critical"
    assert rank_adjustment_pct(480) > 0
    assert rank_adjustment_pct(150) < 0


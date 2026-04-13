"""Unit tests for probabilistic inventory confidence."""

import os
import sys
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "services",
        "inventory-service",
    ),
)

from app.services.confidence_service import band_for_score, score_inventory_position

PACIFIC = ZoneInfo("America/Los_Angeles")


def test_band_for_score():
    assert band_for_score(0.95) == "high"
    assert band_for_score(0.80) == "medium"
    assert band_for_score(0.50) == "low"


def test_score_inventory_position_drops_for_stale_inventory():
    position = SimpleNamespace(
        confidence_score=0.92,
        last_verified_at=datetime(2026, 4, 6, 9, 0, tzinfo=PACIFIC),
        verification_source="seed",
        oos_30d_count=5,
    )
    result = score_inventory_position(
        position,
        now=datetime(2026, 4, 9, 9, 0, tzinfo=PACIFIC),
    )
    assert result["confidence_score"] < 0.90
    assert result["confidence_band"] in {"medium", "low"}


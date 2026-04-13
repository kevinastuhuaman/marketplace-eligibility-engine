from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")


def _coerce_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=PACIFIC)
    return value.astimezone(PACIFIC)


def band_for_score(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 0.90:
        return "high"
    if score >= 0.75:
        return "medium"
    return "low"


def score_inventory_position(position, now: datetime | None = None) -> dict:
    now = _coerce_timestamp(now) or datetime.now(PACIFIC)
    last_verified_at = _coerce_timestamp(getattr(position, "last_verified_at", None))
    stored_score = float(getattr(position, "confidence_score", 1.0) or 1.0)
    stored_score = max(0.0, min(stored_score, 1.0))

    freshness_score = 1.0
    age_hours = 0.0
    if last_verified_at is not None:
        age_hours = max((now - last_verified_at).total_seconds() / 3600, 0.0)
        freshness_score = max(0.0, 1.0 - min(age_hours * 0.00375, 0.35))

    oos_30d_count = int(getattr(position, "oos_30d_count", 0) or 0)
    volatility_score = max(0.0, 1.0 - min(oos_30d_count * 0.03, 0.30))
    final_score = round(min(stored_score, freshness_score, volatility_score), 3)

    verification_source = getattr(position, "verification_source", "seed") or "seed"
    if final_score == stored_score and stored_score < min(freshness_score, volatility_score):
        reason = f"Inventory feed confidence from {verification_source} is below fully verified."
    elif final_score == freshness_score and age_hours > 0:
        reason = f"Last verified {int(age_hours)} hours ago."
    elif final_score == volatility_score and oos_30d_count > 0:
        reason = f"Recent stock volatility: {oos_30d_count} stockouts in the last 30 days."
    else:
        reason = f"Recently verified via {verification_source}."

    return {
        "confidence_score": final_score,
        "confidence_band": band_for_score(final_score),
        "confidence_reason": reason,
        "last_verified_at": last_verified_at,
    }


def summarize_path_confidence(positions: list, primary_node: str | None = None) -> dict:
    if not positions:
        return {
            "confidence_score": None,
            "confidence_band": None,
            "confidence_reason": None,
            "last_verified_at": None,
        }

    if primary_node:
        candidates = [position for position in positions if position.fulfillment_node == primary_node]
        if not candidates:
            return {
                "confidence_score": None,
                "confidence_band": None,
                "confidence_reason": None,
                "last_verified_at": None,
            }
        position = candidates[0]
    else:
        position = max(
            positions,
            key=lambda entry: (
                max(int(getattr(entry, "available_qty", 0) or 0) - int(getattr(entry, "reserved_qty", 0) or 0), 0),
                float(getattr(entry, "confidence_score", 0) or 0),
            ),
        )

    return score_inventory_position(position)

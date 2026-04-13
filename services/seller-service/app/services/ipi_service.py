from __future__ import annotations


def compute_ipi(
    *,
    in_stock_rate: float,
    defect_rate: float,
    on_time_rate: float,
    cancellation_rate: float,
) -> tuple[int, dict]:
    score = int(
        round(
            (in_stock_rate * 400)
            + ((1.0 - defect_rate) * 220)
            + (on_time_rate * 180)
            + ((1.0 - cancellation_rate) * 200)
        )
    )
    return score, {
        "in_stock_rate": round(in_stock_rate, 4),
        "defect_rate": round(defect_rate, 4),
        "on_time_rate": round(on_time_rate, 4),
        "cancellation_rate": round(cancellation_rate, 4),
    }


def ipi_tier(score: int) -> str:
    if score >= 450:
        return "elite"
    if score >= 300:
        return "trusted"
    if score >= 200:
        return "risky"
    return "critical"


def rank_adjustment_pct(score: int) -> float:
    if score >= 450:
        return 8.0
    if score >= 300:
        return 2.5
    if score >= 200:
        return -7.5
    return -15.0

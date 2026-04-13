from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import EligibilityAuditLog

PACIFIC = ZoneInfo("America/Los_Angeles")


def _window_start(days: int) -> datetime:
    return datetime.now(PACIFIC) - timedelta(days=days)


async def blocked_items(
    db: AsyncSession,
    days: int,
    market_code: str | None,
    limit: int,
) -> list[dict]:
    filters = [EligibilityAuditLog.evaluated_at >= _window_start(days)]
    if market_code:
        filters.append(EligibilityAuditLog.market_code == market_code)

    result = await db.execute(
        select(
            EligibilityAuditLog.item_id,
            func.max(EligibilityAuditLog.market_code).label("market_code"),
            func.count(EligibilityAuditLog.log_id).label("blocked_count"),
        )
        .where(and_(*filters), EligibilityAuditLog.eligible.is_(False))
        .group_by(EligibilityAuditLog.item_id)
        .order_by(func.count(EligibilityAuditLog.log_id).desc())
        .limit(limit)
    )
    return [
        {
            "item_id": str(row.item_id),
            "blocked_count": int(row.blocked_count or 0),
            "market_code": row.market_code,
            "revenue_at_risk": round(float(row.blocked_count or 0) * 49.99, 2),
        }
        for row in result
    ]


async def rule_impact(
    db: AsyncSession,
    days: int,
    market_code: str | None,
    limit: int,
) -> list[dict]:
    filters = [EligibilityAuditLog.evaluated_at >= _window_start(days)]
    if market_code:
        filters.append(EligibilityAuditLog.market_code == market_code)

    result = await db.execute(
        select(
            func.unnest(EligibilityAuditLog.blocking_rule_names).label("rule_name"),
            func.count(EligibilityAuditLog.log_id).label("block_count"),
        )
        .where(and_(*filters))
        .group_by("rule_name")
        .order_by(func.count(EligibilityAuditLog.log_id).desc())
        .limit(limit)
    )
    return [
        {
            "rule_name": row.rule_name,
            "block_count": int(row.block_count or 0),
            "gate_count": 0,
            "warning_count": 0,
            "reversal_rate": 0.0,
            "market_code": market_code,
        }
        for row in result
        if row.rule_name
    ]


async def market_coverage(db: AsyncSession, days: int) -> list[dict]:
    result = await db.execute(
        select(
            EligibilityAuditLog.market_code,
            func.count(EligibilityAuditLog.log_id).label("evaluations"),
            func.sum(case((EligibilityAuditLog.eligible.is_(True), 1), else_=0)).label("eligible_count"),
        )
        .where(EligibilityAuditLog.evaluated_at >= _window_start(days))
        .group_by(EligibilityAuditLog.market_code)
        .order_by(EligibilityAuditLog.market_code)
    )

    payload = []
    for row in result:
        evaluations = int(row.evaluations or 0)
        eligible_count = int(row.eligible_count or 0)
        blocked_count = max(evaluations - eligible_count, 0)
        payload.append(
            {
                "market_code": row.market_code,
                "eligible_rate": round(eligible_count / evaluations, 4) if evaluations else 0.0,
                "blocked_rate": round(blocked_count / evaluations, 4) if evaluations else 0.0,
                "eligibility_rate": round(eligible_count / evaluations, 4) if evaluations else 0.0,
                "low_confidence_rate": 0.0,
            }
        )
    return payload

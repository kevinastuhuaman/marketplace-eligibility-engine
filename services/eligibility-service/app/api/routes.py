from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.eligibility_service import evaluate
from app.models.compliance import ComplianceRule
from app.models.fulfillment import FulfillmentPath, MarketFulfillment
from app.schemas.eligibility import (
    RuleCreate,
    FulfillmentPathCreate,
    MarketFulfillmentCreate,
)
from shared.contracts.eligibility import EligibilityRequest
from sqlalchemy import select

import httpx
import json
from tenacity import RetryError

router = APIRouter()


@router.post("/v1/evaluate")
async def evaluate_eligibility(
    request: EligibilityRequest,
    response: Response,
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
    debug: bool = Query(False),
):
    try:
        request_data = json.loads(request.model_dump_json())
        request_data["_debug"] = debug
        result = await evaluate(request_data, db)

        # Publish evaluation event to Redis
        publisher = getattr(raw_request.app.state, "stream_publisher", None)
        if publisher and not result.get("errors"):
            try:
                await publisher.publish("evaluation_completed", {
                    "item_id": result.get("item_id"),
                    "market_code": result.get("market_code"),
                    "eligible": result.get("eligible"),
                    "rules_evaluated": result.get("rules_evaluated"),
                    "evaluation_ms": result.get("evaluation_ms"),
                })
            except Exception:
                pass  # Don't fail the response if stream publish fails

        return result
    except httpx.HTTPStatusError as e:
        response.status_code = 503
        return {
            "error": "service_unavailable",
            "detail": str(e),
            "retry_after_seconds": 5,
        }
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        response.status_code = 503
        return {
            "error": "service_unavailable",
            "detail": f"Downstream service timeout or unreachable: {e}",
            "retry_after_seconds": 5,
        }
    except RetryError as e:
        response.status_code = 503
        return {
            "error": "service_unavailable",
            "detail": f"Downstream service failed after retries: {e}",
            "retry_after_seconds": 5,
        }


@router.post("/v1/rules", status_code=201)
async def create_rule(
    payload: RuleCreate, db: AsyncSession = Depends(get_db)
):
    rule = ComplianceRule(
        rule_name=payload.rule_name,
        rule_type=payload.rule_type,
        action=payload.action,
        priority=payload.priority,
        conflict_group=payload.conflict_group,
        market_codes=payload.market_codes,
        category_paths=payload.category_paths,
        compliance_tags=payload.compliance_tags,
        blocked_paths=payload.blocked_paths,
        rule_definition=payload.rule_definition,
        reason=payload.reason,
        metadata_=payload.metadata or {},
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        enabled=payload.enabled if payload.enabled is not None else True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"rule_id": rule.rule_id, "rule_name": rule.rule_name}


@router.get("/v1/rules")
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplianceRule).order_by(ComplianceRule.priority)
    )
    rules = result.scalars().all()
    return [
        {
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "action": r.action,
            "priority": r.priority,
            "enabled": r.enabled,
        }
        for r in rules
    ]


@router.post("/v1/fulfillment-paths", status_code=201)
async def create_path(
    payload: FulfillmentPathCreate, db: AsyncSession = Depends(get_db)
):
    path = FulfillmentPath(
        path_code=payload.path_code,
        display_name=payload.display_name,
        owner=payload.owner,
        requires_inventory=payload.requires_inventory,
        max_weight_lbs=payload.max_weight_lbs,
    )
    db.add(path)
    await db.commit()
    await db.refresh(path)
    return {"path_id": path.path_id, "path_code": path.path_code}


@router.post("/v1/markets", status_code=201)
async def create_market(
    payload: MarketFulfillmentCreate, db: AsyncSession = Depends(get_db)
):
    mf = MarketFulfillment(
        market_code=payload.market_code,
        path_id=payload.path_id,
        enabled=payload.enabled if payload.enabled is not None else True,
        priority=payload.priority,
    )
    db.add(mf)
    await db.commit()
    return {"market_code": mf.market_code, "path_id": mf.path_id}


@router.get("/v1/demo/scenarios")
async def list_scenarios():
    from shared.scenario_data import SCENARIOS
    return SCENARIOS

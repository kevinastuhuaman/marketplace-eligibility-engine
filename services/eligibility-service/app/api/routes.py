from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import RetryError

from app.db import get_db
from app.models.compliance import ComplianceRule
from app.models.fulfillment import FulfillmentPath, MarketFulfillment
from app.models.geo_restriction_zone import GeoRestrictionZone
from app.models.market_regulation import MarketRegulation
from app.schemas.eligibility import (
    FulfillmentPathCreate,
    GeoRestrictionZoneCreate,
    MarketFulfillmentCreate,
    MarketRegulationCreate,
    RuleCreate,
)
from app.services.analytics_service import blocked_items, market_coverage, rule_impact
from app.services.batch_evaluation_service import evaluate_batch
from app.services.circuit_breaker_service import get_breaker_states
from app.services.diagnosis_service import build_diagnosis
from app.services.eligibility_service import evaluate
from app.services.trace_context import clear_trace, start_trace
from shared.contracts.eligibility import (
    BatchEvaluateRequest,
    DiagnosisRequest,
    EligibilityRequest,
)

router = APIRouter()


def _service_unavailable(response: Response, detail: str) -> dict:
    response.status_code = 503
    return {
        "error": "service_unavailable",
        "detail": detail,
        "retry_after_seconds": 5,
    }


@router.post("/v1/evaluate")
async def evaluate_eligibility(
    request: EligibilityRequest,
    response: Response,
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
    debug: bool = Query(False),
):
    start_trace()
    try:
        request_data = json.loads(request.model_dump_json())
        request_data["_debug"] = debug
        result = await evaluate(request_data, db)

        publisher = getattr(raw_request.app.state, "stream_publisher", None)
        if publisher and not result.get("errors"):
            try:
                await publisher.publish(
                    "evaluation_completed",
                    {
                        "item_id": result.get("item_id"),
                        "market_code": result.get("market_code"),
                        "eligible": result.get("eligible"),
                        "rules_evaluated": result.get("rules_evaluated"),
                        "evaluation_ms": result.get("evaluation_ms"),
                    },
                )
            except Exception:
                pass

        return result
    except httpx.HTTPStatusError as exc:
        return _service_unavailable(response, str(exc))
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        return _service_unavailable(response, f"Downstream service timeout or unreachable: {exc}")
    except RetryError as exc:
        return _service_unavailable(response, f"Downstream service failed after retries: {exc}")
    finally:
        clear_trace()


@router.post("/v1/diagnose")
async def diagnose_eligibility(
    request: DiagnosisRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    start_trace()
    try:
        request_data = json.loads(request.model_dump_json())
        evaluation = await evaluate(request_data, db)
        return await build_diagnosis(db, request_data, evaluation)
    except httpx.HTTPStatusError as exc:
        return _service_unavailable(response, str(exc))
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        return _service_unavailable(response, f"Downstream service timeout or unreachable: {exc}")
    except RetryError as exc:
        return _service_unavailable(response, f"Downstream service failed after retries: {exc}")
    finally:
        clear_trace()


@router.post("/v1/evaluate/batch")
async def evaluate_batch_route(
    payload: BatchEvaluateRequest,
    db: AsyncSession = Depends(get_db),
):
    requests = [json.loads(request.model_dump_json()) for request in payload.requests]
    return await evaluate_batch(requests, db)


@router.post("/v1/rules", status_code=201)
async def create_rule(payload: RuleCreate, db: AsyncSession = Depends(get_db)):
    rule = ComplianceRule(
        rule_name=payload.rule_name,
        rule_type=payload.rule_type,
        regulation_type=payload.regulation_type,
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
    result = await db.execute(select(ComplianceRule).order_by(ComplianceRule.priority))
    rules = result.scalars().all()
    return [
        {
            "rule_id": rule.rule_id,
            "rule_name": rule.rule_name,
            "rule_type": rule.rule_type,
            "regulation_type": rule.regulation_type,
            "action": rule.action,
            "priority": rule.priority,
            "enabled": rule.enabled,
        }
        for rule in rules
    ]


@router.get("/v1/fulfillment-paths")
async def list_paths(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FulfillmentPath).order_by(FulfillmentPath.path_id))
    paths = result.scalars().all()
    return [
        {
            "path_id": path.path_id,
            "path_code": path.path_code,
            "display_name": path.display_name,
            "owner": path.owner,
            "requires_inventory": path.requires_inventory,
        }
        for path in paths
    ]


@router.post("/v1/fulfillment-paths", status_code=201)
async def create_path(payload: FulfillmentPathCreate, db: AsyncSession = Depends(get_db)):
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
async def create_market(payload: MarketFulfillmentCreate, db: AsyncSession = Depends(get_db)):
    market_fulfillment = MarketFulfillment(
        market_code=payload.market_code,
        path_id=payload.path_id,
        enabled=payload.enabled if payload.enabled is not None else True,
        priority=payload.priority,
    )
    db.add(market_fulfillment)
    await db.commit()
    return {"market_code": market_fulfillment.market_code, "path_id": market_fulfillment.path_id}


@router.post("/v1/market-regulations", status_code=201)
async def create_market_regulation(
    payload: MarketRegulationCreate,
    db: AsyncSession = Depends(get_db),
):
    market = MarketRegulation(
        market_code=payload.market_code,
        display_name=payload.display_name,
        country_code=payload.country_code,
        region_code=payload.region_code,
        currency_code=payload.currency_code,
        language_codes=payload.language_codes or ["en"],
        default_timezone=payload.default_timezone,
        regulatory_summary=payload.regulatory_summary or {},
        active=payload.active,
    )
    db.add(market)
    await db.commit()
    return {"market_code": market.market_code}


@router.get("/v1/markets")
async def list_markets(db: AsyncSession = Depends(get_db)):
    market_result = await db.execute(
        select(MarketRegulation).where(MarketRegulation.active.is_(True)).order_by(MarketRegulation.market_code)
    )
    markets = market_result.scalars().all()

    path_result = await db.execute(
        select(FulfillmentPath, MarketFulfillment)
        .join(MarketFulfillment, FulfillmentPath.path_id == MarketFulfillment.path_id)
        .where(MarketFulfillment.enabled.is_(True))
    )
    path_rows = path_result.all()
    supported_paths: dict[str, list[str]] = {}
    for path, mapping in path_rows:
        supported_paths.setdefault(mapping.market_code, []).append(path.path_code)

    return [
        {
            "market_code": market.market_code,
            "display_name": market.display_name,
            "country_code": market.country_code,
            "region_code": market.region_code,
            "currency_code": market.currency_code,
            "language_codes": market.language_codes or [],
            "supported_paths": supported_paths.get(market.market_code, []),
            "regulatory_summary": market.regulatory_summary or {},
        }
        for market in markets
    ]


@router.post("/v1/geo-zones", status_code=201)
async def create_geo_zone(payload: GeoRestrictionZoneCreate, db: AsyncSession = Depends(get_db)):
    zone = GeoRestrictionZone(
        zone_code=payload.zone_code,
        market_code=payload.market_code,
        zone_name=payload.zone_name,
        zone_type=payload.zone_type,
        geometry_type=payload.geometry_type,
        center_latitude=payload.center_latitude,
        center_longitude=payload.center_longitude,
        radius_meters=payload.radius_meters,
        polygon_coordinates=payload.polygon_coordinates or [],
        hex_cells=payload.hex_cells or [],
        blocked_paths=payload.blocked_paths or [],
        metadata_=payload.metadata or {},
        active=payload.active,
    )
    db.add(zone)
    await db.commit()
    return {"zone_code": zone.zone_code}


@router.get("/v1/system/circuit-breakers")
async def get_circuit_breakers():
    return {"breakers": get_breaker_states()}


@router.get("/v1/analytics/blocked-items")
async def get_blocked_items(
    days: int = Query(7, ge=1, le=365),
    market_code: str | None = None,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await blocked_items(db, days, market_code, limit)


@router.get("/v1/analytics/rule-impact")
async def get_rule_impact(
    days: int = Query(7, ge=1, le=365),
    market_code: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await rule_impact(db, days, market_code, limit)


@router.get("/v1/analytics/market-coverage")
async def get_market_coverage(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    return await market_coverage(db, days)


@router.get("/v1/demo/scenarios")
async def list_scenarios():
    from shared.scenario_data import SCENARIOS

    return SCENARIOS

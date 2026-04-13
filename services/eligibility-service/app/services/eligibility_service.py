"""Eligibility evaluation orchestrator."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import inventory_client, item_client, seller_client
from app.config import settings
from app.engine.evaluator import (
    determine_path_status,
    evaluate_rules,
    resolve_and_accumulate,
    resolve_requirements,
)
from app.engine.variables import build_variables
from app.models.audit import EligibilityAuditLog
from app.models.compliance import ComplianceRule
from app.models.fulfillment import FulfillmentPath, MarketFulfillment
from app.models.market_regulation import MarketRegulation
from app.services.diagnosis_service import derive_primary_cause
from app.services.geo_service import find_matching_zones
from app.services.rule_cache_service import get_cached_rules, set_cached_rules
from shared.constants import PLATFORM_SELLER_ID

PACIFIC = ZoneInfo("America/Los_Angeles")


def _rule_to_cache_payload(rule: ComplianceRule) -> dict:
    return {
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "regulation_type": rule.regulation_type,
        "action": rule.action,
        "priority": rule.priority,
        "conflict_group": rule.conflict_group,
        "market_codes": rule.market_codes,
        "category_paths": rule.category_paths,
        "compliance_tags": rule.compliance_tags,
        "blocked_paths": rule.blocked_paths,
        "rule_definition": rule.rule_definition,
        "reason": rule.reason,
        "metadata_": rule.metadata_ or {},
        "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
        "effective_until": rule.effective_until.isoformat() if rule.effective_until else None,
        "enabled": rule.enabled,
        "version": rule.version,
    }


def _hydrate_rule(payload: dict) -> SimpleNamespace:
    payload = dict(payload)
    effective_from = payload.get("effective_from")
    effective_until = payload.get("effective_until")

    if isinstance(effective_from, str):
        payload["effective_from"] = datetime.fromisoformat(effective_from)
    if isinstance(effective_until, str):
        payload["effective_until"] = datetime.fromisoformat(effective_until)
    return SimpleNamespace(**payload)


async def evaluate(request_data: dict, db: AsyncSession) -> dict:
    start = time.perf_counter()
    try:
        item_id = UUID(str(request_data["item_id"]))
        market_code = request_data["market_code"]
        timestamp = request_data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        seller_id_raw = request_data.get("seller_id")
        seller_id = UUID(str(seller_id_raw)) if seller_id_raw else None
        state = request_data["customer_location"]["state"]
    except (KeyError, TypeError, ValueError) as exc:
        return _error_response(
            request_data.get("item_id", "unknown"),
            request_data.get("market_code", "unknown"),
            start,
            [f"Missing or invalid required field: {exc}"],
        )

    market_summary = await _load_market_summary(db, market_code)
    if not market_summary:
        return _error_response(item_id, market_code, start, [f"Unknown market {market_code}"])
    if market_summary["region_code"] != state:
        return _error_response(
            item_id,
            market_code,
            start,
            [f"customer_location.state '{state}' does not match market region '{market_summary['region_code']}'"],
        )

    try:
        item_data = await item_client.get_item(item_id)
    except Exception as exc:
        return _error_response(item_id, market_code, start, [f"Item service unavailable: {exc}"])
    if not item_data:
        return _error_response(item_id, market_code, start, ["Item not found"])

    risk_tier = item_data.get("attributes", {}).get("risk_tier", "medium")
    seller_data = None
    seller_signal = None
    seller_performance = None

    if seller_id:
        try:
            offer = await seller_client.check_offer(seller_id, item_id)
        except Exception as exc:
            return _error_response(item_id, market_code, start, [f"Seller offer lookup failed: {exc}"])
        if not offer.get("exists") or not offer.get("active"):
            return _error_response(item_id, market_code, start, ["Seller does not offer this item"])

        try:
            seller_data = await seller_client.get_seller(seller_id)
        except Exception:
            seller_data = None  # Continue evaluation without seller enrichment
        if seller_data is None:
            seller_data = {
                "seller_id": str(seller_id),
                "trust_tier": "new",
                "defect_rate": "0.10",
                "return_rate": "0.05",
                "on_time_rate": "0.80",
                "total_orders": 0,
                "in_stock_rate": "0.90",
                "cancellation_rate": "0.05",
                "valid_tracking_rate": "0.90",
                "seller_response_rate": "0.80",
                "item_not_received_rate": "0.05",
                "negative_feedback_rate": "0.05",
                "uses_wfs": False,
                "vat_registered": False,
            }  # Conservative defaults so rule variables don't KeyError

        try:
            ipi_data = await seller_client.get_ipi(seller_id)
        except Exception:
            ipi_data = None
        if ipi_data:
            seller_data = {**seller_data, **ipi_data.get("breakdown", {}), "ipi_score": ipi_data.get("ipi_score")}
            seller_signal = {
                "ipi_score": ipi_data.get("ipi_score"),
                "ipi_tier": ipi_data.get("tier"),
                "rank_adjustment_pct": ipi_data.get("rank_adjustment_pct", 0),
                "wfs_recommendation": ipi_data.get("wfs_recommendation"),
            }
        try:
            performance_data = await seller_client.get_performance(seller_id)
        except Exception:
            performance_data = None
        # Normalize performance metric codes to seller_data field names
        _PERF_CODE_TO_FIELD = {
            "on_time_delivery_rate": "on_time_rate",
        }
        if performance_data:
            metric_map = {
                _PERF_CODE_TO_FIELD.get(metric["code"], metric["code"]): metric.get("actual")
                for metric in performance_data.get("metrics", [])
            }
            seller_data = {**seller_data, **metric_map}
            seller_performance = {
                "overall_status": performance_data.get("overall_status"),
                "pro_seller_eligible": performance_data.get("pro_seller_eligible"),
                "uses_wfs": performance_data.get("uses_wfs", False),
                "standards_last_updated": performance_data.get("standards_last_updated"),
                "account_risk": performance_data.get("account_risk"),
                "source": performance_data.get("source"),
                "metrics": performance_data.get("metrics", []),
            }

    paths = await _load_paths(db, market_code, seller_id is not None)
    if not paths:
        owner = "3p" if seller_id else "1p"
        return _error_response(
            item_id,
            market_code,
            start,
            [f"No {owner} fulfillment paths enabled for market {market_code}"],
        )

    rules = await _load_matching_rules(db, market_code, item_data, timestamp)
    debug_mode = bool(request_data.get("_debug"))
    primary_node = (request_data.get("context") or {}).get("primary_node_id")
    nearby_nodes = (request_data.get("context") or {}).get("nearby_nodes") or []
    inv_seller_id = seller_id or PLATFORM_SELLER_ID

    inventory_error = None
    try:
        inventory_data = await inventory_client.get_availability(
            item_id,
            [path.path_id for path, _ in paths],
            inv_seller_id,
            primary_node=primary_node,
            nearby_nodes=nearby_nodes,
        )
    except Exception as exc:
        inventory_error = str(exc)
        inventory_data = {"paths": []}
    inventory_by_path = {path["path_id"]: path for path in inventory_data.get("paths", [])}

    per_path_evaluations = []
    all_triggered = []
    zone_matches: dict[str, list[str]] = {}
    zone_explanations: dict[str, str | None] = {}

    for path, _market_path in paths:
        matching_zones = []
        if settings.enable_geo_restrictions:
            matching_zones = await find_matching_zones(
                db,
                market_code,
                request_data["customer_location"],
                path.path_code,
            )
        zone_codes = [zone.zone_code for zone in matching_zones]
        zone_matches[path.path_code] = zone_codes
        zone_explanations[path.path_code] = (
            matching_zones[0].metadata_.get("explanation")
            if matching_zones and getattr(matching_zones[0], "metadata_", None)
            else None
        )
        variables = build_variables(
            request_data,
            item_data,
            seller_data,
            path.path_code,
            market_data=market_summary,
            matched_zone_codes=zone_codes,
        )
        triggered = evaluate_rules(rules, variables)
        all_triggered.extend(triggered)
        if debug_mode:
            per_path_evaluations.append(
                {
                    "path_code": path.path_code,
                    "matched_zone_codes": zone_codes,
                    "rules": [
                        {
                            "rule_id": rule.rule_id,
                            "rule_name": rule.rule_name,
                            "rule_type": rule.rule_type,
                            "action": rule.action,
                            "priority": rule.priority,
                            "conflict_group": rule.conflict_group,
                            "blocked_paths": rule.blocked_paths or [],
                            "reason": rule.reason,
                            "rule_definition": rule.rule_definition,
                            "matched": any(trigger.rule_id == rule.rule_id for trigger in triggered),
                            "suppressed": False,
                            "suppressed_by": None,
                            "survived": any(trigger.rule_id == rule.rule_id for trigger in triggered),
                        }
                        for rule in rules
                    ],
                }
            )

    unique_triggered = _dedupe_triggered(all_triggered)
    result = resolve_and_accumulate(unique_triggered)
    result = resolve_requirements(
        result,
        {
            "customer_age": (request_data.get("context") or {}).get("customer_age"),
            "requested_quantity": (request_data.get("context") or {}).get("requested_quantity"),
            "background_check_status": (request_data.get("context") or {}).get("background_check_status"),
        },
    )
    _apply_gate_context(result, seller_data)
    if debug_mode:
        _mark_suppressed(per_path_evaluations, result.conflict_resolutions)

    warnings = list(result.warnings)
    if inventory_error:
        warnings.append(
            {
                "rule_id": 0,
                "rule_name": "inventory_circuit_breaker",
                "action": "WARN",
                "reason": f"Inventory fallback applied because inventory-service was unavailable: {inventory_error}",
                "priority": 999,
                "metadata": {
                    "source_service": "inventory-service",
                    "cause_code": "inventory_service_unavailable",
                    "suggested_fix": "Restore inventory-service connectivity or wait for circuit breaker recovery.",
                },
            }
        )

    path_results = []
    for path, _market_path in paths:
        status, eligible = determine_path_status(path.path_code, result)
        inventory_row = inventory_by_path.get(path.path_id, {})
        total_sellable = int(inventory_row.get("total_sellable", 0) or 0)
        alternative_nodes = inventory_row.get("alternative_nodes", [])
        fallback_applied = False
        fallback_reason = None

        if (inventory_error or inventory_row.get("service_unavailable")) and path.requires_inventory and status not in ("blocked", "gated", "conditional"):
            status, eligible = _risk_tier_status(risk_tier)
            fallback_applied = True
            fallback_reason = f"Inventory fallback for {risk_tier}-risk item"
            if risk_tier == "low":
                warnings.append(
                    {
                        "rule_id": 0,
                        "rule_name": "inventory_service_fallback",
                        "action": "WARN",
                        "reason": "Inventory-service is unavailable. Low-risk item allowed with warning.",
                        "priority": 998,
                        "metadata": {
                            "source_service": "inventory-service",
                            "source_entity": "inventory_positions",
                            "source_field": "available_qty",
                            "cause_code": "inventory_service_unavailable",
                            "suggested_fix": "Restore inventory-service connectivity and re-run the evaluation.",
                            "diagnosis": {
                                "en": "Inventory-service was unavailable, so the system allowed this low-risk item with a warning.",
                                "es": "El servicio de inventario no estaba disponible, por eso el sistema permitió este artículo de bajo riesgo con una advertencia.",
                            },
                        },
                    }
                )
            elif risk_tier == "medium":
                result.gates.setdefault(path.path_code, []).append(
                    {
                        "rule_id": 0,
                        "rule_name": "inventory_service_manual_review",
                        "action": "GATE",
                        "reason": "Inventory-service is unavailable. Medium-risk item requires manual review.",
                        "priority": 998,
                        "gate_type": "manual_review",
                        "current": {},
                        "required": {"manual_review": True},
                        "gap": {"manual_review": True},
                        "metadata": {
                            "source_service": "inventory-service",
                            "source_entity": "inventory_positions",
                            "source_field": "available_qty",
                            "cause_code": "inventory_service_unavailable",
                            "suggested_fix": "Restore inventory-service connectivity or clear the item manually.",
                            "diagnosis": {
                                "en": "Inventory-service was unavailable, so this medium-risk item was gated for manual review.",
                                "es": "El servicio de inventario no estaba disponible, por eso este artículo de riesgo medio fue bloqueado para revisión manual.",
                            },
                        },
                    }
                )
            else:
                result.violations.setdefault(path.path_code, []).append(
                    {
                        "rule_id": 0,
                        "rule_name": "inventory_service_fail_closed",
                        "action": "BLOCK",
                        "reason": "Inventory-service is unavailable. High-risk item failed closed.",
                        "priority": 998,
                        "metadata": {
                            "source_service": "inventory-service",
                            "source_entity": "inventory_positions",
                            "source_field": "available_qty",
                            "cause_code": "inventory_service_unavailable",
                            "suggested_fix": "Restore inventory-service connectivity before allowing checkout.",
                            "diagnosis": {
                                "en": "Inventory-service was unavailable, so this high-risk item failed closed.",
                                "es": "El servicio de inventario no estaba disponible, por eso este artículo de alto riesgo se bloqueó por seguridad.",
                            },
                        },
                    }
                )
        elif path.requires_inventory and total_sellable <= 0 and not alternative_nodes and status != "blocked":
            violation = _inventory_violation(path.path_code)
            result.violations.setdefault(path.path_code, []).append(violation)
            status = "blocked"
            eligible = False
        elif path.requires_inventory and total_sellable <= 0 and alternative_nodes:
            total_sellable = sum(node.get("available_qty", 0) for node in alternative_nodes)

        confidence_score = inventory_row.get("confidence_score")
        confidence_band = inventory_row.get("confidence_band")
        if (
            settings.enable_low_confidence
            and eligible
            and total_sellable > 0
            and confidence_score is not None
            and float(confidence_score) < settings.low_confidence_threshold
        ):
            status = "low_confidence"
            eligible = True

        path_results.append(
            {
                "path_code": path.path_code,
                "eligible": eligible,
                "status": status,
                "violations": result.violations.get(path.path_code, []) + result.violations.get("__all__", []),
                "requirements": result.requirements.get(path.path_code, []) + result.requirements.get("__all__", []),
                "gates": result.gates.get(path.path_code, []) + result.gates.get("__all__", []),
                "inventory_available": total_sellable if path.requires_inventory else None,
                "confidence_score": confidence_score,
                "confidence_band": confidence_band,
                "confidence_reason": inventory_row.get("confidence_reason"),
                "last_verified_at": inventory_row.get("last_verified_at"),
                "alternative_nodes": alternative_nodes,
                "matched_zone_codes": zone_matches.get(path.path_code, []),
                "zone_explanation": zone_explanations.get(path.path_code),
                "fallback_applied": fallback_applied,
                "fallback_reason": fallback_reason,
            }
        )

    overall_eligible = any(path["eligible"] for path in path_results)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    response = {
        "item_id": str(item_id),
        "market_code": market_code,
        "eligible": overall_eligible,
        "paths": path_results,
        "warnings": warnings,
        "errors": [],
        "conflict_resolutions": result.conflict_resolutions,
        "rules_evaluated": result.rules_evaluated,
        "rules_suppressed": result.rules_suppressed,
        "rules_loaded": len(rules),
        "debug": {
            "rules_loaded": len(rules),
            "rules_triggered": len(unique_triggered),
            "rules_suppressed": result.rules_suppressed,
            "per_path_evaluations": per_path_evaluations,
        }
        if debug_mode
        else None,
        "evaluation_ms": elapsed_ms,
        "evaluated_at": datetime.now(PACIFIC).isoformat(),
        "seller_signal": seller_signal,
        "seller_performance": seller_performance,
        "market_summary": market_summary,
    }

    source_service, cause_code = derive_primary_cause(response)
    audit = EligibilityAuditLog(
        item_id=item_id,
        market_code=market_code,
        seller_id=seller_id,
        eligible=overall_eligible,
        request_payload={k: v for k, v in request_data.items() if not str(k).startswith("_")},
        response_payload={k: v for k, v in response.items() if k != "debug"},
        rules_evaluated=result.rules_evaluated,
        rules_suppressed=result.rules_suppressed,
        evaluation_ms=elapsed_ms,
        blocking_rule_names=_rule_names(path_results, "violations"),
        gating_rule_names=_rule_names(path_results, "gates"),
        warning_rule_names=[warning["rule_name"] for warning in warnings],
        path_statuses={path["path_code"]: path["status"] for path in path_results},
        diagnosis_source_service=source_service,
        diagnosis_root_cause_code=cause_code,
    )
    db.add(audit)
    await db.commit()
    return response


async def _load_market_summary(db: AsyncSession, market_code: str) -> dict | None:
    market_result = await db.execute(
        select(MarketRegulation).where(
            MarketRegulation.market_code == market_code,
            MarketRegulation.active.is_(True),
        )
    )
    market = market_result.scalar_one_or_none()
    if not market:
        return None
    paths_result = await db.execute(
        select(FulfillmentPath.path_code)
        .join(MarketFulfillment, FulfillmentPath.path_id == MarketFulfillment.path_id)
        .where(
            MarketFulfillment.market_code == market_code,
            MarketFulfillment.enabled.is_(True),
        )
        .order_by(MarketFulfillment.priority.desc())
    )
    return {
        "market_code": market.market_code,
        "display_name": market.display_name,
        "country_code": market.country_code,
        "region_code": market.region_code,
        "currency_code": market.currency_code,
        "language_codes": market.language_codes or [],
        "supported_paths": [row[0] for row in paths_result],
        "regulatory_summary": market.regulatory_summary or {},
    }


async def _load_paths(db: AsyncSession, market_code: str, seller_mode: bool) -> list:
    path_owner = "3p" if seller_mode else "1p"
    result = await db.execute(
        select(FulfillmentPath, MarketFulfillment)
        .join(MarketFulfillment, FulfillmentPath.path_id == MarketFulfillment.path_id)
        .where(
            and_(
                MarketFulfillment.market_code == market_code,
                MarketFulfillment.enabled.is_(True),
                FulfillmentPath.owner == path_owner,
            )
        )
        .order_by(MarketFulfillment.priority.desc())
    )
    return result.all()


async def _load_matching_rules(
    db: AsyncSession, market_code: str, item_data: dict, timestamp: datetime
) -> list:
    cached_rules = await get_cached_rules(market_code)
    if cached_rules:
        rules = [_hydrate_rule(rule_payload) for rule_payload in cached_rules]
    else:
        result = await db.execute(
            select(ComplianceRule)
            .where(
                and_(
                    ComplianceRule.enabled.is_(True),
                    or_(
                        ComplianceRule.market_codes == None,
                        ComplianceRule.market_codes.contains([market_code]),
                    ),
                )
            )
            .order_by(ComplianceRule.priority)
        )
        rules = result.scalars().all()
        await set_cached_rules(market_code, [_rule_to_cache_payload(rule) for rule in rules])

    item_tags = item_data.get("compliance_tags", [])
    item_category = item_data.get("category_path", "")
    filtered_rules = []
    for rule in rules:
        if rule.compliance_tags and not set(rule.compliance_tags).intersection(item_tags):
            continue
        if rule.category_paths and not any(
            item_category == category or item_category.startswith(f"{category}.")
            for category in rule.category_paths
        ):
            continue
        effective_from = getattr(rule, "effective_from", None)
        effective_until = getattr(rule, "effective_until", None)
        # Normalize naive timestamp to UTC to avoid TypeError with TIMESTAMPTZ columns
        ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        if effective_from and effective_from > ts:
            continue
        if effective_until and effective_until <= ts:
            continue
        filtered_rules.append(rule)
    return filtered_rules


def _dedupe_triggered(triggered_rules: list) -> list:
    seen = set()
    unique = []
    for rule in triggered_rules:
        if rule.rule_id in seen:
            continue
        seen.add(rule.rule_id)
        unique.append(rule)
    return unique


def _mark_suppressed(per_path_evaluations: list[dict], conflict_resolutions: list[dict]) -> None:
    suppression_map = {
        conflict["suppressed_rule_id"]: {
            "rule_id": conflict["winner_rule_id"],
            "rule_name": conflict["winner_rule_name"],
        }
        for conflict in conflict_resolutions
    }
    for evaluation in per_path_evaluations:
        for rule in evaluation["rules"]:
            if rule["matched"] and rule["rule_id"] in suppression_map:
                rule["suppressed"] = True
                rule["suppressed_by"] = suppression_map[rule["rule_id"]]
                rule["survived"] = False


def _apply_gate_context(result, seller_data: dict | None) -> None:
    if not seller_data:
        return
    current_values = {
        "seller_defect_rate": float(seller_data.get("defect_rate", 0)),
        "seller_on_time_rate": float(seller_data.get("on_time_rate", 0)),
        "seller_in_stock_rate": float(seller_data.get("in_stock_rate", 0) or 0),
        "seller_cancellation_rate": float(seller_data.get("cancellation_rate", 0) or 0),
        "seller_valid_tracking_rate": float(seller_data.get("valid_tracking_rate", 0) or 0),
        "seller_response_rate": float(seller_data.get("seller_response_rate", 0) or 0),
        "seller_return_rate": float(seller_data.get("return_rate", 0) or 0),
        "seller_item_not_received_rate": float(seller_data.get("item_not_received_rate", 0) or 0),
        "seller_negative_feedback_rate": float(seller_data.get("negative_feedback_rate", 0) or 0),
        "seller_uses_wfs": bool(seller_data.get("uses_wfs", False)),
        "seller_ipi_score": float(seller_data.get("ipi_score", 0) or 0),
        "seller_vat_registered": bool(seller_data.get("vat_registered", False)),
    }
    for gate_list in result.gates.values():
        for gate in gate_list:
            required = gate.get("required", {})
            current = {}
            gap = {}
            resolved = True
            for key, value in required.items():
                current_value = current_values.get(key)
                current[key] = current_value
                if current_value is None:
                    resolved = False
                    gap[key] = value
                    continue
                operator = "equal_to"
                expected = value
                if isinstance(value, dict):
                    operator = value.get("operator", "equal_to")
                    expected = value.get("value")
                if not _gate_passes(current_value, operator, expected):
                    resolved = False
                    if isinstance(expected, (int, float)) and isinstance(current_value, (int, float)):
                        gap[key] = round(float(expected) - float(current_value), 4)
                    else:
                        gap[key] = {
                            "operator": operator,
                            "expected": expected,
                            "current": current_value,
                        }
            gate["current"] = current
            gate["gap"] = gap
            gate["resolved"] = resolved


def _gate_passes(current_value, operator: str, expected) -> bool:
    if operator == "less_than":
        return float(current_value) < float(expected)
    if operator == "less_than_or_equal_to":
        return float(current_value) <= float(expected)
    if operator == "greater_than":
        return float(current_value) > float(expected)
    if operator == "greater_than_or_equal_to":
        return float(current_value) >= float(expected)
    if operator == "in":
        return current_value in expected
    if operator == "not_in":
        return current_value not in expected
    return current_value == expected


def _inventory_violation(path_code: str) -> dict:
    return {
        "rule_id": 0,
        "rule_name": "inventory_check",
        "action": "BLOCK",
        "reason": f"No inventory available for path {path_code}",
        "priority": 999,
        "metadata": {
            "source_service": "inventory-service",
            "source_entity": "inventory_positions",
            "source_field": "available_qty",
            "cause_code": "inventory_unavailable",
            "suggested_fix": "Restore inventory at the requested node or offer an alternative node.",
        },
    }


def _risk_tier_status(risk_tier: str) -> tuple[str, bool]:
    if risk_tier == "low":
        return "clear", True
    if risk_tier == "high":
        return "blocked", False
    return "gated", False


def _fallback_response(item_id, market_code: str, risk_tier: str, start: float, detail: str) -> dict:
    status, eligible = _risk_tier_status(risk_tier)
    path_result = {
        "path_code": "fallback",
        "eligible": eligible,
        "status": status,
        "violations": [],
        "requirements": [],
        "gates": [],
        "inventory_available": None,
        "confidence_score": None,
        "confidence_band": None,
        "confidence_reason": None,
        "last_verified_at": None,
        "alternative_nodes": [],
        "matched_zone_codes": [],
        "zone_explanation": None,
        "fallback_applied": True,
        "fallback_reason": detail,
    }
    return {
        "item_id": str(item_id),
        "market_code": market_code,
        "eligible": eligible,
        "paths": [path_result],
        "warnings": [],
        "errors": [],
        "conflict_resolutions": [],
        "rules_evaluated": 0,
        "rules_suppressed": 0,
        "rules_loaded": 0,
        "debug": None,
        "evaluation_ms": int((time.perf_counter() - start) * 1000),
        "evaluated_at": datetime.now(PACIFIC).isoformat(),
        "seller_signal": None,
        "seller_performance": None,
        "market_summary": None,
    }


def _rule_names(paths: list[dict], key: str) -> list[str]:
    names = {
        entry["rule_name"]
        for path in paths
        for entry in path.get(key, [])
        if entry.get("rule_name")
    }
    return sorted(names)


def _error_response(item_id, market_code: str, start: float, errors: list[str]) -> dict:
    return {
        "item_id": str(item_id),
        "market_code": market_code,
        "eligible": False,
        "paths": [],
        "warnings": [],
        "errors": errors,
        "conflict_resolutions": [],
        "rules_evaluated": 0,
        "rules_suppressed": 0,
        "rules_loaded": 0,
        "debug": None,
        "evaluation_ms": int((time.perf_counter() - start) * 1000),
        "evaluated_at": datetime.now(PACIFIC).isoformat(),
        "seller_signal": None,
        "seller_performance": None,
        "market_summary": None,
    }

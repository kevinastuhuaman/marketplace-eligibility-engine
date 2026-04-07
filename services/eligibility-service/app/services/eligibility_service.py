"""Eligibility evaluation orchestrator. Makes cross-service calls, runs rules, returns result."""
import time
from uuid import UUID
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.compliance import ComplianceRule
from app.models.fulfillment import FulfillmentPath, MarketFulfillment
from app.models.audit import EligibilityAuditLog
from app.clients import item_client, inventory_client, seller_client
from app.engine.variables import build_variables
from app.engine.evaluator import (
    evaluate_rules,
    resolve_and_accumulate,
    resolve_requirements,
    determine_path_status,
)
from shared.constants import WALMART_SELLER_ID


async def evaluate(request_data: dict, db: AsyncSession) -> dict:
    """Main evaluation orchestrator."""
    start = time.perf_counter()

    try:
        item_id = (
            UUID(request_data["item_id"])
            if isinstance(request_data["item_id"], str)
            else request_data["item_id"]
        )
        market_code = request_data["market_code"]
        seller_id_raw = request_data.get("seller_id")
        seller_id = UUID(seller_id_raw) if seller_id_raw else None
        timestamp = request_data["timestamp"]
        state = request_data["customer_location"]["state"]
    except (KeyError, TypeError) as e:
        return _error_response(
            request_data.get("item_id", "unknown"),
            request_data.get("market_code", "unknown"),
            request_data.get("timestamp", datetime.now(PACIFIC).isoformat()),
            start,
            [f"Missing required field: {e}"],
        )

    # Validate market_code matches state
    expected_state = market_code.split("-")[1] if "-" in market_code else None
    if expected_state and expected_state != state:
        return _error_response(
            item_id,
            market_code,
            timestamp,
            start,
            [
                f"customer_location.state '{state}' does not match market_code '{market_code}'"
            ],
        )

    # --- Step 1: Load item from item-service ---
    item_data = await item_client.get_item(item_id)
    if not item_data:
        return _error_response(
            item_id, market_code, timestamp, start, ["Item not found"]
        )

    # --- Step 2: If seller, verify offer + load metrics ---
    seller_data = None
    if seller_id:
        offer = await seller_client.check_offer(seller_id, item_id)
        if not offer.get("exists") or not offer.get("active"):
            return _error_response(
                item_id,
                market_code,
                timestamp,
                start,
                ["Seller does not offer this item"],
            )
        seller_data = await seller_client.get_seller(seller_id)
        if not seller_data:
            return _error_response(
                item_id, market_code, timestamp, start, ["Seller not found"]
            )

    # --- Step 3: Load fulfillment paths for this market ---
    path_owner = "3p" if seller_id else "1p"
    paths_result = await db.execute(
        select(FulfillmentPath, MarketFulfillment)
        .join(
            MarketFulfillment,
            FulfillmentPath.path_id == MarketFulfillment.path_id,
        )
        .where(
            and_(
                MarketFulfillment.market_code == market_code,
                MarketFulfillment.enabled == True,
                FulfillmentPath.owner == path_owner,
            )
        )
        .order_by(MarketFulfillment.priority.desc())
    )
    paths = paths_result.all()

    if not paths:
        return _error_response(
            item_id,
            market_code,
            timestamp,
            start,
            [
                f"No {path_owner} fulfillment paths enabled for market {market_code}"
            ],
        )

    # --- Step 4: Load matching compliance rules ---
    rules = await _load_matching_rules(db, market_code, item_data, timestamp)

    # --- Step 5: Load inventory ---
    inv_seller_id = seller_id if seller_id else WALMART_SELLER_ID
    path_ids = [fp.path_id for fp, mf in paths]
    inventory_data = await inventory_client.get_availability(
        item_id, path_ids, inv_seller_id
    )
    inv_by_path = {p["path_id"]: p for p in inventory_data.get("paths", [])}

    # --- Step 6: Evaluate rules for each path ---
    debug_mode = request_data.get("_debug", False)
    per_path_evals = []
    path_results = []
    all_triggered = []

    for fp, mf in paths:
        variables = build_variables(
            request_data, item_data, seller_data, fp.path_code
        )
        triggered = evaluate_rules(rules, variables)
        all_triggered.extend(triggered)

        if debug_mode:
            triggered_ids = {t.rule_id for t in triggered}
            per_path_evals.append({
                "path_code": fp.path_code,
                "_triggered_ids": triggered_ids,
                "_rules_snapshot": [
                    {
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "rule_type": r.rule_type,
                        "action": r.action,
                        "priority": r.priority,
                        "conflict_group": r.conflict_group,
                        "blocked_paths": r.blocked_paths or [],
                        "reason": r.reason,
                        "rule_definition": r.rule_definition,
                    }
                    for r in rules
                ],
            })

    # --- Step 7: Resolve conflicts and accumulate ---
    # Deduplicate triggered rules (same rule may trigger for multiple paths)
    seen = set()
    unique_triggered = []
    for t in all_triggered:
        if t.rule_id not in seen:
            seen.add(t.rule_id)
            unique_triggered.append(t)

    result = resolve_and_accumulate(unique_triggered)

    # Enrich debug per-path evaluations with suppression state
    if debug_mode:
        suppression_map = {}
        for cr in result.conflict_resolutions:
            suppression_map[cr["suppressed_rule_id"]] = {
                "rule_id": cr["winner_rule_id"],
                "rule_name": cr["winner_rule_name"],
            }
        for ppe in per_path_evals:
            triggered_ids = ppe.pop("_triggered_ids")
            ppe["rules"] = []
            for rs in ppe.pop("_rules_snapshot"):
                rid = rs["rule_id"]
                matched = rid in triggered_ids
                suppressed = matched and rid in suppression_map
                rs["matched"] = matched
                rs["suppressed"] = suppressed
                rs["suppressed_by"] = suppression_map.get(rid) if suppressed else None
                rs["survived"] = matched and not suppressed
                ppe["rules"].append(rs)

    # --- Step 8: Resolve REQUIRE rules against context ---
    context_vars = request_data.get("context") or {}
    full_vars = {
        "customer_age": context_vars.get("customer_age"),
        "requested_quantity": context_vars.get("requested_quantity"),
        "background_check_status": context_vars.get("background_check_status"),
    }
    result = resolve_requirements(result, full_vars)

    # --- Step 9: Build per-path results ---
    for fp, mf in paths:
        status, eligible = determine_path_status(fp.path_code, result)

        inv_path = inv_by_path.get(fp.path_id, {})
        inv_available = inv_path.get("total_sellable", 0)

        # Check inventory
        if fp.requires_inventory and inv_available <= 0 and status != "blocked":
            status = "blocked"
            eligible = False
            if fp.path_code not in result.violations:
                result.violations[fp.path_code] = []
            result.violations[fp.path_code].append(
                {
                    "rule_id": 0,
                    "rule_name": "inventory_check",
                    "action": "BLOCK",
                    "reason": f"No inventory available for path {fp.path_code}",
                    "priority": 999,
                    "metadata": {},
                }
            )

        path_results.append(
            {
                "path_code": fp.path_code,
                "eligible": eligible,
                "status": status,
                "violations": result.violations.get(fp.path_code, [])
                + result.violations.get("__all__", []),
                "requirements": result.requirements.get(fp.path_code, [])
                + result.requirements.get("__all__", []),
                "gates": result.gates.get(fp.path_code, [])
                + result.gates.get("__all__", []),
                "inventory_available": inv_available,
            }
        )

    overall_eligible = any(p["eligible"] for p in path_results)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    now = datetime.now(PACIFIC)

    response = {
        "item_id": str(item_id),
        "market_code": market_code,
        "eligible": overall_eligible,
        "paths": path_results,
        "warnings": result.warnings,
        "errors": [],
        "conflict_resolutions": result.conflict_resolutions,
        "rules_evaluated": result.rules_evaluated,
        "rules_suppressed": result.rules_suppressed,
        "rules_loaded": len(rules),
        "debug": {
            "rules_loaded": len(rules),
            "rules_triggered": len(unique_triggered),
            "rules_suppressed": result.rules_suppressed,
            "per_path_evaluations": per_path_evals,
        } if debug_mode else None,
        "evaluation_ms": elapsed_ms,
        "evaluated_at": now.isoformat(),
    }

    # --- Step 10: Log audit ---
    audit_response = {k: v for k, v in response.items() if k != "debug"}
    audit_request = {k: v for k, v in request_data.items() if not k.startswith("_")}
    audit = EligibilityAuditLog(
        item_id=item_id,
        market_code=market_code,
        seller_id=seller_id,
        eligible=overall_eligible,
        request_payload=audit_request,
        response_payload=audit_response,
        rules_evaluated=result.rules_evaluated,
        rules_suppressed=result.rules_suppressed,
        evaluation_ms=elapsed_ms,
    )
    db.add(audit)
    await db.commit()

    return response


async def _load_matching_rules(
    db: AsyncSession, market_code: str, item_data: dict, timestamp
) -> list:
    """Load compliance rules matching this item/market/time."""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)

    query = (
        select(ComplianceRule)
        .where(
            and_(
                ComplianceRule.enabled == True,
                or_(
                    ComplianceRule.market_codes == None,
                    ComplianceRule.market_codes.contains([market_code]),
                ),
                or_(
                    ComplianceRule.compliance_tags == None,
                    ComplianceRule.compliance_tags.overlap(
                        item_data.get("compliance_tags", [])
                    ),
                ),
                ComplianceRule.effective_from <= timestamp,
                or_(
                    ComplianceRule.effective_until == None,
                    ComplianceRule.effective_until > timestamp,
                ),
            )
        )
        .order_by(ComplianceRule.priority)
    )

    result = await db.execute(query)
    rules = result.scalars().all()

    # Post-filter on category_paths: a rule with category_paths set should only
    # match items whose category_path is equal to or a descendant of one of the
    # rule's category paths (mimics ltree <@ semantics).
    item_cat = item_data.get("category_path", "")
    filtered = []
    for rule in rules:
        if rule.category_paths is None:
            # Rule has no category scope — applies to all items
            filtered.append(rule)
        elif not item_cat:
            # Item has no category — skip category-scoped rules
            continue
        else:
            for rcp in rule.category_paths:
                if item_cat == rcp or item_cat.startswith(rcp + "."):
                    filtered.append(rule)
                    break
    rules = filtered

    return rules


def _error_response(item_id, market_code, timestamp, start, errors):
    elapsed_ms = int((time.perf_counter() - start) * 1000)
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
        "evaluation_ms": elapsed_ms,
        "evaluated_at": datetime.now(PACIFIC).isoformat(),
    }

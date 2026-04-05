# Walmart Transactability Engine

A distributed system that answers the hardest question in e-commerce at Walmart scale:
**"Can this customer buy this item, right now, through this fulfillment method?"**

4 microservices | Event-driven | 4 action types | Real conflict resolution | 57 tests passing

---

## The Problem

At Walmart scale (420M+ SKUs, 50 states, 4 fulfillment methods, thousands of 3P sellers), item eligibility is a combinatorial explosion. A bottle of wine might be legal in Colorado but prohibited in Utah. Pool chlorine can be picked up in-store but never shipped. Fireworks are only sellable in June and July -- and only in states that allow them. An item's "transactability" depends on geography, time, fulfillment path, seller trust, inventory, and regulatory compliance -- all evaluated simultaneously, with conflicting rules resolved deterministically.

## Quick Start

```bash
docker compose up -d --build
# Wait ~30s for all health checks to pass
python3 -m scripts.seed
```

Test it -- wine blocked in Utah:

```bash
curl -s -X POST http://localhost/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "<wine-item-id-from-seed-output>",
    "market_code": "US-UT",
    "customer_location": {"state": "UT", "zip": "84101"},
    "timestamp": "2026-07-04T14:00:00-06:00"
  }' | python3 -m json.tool
```

Expected: `"eligible": false` with violation `utah_alcohol_prohibition` on all 4 paths.

## Architecture

```
                         +------------------+
                         |      Nginx       |
                         |   API Gateway    |
                         |    (port 80)     |
                         +--------+---------+
                                  |
            +----------+----------+----------+----------+
            |          |                     |          |
      +-----+----+ +--+--------+     +------+---+ +---+-------+
      |   Item   | |Eligibility|     |Inventory | |  Seller   |
      | Service  | |  Service  |     | Service  | |  Service  |
      | (8001)   | |  (8002)   |     |  (8003)  | |  (8004)   |
      +-----+----+ +--+---+----+     +------+---+ +---+-------+
            |          |   |                |          |
            +----------+---+----------------+----------+
                           |
                  +--------+--------+
                  |    PostgreSQL    |    +----------+
                  |  (ltree, JSONB) |    |  Redis 7 |
                  |   4 schemas     |    | (Streams)|
                  +-----------------+    +----------+
```

| Service | Owns | Role |
|---------|------|------|
| **Item Service** | SKU catalog, categories, compliance tags | Source of truth for what an item is |
| **Eligibility Service** | Rules, evaluation engine, audit log | Orchestrates cross-service calls, runs rule engine |
| **Inventory Service** | Stock positions, fulfillment nodes | Tracks available/reserved qty per path per seller |
| **Seller Service** | 3P seller profiles, trust tiers, offers | Manages seller metrics and item-seller relationships |

**Communication:** Synchronous HTTP for evaluation (Eligibility calls Item, Inventory, and Seller during each request). Redis Streams for state change events (inventory adjustments, seller metric updates). PostgreSQL with per-service schemas (`item_svc`, `eligibility_svc`, `inventory_svc`, `seller_svc`) and `ltree` for category hierarchy.

## The 4 Action Types

| Action | Severity | Behavior | Example |
|--------|----------|----------|---------|
| **BLOCK** | Hard stop | Path is ineligible, no override | Wine to Utah -- state law prohibits |
| **WARN** | Advisory | Path stays eligible, warning attached | Prop 65 label on supplements in CA |
| **REQUIRE** | Conditional | Eligible if condition met, escalates to BLOCK if failed | Firearm purchase requires age >= 21 |
| **GATE** | Seller capability | Seller must meet threshold to use this path | 3P seller needs < 3% defect rate for hazmat |

The key insight: binary eligible/not-eligible is insufficient. REQUIRE lets the system say "yes, if you verify age" without blocking the entire flow. GATE separates seller capability from product compliance.

## 10 Demo Scenarios

These are the talking points. Each one demonstrates a different dimension of the engine.

| # | Scenario | What It Proves | Expected Outcome |
|---|----------|----------------|------------------|
| 1 | **Wine to Utah vs Colorado** | Geographic compliance | UT: BLOCKED all paths. CO: eligible with age verification |
| 2 | **Pool Chlorine Paths** | Path-level differentiation | Shipping BLOCKED (hazmat), pickup CLEAR |
| 3 | **Fireworks: TX July / TX October / MA** | Temporal + geographic layering | Jul TX: eligible. Oct TX: GATED (out of season). MA: BLOCKED (state ban) |
| 4 | **Supplement in California** | Advisory warnings without blocking | Eligible with Prop 65 WARNING attached |
| 5 | **Rifle: 1P with Age / No Age / Underage** | REQUIRE escalation to BLOCK | Age 25: clear. No age: conditional. Age 17: BLOCKED |
| 6 | **Hazmat Seller Quality Gate** | Seller metric thresholds | ChemSupply (4.5% defect rate) GATED from marketplace |
| 7 | **3P Alcohol: Trusted vs New Seller** | Seller trust tiers | Acme Wines (trusted): passes. NewSeller123 (new): GATED |
| 8 | **Electronics: Trusted vs New Seller** | Category-specific seller gates | TechGear Pro (trusted): passes. NewSeller123: GATED |
| 9 | **Pseudoephedrine Quantity Limit** | Quantity-based compliance (CMEA) | qty=2: eligible. qty=5: BLOCKED |
| 10 | **Inventory Depletion** | Real-time stock check | Available (qty=50): eligible. After depletion: BLOCKED |

## Conflict Resolution

When multiple rules fire for the same item, conflicts are resolved deterministically:

1. **Conflict groups** -- Rules in the same group compete. The winner is selected by scope specificity (item > seller > category > geographic > temporal), then priority.
2. **Safety property** -- A less-restrictive rule never suppresses a more-restrictive one. If a WARN wins the group but a BLOCK also fired, the BLOCK survives.
3. **Accumulation** -- Surviving rules accumulate: BLOCKs go to `violations`, WARNs to `warnings`, REQUIREs to `requirements`, GATEs to `gates`.

Example: In Massachusetts, the `ma_fireworks_total_ban` (BLOCK, geographic) and `fireworks_carrier_ban` (BLOCK, product) both fire. They are in the same conflict group. The geographic ban wins on scope, but the carrier ban is equally restrictive -- so both survive. The item is blocked regardless.

## API Contract

**Request:** `POST /v1/evaluate`

```json
{
  "item_id": "uuid",
  "market_code": "US-UT",
  "customer_location": { "state": "UT", "zip": "84101" },
  "timestamp": "2026-07-04T14:00:00-06:00",
  "seller_id": "uuid (optional, triggers 3P path)",
  "context": { "customer_age": 25, "requested_quantity": 2 }
}
```

**Response:**

```json
{
  "item_id": "uuid",
  "market_code": "US-UT",
  "eligible": false,
  "paths": [
    {
      "path_code": "ship_to_home",
      "eligible": false,
      "status": "blocked",
      "violations": [{ "rule_name": "utah_alcohol_prohibition", "reason": "..." }],
      "requirements": [],
      "gates": [],
      "inventory_available": 50
    }
  ],
  "warnings": [],
  "errors": [],
  "conflict_resolutions": [],
  "rules_evaluated": 3,
  "rules_suppressed": 0,
  "evaluation_ms": 12,
  "evaluated_at": "2026-07-04T14:00:01-07:00"
}
```

## Design Decisions

| Decision | What We Chose | Why |
|----------|---------------|-----|
| 4 microservices over monolith | Item, Eligibility, Inventory, Seller as separate services | Each domain has different ownership, scaling, and data models at Walmart |
| BLOCK/WARN/REQUIRE/GATE over binary | 4 action types with distinct semantics | Binary eligible/not loses critical information. "Requires age verification" is not the same as "prohibited" |
| Conflict groups over simple accumulation | Scope-based priority with safety property | Prevents contradictory rules from producing incoherent results. A state ban and a federal guideline should not both appear as separate violations |
| 1P/3P path separation | Seller presence determines which fulfillment paths evaluate | 1P and 3P have fundamentally different compliance requirements. Firearms are legal at 1P pickup but prohibited on 3P marketplace |
| Fail-closed compliance | REQUIRE escalates to BLOCK when condition fails | Underage buyer + firearm = hard block, not "conditional." Safety-critical rules must fail closed |
| Redis Streams for observability | Event log for inventory/seller changes | Decouples state mutation from evaluation. Foundation for event-driven re-evaluation without adding latency to the read path |
| PostgreSQL ltree for categories | Hierarchical category matching | `chemicals.pool` matches rules on `chemicals.*` without application-level tree traversal |
| Per-service DB schemas | `item_svc`, `eligibility_svc`, `inventory_svc`, `seller_svc` | Simulates service-owned datastores. Each service manages its own schema and migrations |

## Test Suite

57 tests total, two layers:

- **29 unit tests** (`tests/test_evaluator.py`) -- Pure function tests of the rule engine. No database, no Docker, no network. Tests condition evaluation, conflict resolution, REQUIRE escalation, and path status determination.
- **28 integration tests** (`tests/test_scenarios.py`) -- All 10 scenarios end-to-end through Nginx, hitting all 4 services with seeded data. Validates the full orchestration path from API gateway to response.

```bash
# Unit tests (no Docker required)
pytest tests/test_evaluator.py -v

# Integration tests (requires docker compose up + seed)
pytest tests/test_scenarios.py -v
```

## What I'd Build Next

- **What-if simulator** -- "What happens if Utah legalizes alcohol delivery?" Preview rule changes before deployment.
- **Compliance drift detection** -- Monitor for rules that stopped firing (regulation changed?) or fire unexpectedly (data quality issue?).
- **Redis-backed eligibility cache** -- Cache evaluation results keyed by (item, market, path) with TTL-based invalidation from inventory events.
- **Event-driven re-evaluation** -- Inventory depletion triggers automatic re-evaluation and pushes updated eligibility to the storefront.
- **Rule versioning and rollback** -- Temporal rule history with point-in-time evaluation for audit and compliance.

## Built With

Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16 (ltree, JSONB), Redis 7 (Streams), Nginx 1.27, Docker Compose, Streamlit (dashboard), pytest

## About

Built as a portfolio project demonstrating understanding of Walmart's transactability architecture. Based on research of Walmart's engineering blog posts on event-sourced inventory, item setup orchestration, and domain-driven microservices. The 25 compliance rules model real regulatory constraints (Utah Code 32B, 49 CFR 173, CMEA, CA Prop 65, DOT/PHMSA) applied to real product categories.

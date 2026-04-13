# Marketplace Eligibility Engine

[![CI](https://github.com/kevinastuhuaman/marketplace-eligibility-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/kevinastuhuaman/marketplace-eligibility-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)

A distributed compliance and eligibility engine for multi-market e-commerce.
**"Can this customer buy this item, right now, through this fulfillment method?"**

4 microservices | 25 compliance rules | 24 UI scenarios | 12 markets | Event-driven

---

## The Problem

At scale (420M+ SKUs, 50 states, 4 fulfillment methods, thousands of 3P sellers), item eligibility is a combinatorial explosion. A bottle of wine might be legal in Colorado but prohibited in Utah. Pool chlorine can be picked up in-store but never shipped. Fireworks are only sellable in June and July -- and only in states that allow them. An item's eligibility depends on geography, time, fulfillment path, seller trust, inventory, and regulatory compliance -- all evaluated simultaneously, with conflicting rules resolved deterministically.

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

## Component Showcase

This project implements 8 independent, production-grade components -- each demonstrating a distinct architectural pattern used by major marketplace platforms.

### 1. Rule Engine with Conflict Resolution

Amazon's FBA system uses 40+ distinct ineligibility reason codes. Shopify takes the opposite approach with publication-based inclusion. This engine implements a middle path: scope-ranked conflict resolution with a safety property that ensures a less-restrictive rule never suppresses a more-restrictive one. Rules fire as BLOCK, WARN, REQUIRE, or GATE, and conflicts within the same group are resolved by scope specificity (item > seller > regulation > category > geographic > temporal).

**Key files:** `services/eligibility-service/app/engine/evaluator.py`, `services/eligibility-service/app/engine/variables.py`

### 2. Event-Driven Microservices

Domain-driven bounded contexts mirroring how large retailers separate catalog, inventory, compliance, and seller management. Each service owns its PostgreSQL schema, publishes state changes via Redis Streams, and the evaluation path orchestrates synchronous HTTP calls across all four. The architecture supports independent scaling and deployment per domain.

**Key files:** `services/shared/redis_streams.py`, each service's `app/main.py`

### 3. Geo-Restriction Zone System

Major retailers are replacing ZIP-code-level blocking with address-level precision (inspired by Uber's H3 hex-grid system). This engine implements polygon + hex-cell restriction zones, so an alcohol delivery rule can block a school buffer zone without denying thousands of eligible households in the same ZIP code. Coarse hex-cell matching enables fast precomputation.

**Key files:** `services/eligibility-service/app/models/geo_restriction_zone.py`, `services/eligibility-service/app/services/geo_service.py`

### 4. Seller Trust Scoring (IPI)

Amazon's IPI scoring determines FBA storage limits. eBay's seller levels gate listing visibility. This engine implements a continuous 180-910 score computed from defect rate, return rate, on-time delivery, cancellation rate, and more. The score maps to trust tiers (new/standard/trusted/top_rated) that feed eligibility gates and fulfillment service recommendations.

**Key files:** `services/seller-service/app/services/ipi_service.py`, `services/seller-service/app/services/performance_service.py`

### 5. Probabilistic Inventory

Instacart's picker feedback loops and Target's RFID rollout (65% to 95% in-stock accuracy) show that binary available/unavailable is insufficient for modern commerce. This engine tracks confidence-weighted availability (0.0-1.0) with staleness signals, OOS frequency, and verification source. The system can say "available, but stale and low confidence" instead of overpromising.

**Key files:** `services/inventory-service/app/models/inventory.py`, `services/inventory-service/app/services/confidence_service.py`

### 6. Circuit Breaker with Risk-Tiered Fallback

Not a generic circuit breaker. When an upstream service fails, the item's risk tier determines behavior: low-risk items proceed with warnings, medium-risk items gate to human review, high-risk items fail closed. The platform degrades intentionally, not randomly.

**Key files:** `services/eligibility-service/app/services/circuit_breaker_service.py`, `services/eligibility-service/app/services/fallback_cache_service.py`

### 7. Diagnosis Engine

Rule evaluations produce machine-readable results. The diagnosis endpoint traces exactly which rule, service, and data field caused a block, then generates a human-readable explanation and concrete fix suggestion. A merchandiser sees "Missing NOM certification in Mexico" instead of "item unavailable."

**Key files:** `services/eligibility-service/app/services/diagnosis_service.py`, `services/eligibility-service/app/api/routes.py`

### 8. Global Compliance Framework

Mexico NOM certification, Chile lithium import restrictions, Costa Rica RTCA registration, Canada bilingual labeling requirements. Market differences are parameterized as data in a regulations table -- not branching code. Adding a new market is a matter of loading regulations and rule metadata into the same engine.

**Key files:** `services/shared/scenario_data.py`, `services/eligibility-service/app/models/market_regulation.py`

## The 4 Action Types

| Action | Severity | Behavior | Example |
|--------|----------|----------|---------|
| **BLOCK** | Hard stop | Path is ineligible, no override | Wine to Utah -- state law prohibits |
| **WARN** | Advisory | Path stays eligible, warning attached | Prop 65 label on supplements in CA |
| **REQUIRE** | Conditional | Eligible if condition met, escalates to BLOCK if failed | Firearm purchase requires age >= 21 |
| **GATE** | Seller capability | Seller must meet threshold to use this path | 3P seller needs < 3% defect rate for hazmat |

The key insight: binary eligible/not-eligible is insufficient. REQUIRE lets the system say "yes, if you verify age" without blocking the entire flow. GATE separates seller capability from product compliance.

## Scenario Catalog

24 interactive UI scenarios covering the full spectrum of eligibility decisions:

- 1-10. Core scenarios: wine DTC restrictions, hazmat path blocking, fireworks seasonal gates, Prop 65 warnings, firearms age verification, seller trust demotion, inventory depletion
- 11\. Cross-System Diagnosis Cascade
- 12\. Offer Exists, Inventory Missing
- 13\. School-Zone Alcohol Delivery (geo-restriction)
- 14\. Mexico NOM Certification
- 15\. Mexico IEPS + Spanish Label
- 16\. Chile Black Label + Lithium Import
- 17\. Costa Rica RTCA + VAT Registration
- 18\. Canada Bilingual + Metric Units
- 19\. FC Clear, Store Low Confidence (probabilistic inventory)
- 20\. Inventory Service Outage Fallback (circuit breaker)
- 21\. Seller IPI Split (trusted vs. new seller)
- 22\. Nearby Store Rescue (multi-store pooling)
- 23\. Impact Dashboard Story (analytics)
- 24\. Side-by-Side Market Compare

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
| 4 microservices over monolith | Item, Eligibility, Inventory, Seller as separate services | Each domain has different ownership, scaling, and data models in a large marketplace |
| BLOCK/WARN/REQUIRE/GATE over binary | 4 action types with distinct semantics | Binary eligible/not loses critical information. "Requires age verification" is not the same as "prohibited" |
| Conflict groups over simple accumulation | Scope-based priority with safety property | Prevents contradictory rules from producing incoherent results. A state ban and a federal guideline should not both appear as separate violations |
| 1P/3P path separation | Seller presence determines which fulfillment paths evaluate | 1P and 3P have fundamentally different compliance requirements. Firearms are legal at 1P pickup but prohibited on 3P marketplace |
| Fail-closed compliance | REQUIRE escalates to BLOCK when condition fails | Underage buyer + firearm = hard block, not "conditional." Safety-critical rules must fail closed |
| Redis Streams for observability | Event log for inventory/seller changes | Decouples state mutation from evaluation. Foundation for event-driven re-evaluation without adding latency to the read path |
| PostgreSQL ltree for categories | Hierarchical category matching | `chemicals.pool` matches rules on `chemicals.*` without application-level tree traversal |
| Per-service DB schemas | `item_svc`, `eligibility_svc`, `inventory_svc`, `seller_svc` | Simulates service-owned datastores. Each service manages its own schema and migrations |

See [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) for the full architectural philosophy and operational learnings.

## Test Suite

- **29 unit tests** (`tests/test_evaluator.py`) -- Pure function tests of the rule engine. No database, no Docker, no network.
- **28 integration tests** (`tests/test_scenarios.py`) -- All 10 core scenarios end-to-end through Nginx, hitting all 4 services with seeded data.
- Feature tests for geo restrictions, global markets, seller IPI, inventory confidence, diagnosis, and batch evaluation.

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

## Industry Research

This system is informed by publicly documented engineering patterns from major retail platforms. The [Architecture Blueprint](ARCHITECTURE.md) includes research on event-sourced inventory systems, item setup orchestration pipelines, domain-driven microservice topologies, and cross-industry eligibility patterns from Amazon, Shopify, eBay, Target, Instacart, and Alibaba/JD.

## Built With

Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16 (ltree, JSONB), Redis 7 (Streams), Nginx 1.27, Docker Compose, React 18 (Vite + TypeScript + Tailwind), Streamlit (dashboard), Playwright (e2e), pytest

## License

[MIT](LICENSE) -- Kevin Astuhuaman, 2026

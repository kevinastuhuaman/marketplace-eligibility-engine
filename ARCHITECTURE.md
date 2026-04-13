# Marketplace Eligibility Engine — Architecture Blueprint

## What Is Transactability?

"Eligibility" (sometimes called "transactability" in large retail platforms) refers to whether an item can be sold to a specific customer, through a specific fulfillment path, in a specific market, at a specific time. It's not a single system — it's an **emergent property of 7+ independent services** each evaluating their own eligibility dimension.

An item is "transactable" when ALL of these pass:
1. The product exists and is published in the catalog
2. The seller is authorized to sell it
3. It passes compliance/regulatory rules for the target market
4. It's in stock at a fulfillment node that can reach the customer
5. The fulfillment path supports the item (weight, hazmat, temperature)
6. The customer's geography allows it (state laws, shipping zones)
7. The time window allows it (alcohol hours, flash sales, seasonal gates)

## Industry Architecture Research: How Large Retail Platforms Handle Eligibility

### Architecture: Domain-Driven Bounded Contexts

Large marketplace platforms do NOT have a single "eligibility engine." They use **DDD bounded contexts** where each domain owns its own eligibility dimension:

| Bounded Context | Owns | Scale |
|----------------|------|-------|
| **Catalog** | Product validity, taxonomy, attributes | 20-40M item setups/day |
| **Inventory** | Available-to-sell (ATS) per node | Billions of products × 100K+ nodes |
| **Fulfillment (GIF)** | Ship-from-store, pickup, delivery radius | Global: US + international |
| **Marketplace** | Seller offer validation, compliance holds | 3P seller restrictions |
| **Cart** | Quantity/weight rules, bundle validation | Request-time enforcement |
| **Fraud/Trust** | Graph neural networks for anomaly detection | Real-time scoring |
| **Pricing** | Price calculation, promotions, discounts | 60-80M price updates/day |

### Item Setup Orchestrator ("Hyperloop")

Three-stage pipeline processing items into the catalog:
```
Spec Parser → Feed Ingestor → Item Setup Orchestrator
                                    ↓
                    Routes simultaneously to:
                    - Pricing Service
                    - Supplier Service
                    - Logistics Service
                    - Cost Service
```
- 60 dedicated machines, 2-hour SLA
- Kafka topics feed the pipeline
- Orchestration pattern for onboarding, choreography for ongoing changes

### Inventory: Event-Sourced on Cosmos DB

**Core formula:** `Available to Sell (ATS) = OnHand - ActiveReservations`

Event types that change eligibility:
- `Reserved` — customer locks inventory
- `InventoryUpdated` — supply changes
- `NodeDisabled` / `NodeEnabled` — warehouse closures
- `OrderShipped` / `OrderCancelled` — fulfillment completion
- `ItemDissociatedFromNode` — remove item-to-node sellability
- `BusinessRuleApplied` — **category/department-level holds translated to product level** (this is the compliance overlay)

Scale: 300K+ orders/minute, single-digit ms latency via Cosmos DB Change Feed.

### Tech Stack (Confirmed)

| Layer | Technology |
|-------|-----------|
| Orchestration | Azure Kubernetes Service (AKS), Docker |
| Service mesh | Istio (sticky sessions, fault injection) |
| Primary DB | Azure Cosmos DB (event store, inventory) |
| Caching | Redis + in-memory with TTL |
| Event streaming | Apache Kafka (billions/day, multi-DC) |
| Stream processing | Storm, Spark, Akka Streams, plain Java |
| Data warehouse | BigQuery, Hive |
| Observability | Splunk, Prometheus + Grafana |
| Cloud | Azure (compute/DB) + GCP (batch/analytics) |
| Product graph | Cosmos DB (Gremlin) + FAISS embeddings |

## Cross-Industry Patterns (Amazon, Shopify, eBay)

### Universal 5-Layer Eligibility Stack

Every major retailer uses this pattern:
```
Layer 1: Catalog Eligibility      — "Does this product TYPE exist?"
Layer 2: Seller Eligibility       — "Can THIS SELLER sell this product?"
Layer 3: Compliance Eligibility   — "Does it meet REGULATORY requirements?"
Layer 4: Fulfillment Eligibility  — "Can it be fulfilled via METHOD X from LOCATION Y?"
Layer 5: Geographic Eligibility   — "Can it be sold/shipped to REGION Z?"
```

### Amazon's Three-Layer Model (Most Documented)

1. **Product Type Definitions API** — JSON Schema per product type (catalog gate)
2. **Listings Restrictions API** — Per-seller gating with 3 reason codes: `APPROVAL_REQUIRED`, `ASIN_NOT_FOUND`, `NOT_ELIGIBLE`
3. **FBA Inbound Eligibility API** — 40+ ineligibility reason codes (hazmat, brand registry, dimensions, tax docs)

Key pattern: **Schema-as-Contract** — product requirements externalized as JSON Schema, validation against schema IS the eligibility rule.

### Shopify's Object Model (Most Transparent)

```
Market (geographic) → Catalog (product set) → Publication (channel) → DeliveryProfile (fulfillment) → FulfillmentOrder (runtime)
```
Each layer independently gates visibility and purchasability.

### eBay's Trust-Gated Model

Seller levels (Top Rated → Above Standard → Below Standard) dynamically gate:
- Which categories you can list in
- Which fulfillment options are available
- Search visibility and fees

Pattern: **"Prove yourself, then earn capabilities"** vs Amazon's **"Apply for approval"**

### Key Pattern: Orchestration for Onboarding, Choreography for Ongoing

- Item setup = orchestration (central coordinator, sequential validation)
- Ongoing state changes = choreography (event-driven, each service reacts independently)

---

## What We're Building

### The Compliance Gap: What Public Documentation Misses

The compliance/regulatory layer is the **most opaque part** of large retail architectures — there are virtually no public blog posts about alcohol rules, hazmat shipping, age-restricted items, or state-by-state regulations. This engine fills that gap.

### Our System: Transactability Resolution Engine

A working simulation of how item eligibility is evaluated across multiple dimensions, with emphasis on:

1. **Item Graph** — Parent/child SKUs, variants, bundles with PostgreSQL `ltree`
2. **Fulfillment Path Routing** — Multiple paths per item (ship-to-home, pickup, ship-from-store, 3P marketplace)
3. **Compliance/Policy Engine** — State-by-state rules, hazmat, age restrictions, time windows
4. **Event-Driven Inventory** — Real-time stock changes flowing through Redis Streams
5. **Seller Trust Scoring** — Progressive gating based on seller metrics
6. **Operational Dashboard** — Coverage gaps, rule conflicts, what-if simulation

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                   API Gateway (Nginx)                 │
│                     localhost:80                      │
├──────────────┬───────────────┬───────────────────────┤
│  Item Service│  Fulfillment  │  Marketplace          │
│  :8001       │  Eligibility  │  Seller Service       │
│              │  :8002        │  :8004                │
│  - Item CRUD │  - Path eval  │  - Seller profiles    │
│  - SKU graph │  - Inventory  │  - Trust scoring      │
│  - Variants  │  - Node mgmt  │  - Category gating    │
│  - Bundles   │               │                       │
├──────────────┴───────┬───────┴───────────────────────┤
│   Compliance Engine  │  Inventory Event Stream       │
│   :8003              │  (Redis Streams)              │
│                      │                               │
│  - Policy rules (OPA │  - Stock changes              │
│    or venmo/business │  - Node enable/disable        │
│    -rules)           │  - BusinessRuleApplied        │
│  - State regulations │  - Reservation events         │
│  - Time windows      │                               │
│  - Audit trail       │                               │
├──────────────────────┴───────────────────────────────┤
│          Transactability Resolution Engine            │
│                                                      │
│  POST /evaluate                                      │
│  Input:  { item_id, market, customer_location }      │
│  Output: { eligible: bool, paths: [...],             │
│            violations: [...], audit_trail: [...] }    │
│                                                      │
│  Merges ALL signals → final eligibility per          │
│  item × market × fulfillment × time window           │
├──────────────────────────────────────────────────────┤
│              Operational Dashboard                    │
│              (Streamlit) :8501                        │
│                                                      │
│  - Coverage gaps (items with no transactable path)   │
│  - Rule conflict detection + audit trail             │
│  - "What-if" simulator (relax a rule → revenue δ)   │
│  - Seller trajectory modeling                        │
│  - Compliance drift tracker                          │
└──────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Services** | Python FastAPI | Async, auto OpenAPI docs, Pydantic validation |
| **Database** | PostgreSQL 16 + `ltree` + JSONB | Item hierarchy + flexible attributes, no graph DB needed |
| **Event streaming** | Redis Streams | Kafka-like semantics, zero overhead, consumer groups |
| **Policy engine** | `venmo/business-rules` + OPA sidecar | JSON rules for business logic, Rego for hard compliance |
| **Inter-service** | HTTPX (async) | HTTP/2, strict timeouts, retries with tenacity |
| **API Gateway** | Nginx | Reverse proxy, rate limiting |
| **Dashboard** | Streamlit | Python-native, real-time, fast to build |
| **Containers** | Docker Compose | PostgreSQL + Redis + 5 services + Nginx + Streamlit |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Async PostgreSQL with proper relational modeling |
| **Testing** | pytest + testcontainers-python | Spin up real PostgreSQL/Redis in tests |

### Database Schema (Core Tables)

```sql
-- Item graph with ltree for category hierarchy
CREATE TABLE items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    item_type VARCHAR(20) CHECK (item_type IN ('base', 'variant', 'bundle')),
    parent_item_id UUID REFERENCES items(item_id),
    category_path ltree,  -- 'grocery.dairy.milk'
    attributes JSONB DEFAULT '{}',
    compliance_tags TEXT[] DEFAULT '{}',  -- ['hazmat', 'age_restricted', 'alcohol']
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bundle composition
CREATE TABLE bundle_components (
    bundle_item_id UUID REFERENCES items(item_id),
    component_item_id UUID REFERENCES items(item_id),
    quantity INT DEFAULT 1,
    PRIMARY KEY (bundle_item_id, component_item_id)
);

-- Fulfillment paths
CREATE TABLE fulfillment_paths (
    path_id SERIAL PRIMARY KEY,
    path_code VARCHAR(50) UNIQUE NOT NULL,  -- 'ship_to_home', 'pickup', 'ship_from_store'
    display_name TEXT,
    requires_inventory BOOLEAN DEFAULT true,
    max_weight_lbs DECIMAL,
    supported_item_types TEXT[]
);

-- Market-level fulfillment config
CREATE TABLE market_fulfillment (
    market_code VARCHAR(10),  -- 'US-CA', 'US-TX', 'MX'
    path_id INT REFERENCES fulfillment_paths(path_id),
    enabled BOOLEAN DEFAULT true,
    priority INT DEFAULT 0,
    PRIMARY KEY (market_code, path_id)
);

-- Inventory positions per node
CREATE TABLE inventory_positions (
    item_id UUID REFERENCES items(item_id),
    fulfillment_node VARCHAR(50),  -- 'FC-DAL-01', 'STORE-4532'
    available_qty INT DEFAULT 0,
    reserved_qty INT DEFAULT 0,
    path_id INT REFERENCES fulfillment_paths(path_id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (item_id, fulfillment_node, path_id)
);

-- Compliance rules (versioned, auditable)
CREATE TABLE compliance_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(30) CHECK (rule_type IN ('geographic', 'temporal', 'category', 'seller', 'item')),
    market_codes TEXT[],  -- which markets this applies to, NULL = all
    category_paths ltree[],  -- which categories, NULL = all
    compliance_tags TEXT[],  -- which item tags trigger this rule
    rule_definition JSONB NOT NULL,  -- the actual rule logic (venmo/business-rules format)
    effective_from TIMESTAMPTZ DEFAULT NOW(),
    effective_until TIMESTAMPTZ,  -- NULL = no expiry
    enabled BOOLEAN DEFAULT true,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seller profiles with trust scoring
CREATE TABLE sellers (
    seller_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    trust_tier VARCHAR(20) CHECK (trust_tier IN ('new', 'standard', 'trusted', 'top_rated')),
    defect_rate DECIMAL DEFAULT 0,
    return_rate DECIMAL DEFAULT 0,
    on_time_rate DECIMAL DEFAULT 1.0,
    allowed_categories ltree[],  -- categories this seller can list in
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit trail for every eligibility decision
CREATE TABLE eligibility_audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    item_id UUID NOT NULL,
    market_code VARCHAR(10) NOT NULL,
    fulfillment_path VARCHAR(50),
    seller_id UUID,
    eligible BOOLEAN NOT NULL,
    violations JSONB DEFAULT '[]',
    rules_evaluated JSONB DEFAULT '[]',
    evaluation_ms INT,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Eligibility Resolution Algorithm

```
POST /evaluate
{
  "item_id": "uuid",
  "market_code": "US-CA",
  "customer_location": { "state": "CA", "zip": "94105" },
  "seller_id": "uuid",  // optional, for marketplace items
  "timestamp": "2024-03-15T14:30:00Z"  // optional, for time-based rules
}

Resolution steps:
1. Load item + all variants/components (if bundle, evaluate each component)
2. Load market's enabled fulfillment paths (ordered by priority)
3. For each path:
   a. COMPLIANCE CHECK — evaluate all matching compliance_rules
      - Geographic: state/county restrictions (alcohol, firearms, fireworks)
      - Temporal: time-of-day restrictions (alcohol before 10am)
      - Category: hazmat shipping restrictions per path
      - Item: specific SKU blocks or holds
   b. SELLER CHECK — if marketplace item:
      - Trust tier allows this category?
      - Defect rate below threshold?
   c. INVENTORY CHECK — query inventory_positions for this item + path
      - Available qty > 0 at a node serving this path?
      - Node is enabled (not disabled/closed)?
   d. FULFILLMENT CHECK — item meets path requirements?
      - Weight within max_weight_lbs?
      - Item type in supported_item_types?
4. Aggregate results across all paths
5. Log decision to eligibility_audit_log
6. Return response with eligible paths, violations, and audit trail
```

### Phased Build Plan

**Phase 1: Core Engine (Day 1-2)**
- Single FastAPI service with PostgreSQL
- Item model with parent/child, bundles, ltree categories
- Fulfillment paths + market config
- Rule engine (venmo/business-rules) for compliance rules
- `POST /evaluate` endpoint
- Seed data: 100 items, 4 fulfillment paths, 5 markets (US states)
- 20 compliance rules (alcohol, hazmat, age-restricted, firearms, time-based)

**Phase 2: Microservices + Events (Day 3-4)**
- Split into item-service, eligibility-service, inventory-service, seller-service
- Docker Compose: PostgreSQL + Redis + 4 services + Nginx
- Redis Streams for inventory state changes
- Event-driven eligibility re-evaluation on stock changes
- Seller trust scoring with progressive category gating

**Phase 3: Dashboard + Killer Features (Day 5-6)**
- Streamlit operational dashboard
- Coverage gap analysis (items with no transactable path)
- Rule conflict detection with audit trail
- "What-if" simulator: relax a rule → see revenue impact
- Seller trajectory modeling (predict when seller qualifies for new categories)
- Compliance drift tracker (items that lost eligibility and why)

**Phase 4: Polish + Production-Ready (Day 7)**
- Integration tests with testcontainers-python
- API documentation (auto-generated by FastAPI)
- README with architecture diagrams
- Demo seed data that tells a compelling story
- Performance benchmarks

### Killer Features (Architecturally Significant Patterns)

1. **Rule conflict resolution with audit trail** — When two rules contradict (state allows, federal blocks), which wins and why? Every decision logged with full reasoning.

2. **"What-if" simulator** — "If we relaxed hazmat shipping to 3 more states, how many SKUs become transactable? What's the revenue upside?" Real analysis, not hand-waving.

3. **Compliance drift detection** — An item was transactable yesterday but isn't today. What changed? Which rule? Proactive alerts.

4. **Seller trajectory modeling** — Based on defect rate trend, when will this seller qualify for gated categories? Predictive, not just reactive.

5. **Event-driven re-evaluation** — Inventory drops to 0 at FC-Dallas → item instantly becomes non-transactable for ship-to-home in TX → still available for pickup at Store #4532. Real-time, not batch.

## Expansion Additions

### Market Metadata

The eligibility service now separates market enablement from market regulation metadata:

- `market_fulfillment` continues to control which paths are enabled in a market.
- `market_regulations` holds the market display name, country, region, language set, currency, timezone, and regulatory summary.
- `customer_location.state` is treated as a generic region code and validated against `market_regulations.region_code`, which removes the earlier US-only assumption.

### Geo Restriction Zones

`geo_restriction_zones` adds address-level overlays for cases where ZIP-level blocking is too broad:

- polygon or radius geometry stored directly in JSONB
- optional `hex_cells` for coarse precomputed matching
- `blocked_paths` so the same zone can block delivery but leave other paths untouched
- surfaced through `matched_zone_codes` and `zone_explanation` in the evaluation response

### Seller IPI and Market Readiness

Seller quality is now represented as an additive operational signal instead of only trust tier:

- `in_stock_rate`, `cancellation_rate`, `ipi_score`, and `ipi_breakdown` are persisted on sellers
- `/v1/sellers/{seller_id}/ipi` exposes the score, tier, and ranking impact
- eligibility rules can gate or block on `seller_ipi_score`
- seller VAT readiness is also exposed as data so market-specific seller registration rules remain declarative

### Probabilistic Inventory and Pooling

Inventory is no longer purely binary:

- `inventory_positions` now carry `confidence_score`, `last_verified_at`, `verification_source`, `oos_30d_count`, and `node_type`
- path summaries surface `confidence_band` and `confidence_reason`
- alternative fulfillment nodes can be returned for nearby-store rescue flows

### Diagnosis, Analytics, and Resilience

Three new additive layers sit on top of the original `/v1/evaluate` flow:

- `/v1/diagnose` turns evaluation outputs plus trace metadata into deterministic root-cause findings
- analytics endpoints aggregate the audit log into blocked-item, rule-impact, and market-coverage views
- Redis-backed rule caching and circuit-breaker state let the system degrade by item risk tier instead of failing uniformly

### Batch Evaluation

`POST /v1/evaluate/batch` provides measured batch benchmarking over the same core engine:

- same request model as single evaluation, wrapped in `requests[]`
- ordered results with aggregate `p50_ms`, `p95_ms`, and `p99_ms`
- compatible with the same rule cache and audit instrumentation

---

## Sources

### Large-Scale Retail Engineering (Walmart Tech Blog)
- [Inventory Availability via Event Sourcing](https://medium.com/walmartglobaltech/design-inventory-availability-system-using-event-sourcing-1d0f022e399f)
- [Item Setup Orchestrator Performance](https://medium.com/walmartglobaltech/performance-enhancements-to-the-item-setup-orchestrator-6a733b99591d)
- [Kafka for Item Setup](https://medium.com/walmartglobaltech/apache-kafka-for-item-setup-3fe8f4ba5967)
- [Domain-Driven Microservices](https://medium.com/walmartglobaltech/building-domain-driven-microservices-af688aa1b1b8)
- [Next-Gen E-Commerce Platform](https://medium.com/walmartglobaltech/building-a-next-generation-e-commerce-platform-for-10x-growth-b677ea35de89)
- [Inventory Reservations API Scaling](https://medium.com/walmartglobaltech/scaling-the-walmart-inventory-reservations-api-for-peak-traffic-9ba37833ef9d)
- [Retail Product Knowledge Graph](https://medium.com/walmartglobaltech/retail-graph-walmarts-product-knowledge-graph-6ef7357963bc)

### Competitor APIs
- [Amazon Listings Restrictions API](https://developer-docs.amazon.com/sp-api/docs/listings-restrictions-api-v2021-08-01-reference)
- [Amazon FBA Inbound Eligibility](https://github.com/amzn/selling-partner-api-models)
- [Shopify Markets](https://shopify.dev/docs/apps/selling-strategies/markets)
- [Shopify FulfillmentOrder](https://shopify.dev/docs/api/admin-graphql/2024-01/objects/FulfillmentOrder)
- [Walmart Marketplace API](https://developer.walmart.com/api/us/mp/items/)

### Libraries & Tools
- [venmo/business-rules](https://github.com/venmo/business-rules) — Python rule engine
- [Open Policy Agent](https://www.openpolicyagent.org/) — Policy-as-code
- [Redpanda](https://github.com/redpanda-data/redpanda) — Kafka-compatible, no JVM
- [testcontainers-python](https://github.com/testcontainers/testcontainers-python) — Integration testing
- [InvenTree](https://github.com/inventree/InvenTree) — Reference inventory management system

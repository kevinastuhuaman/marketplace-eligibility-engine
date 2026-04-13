# Design Decisions & Learnings

This document captures the architectural philosophy behind the Marketplace Eligibility Engine and the operational lessons learned building and deploying it. Each section explains not just what was built, but why that approach was chosen over alternatives.

---

## Architectural Philosophy

### Diagnosis as a First-Class Concern

I built the diagnosis endpoint on top of the evaluation engine, not beside it. When `POST /v1/evaluate` returns a block, the diagnosis service traces exactly which rule, which upstream service, and which data field caused it. Then it generates a human-readable explanation and a concrete fix suggestion.

The alternative -- building diagnosis as a separate system that re-interprets evaluation results -- creates a consistency problem. If the diagnosis logic ever diverges from the evaluation logic, you get explanations that don't match reality. By making diagnosis a downstream consumer of the same rule trace, they're guaranteed to agree.

### Markets as Data, Not Code

Adding Mexico, Chile, Costa Rica, and Canada to the engine didn't require any new code paths. Each market's regulatory requirements are stored as data in the `market_regulations` table: display name, country code, currency, language codes, timezone, and a regulatory summary JSONB field. Compliance rules reference market codes in their `market_codes` array.

The temptation is to add `if market == "MX": check_nom_cert()` branches. That works for 2 markets and becomes unmaintainable at 20. By parameterizing market differences as data, the same engine handles US state-level alcohol laws and Mexico's NOM certification requirements with zero branching.

### Address-Level Geofencing Over ZIP-Level Blocking

The traditional model blocks an entire ZIP code if a restricted zone (school, church, government building) sits inside it. For alcohol delivery, this means denying thousands of eligible households because one school exists in the ZIP. That's a real revenue and customer experience problem.

I implemented address-level restriction zones with polygon coordinates and hex-cell metadata (inspired by the H3 hex-grid pattern used in delivery logistics). The coarse hex cells enable fast precomputation -- check if the customer's hex matches a restricted zone before doing the expensive polygon containment test.

### Confidence-Weighted Inventory

Binary inventory (available/unavailable) is a simplification that breaks in same-day commerce. An item might show "in stock" based on a count from 6 hours ago, but the actual shelf is empty. Target's RFID rollout improved in-stock accuracy from 65% to 95% precisely because they moved beyond binary counts.

I moved inventory to a confidence-weighted model (0.0 to 1.0) that factors in verification source, time since last check, and historical OOS frequency. The evaluation engine can now say "available at 0.4 confidence" and let the path status reflect that uncertainty rather than overpromising.

### Risk-Tiered Circuit Breakers

A generic circuit breaker treats all requests the same: open the circuit, fail everything. But in a compliance engine, a T-shirt and a firearm have very different risk profiles when an upstream service is unavailable.

I implemented risk-tiered fallback: when the seller service is down, low-risk items (grocery, home goods) proceed with a warning. Medium-risk items (supplements, chemicals) gate to manual review. High-risk items (firearms, age-restricted) fail closed. The platform degrades intentionally along the risk axis, not randomly.

### Seller Quality as a Platform Primitive

Seller trust started as a simple boolean gate: "is this seller trusted enough to sell hazmat?" That works until you need to answer "how close is this seller to qualifying?" or "should we recommend they use platform fulfillment to improve their metrics?"

I extended seller trust to an IPI-style continuous score (180-910) computed from 8+ metrics. The score maps to trust tiers that feed eligibility gates, ranking metadata, and fulfillment service recommendations. Seller quality becomes a reusable platform primitive rather than a scattered collection of one-off rules.

### Multi-Store Pooling for OOS Recovery

When the primary fulfillment node is out of stock, the traditional response is "unavailable." But a store 3 miles away might have 50 units. The nearby-store pooling endpoint (`GET /v1/inventory/alternative-nodes`) surfaces the next-best stores with distance, inventory, and confidence -- turning an OOS into a save without adding any new inventory to the system.

### Audit Trail as Analytics Foundation

Every evaluation writes to the audit log: item, market, path, seller, eligible/not, violations, rules evaluated, and latency. This creates a compliance record, but more importantly, it creates an analytics foundation.

The analytics endpoints aggregate the audit trail to answer: which rules block the most items? Which markets have the lowest eligibility rate? Where do conflict resolutions suggest the rule logic is too broad? These insights turn a compliance system into a revenue optimization tool.

### Frontend as Decision Console

The React frontend was designed as an internal decision console, not a consumer-facing shopping experience. Scenario walkthroughs explain the rule logic narratively. Market comparison panels show the same item's eligibility across geographies side by side. The diagnosis timeline traces causality visually. Print-ready scenario pages work as reference handouts.

### Performance as Product

Performance is a feature, not an afterthought. The batch evaluation endpoint returns p50/p95/p99 latency alongside results. Rule caching via Redis with TTL-based invalidation keeps repeated evaluations fast. Connection pool tuning prevents database contention under load. The perf test script measures actual throughput so claims about scale are backed by numbers.

---

## Operational Learnings

These are the production gotchas discovered during development and deployment -- the kind of knowledge that only comes from running the system end-to-end.

### Docker DNS Caching

Nginx inside Docker caches upstream DNS lookups at startup. When a backend service restarts and gets a new container IP, nginx keeps routing to the old IP and returns 502s. The fix is adding `resolver 127.0.0.11 valid=10s ipv6=off;` to the nginx server block, which forces periodic re-resolution against Docker's internal DNS.

### Seed Idempotency Requires GET Endpoints

The seed script creates items, then sellers, then inventory positions that reference both. If a seller already exists (duplicate name), the POST returns 409. To continue the seed, the script needs to resolve the existing seller's ID -- which requires a `GET /v1/sellers` list endpoint. Every POST-only endpoint needs a corresponding GET list endpoint for the recovery path. Without it, skipped duplicates break downstream steps.

### `create_all()` Doesn't ALTER Existing Tables

SQLAlchemy's `create_all()` creates tables that don't exist but silently skips tables that do. If you add a `display_metadata` JSONB column to the Item model, `create_all()` won't add it to the existing `items` table. You need explicit `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` SQL in the service's lifespan handler, plus a backfill step for existing rows.

### Docker Build Context Boundaries

The eligibility service Dockerfile sets `context: ./services` in docker-compose. This means `COPY ../scripts/seed.py` is impossible -- Docker can't access files above the build context. Shared data (catalog definitions, scenario data, constants) must live inside the `services/shared/` directory so all service Dockerfiles can reach it.

### Upstream Image Recreation

`docker compose up -d` only recreates containers whose image hash changed. Stock images (nginx, postgres, redis) never change, so Docker prints "Running" instead of "Recreated" even when their config files changed. If you updated `nginx.conf` or need nginx to re-resolve DNS after a service rebuild, you must use `--force-recreate nginx` explicitly.

### Inventory Depletion Persists Across Deploys

The seed script creates inventory positions with initial quantities, but it uses INSERT semantics -- it creates new rows, it doesn't update existing depleted ones. If a demo depleted a position to 0, re-running the seed doesn't restore it. You need an explicit replenishment step via `POST /v1/inventory/adjust` with a positive delta for each depleted position.

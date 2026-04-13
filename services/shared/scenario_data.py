"""Canonical scenario definitions for all demo scenarios -- single source of truth.
Used by:
  - dashboard/app.py (Scenario Demo tab) to render buttons and run evaluations
  - scripts/seed.py to print test curl commands
  - future API-driven scenario runner

Each scenario has one or more variants.  A variant fully describes the
/v1/evaluate payload that should be sent, plus the expected human-readable
outcome for display purposes.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Seller UUIDs (must match scripts/seed.py)
# ---------------------------------------------------------------------------
ACME_WINES_SELLER_ID = "00000000-0000-0000-0000-000000000002"
TECHGEAR_SELLER_ID = "00000000-0000-0000-0000-000000000003"
NEWSELLER_SELLER_ID = "00000000-0000-0000-0000-000000000004"
CHEMSUPPLY_SELLER_ID = "00000000-0000-0000-0000-000000000005"

# ---------------------------------------------------------------------------
# Scenario Definitions
# ---------------------------------------------------------------------------

SCENARIOS: list[dict] = [
    # ------------------------------------------------------------------
    # Scenario 1: Wine to Utah (BLOCKED) vs Colorado (CLEAR)
    # ------------------------------------------------------------------
    {
        "id": 1,
        "label": "Wine to Utah (BLOCKED) vs Colorado (CLEAR)",
        "short_label": "Wine UT/CO",
        "what_it_proves": "Geographic compliance -- same item, different outcome by state",
        "variants": [
            {
                "label": "Utah (BLOCKED)",
                "item_sku": "ALC-001",
                "market_code": "US-UT",
                "state": "UT",
                "zip": "84101",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "All paths blocked",
                "sellers": [],
                "context": {},
            },
            {
                "label": "Colorado (CLEAR)",
                "item_sku": "ALC-001",
                "market_code": "US-CO",
                "state": "CO",
                "zip": "80202",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "Eligible with age verification",
                "sellers": [],
                "context": {"customer_age": 25},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 2: Pool Chlorine -- Hazmat Path Restrictions
    # ------------------------------------------------------------------
    {
        "id": 2,
        "label": "Pool Chlorine -- Hazmat Path Restrictions",
        "short_label": "Chlorine TX",
        "what_it_proves": "Hazmat items blocked from shipping but allowed for pickup",
        "variants": [
            {
                "label": "Pool Chlorine in Texas",
                "item_sku": "CHEM-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Shipping blocked, pickup allowed",
                "sellers": [],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 3: Fireworks -- Seasonal + Geographic Restrictions
    # ------------------------------------------------------------------
    {
        "id": 3,
        "label": "Fireworks -- Seasonal + Geographic Restrictions",
        "short_label": "Fireworks TX/MA",
        "what_it_proves": "Seasonal gates, carrier bans, and state-level total bans",
        "variants": [
            {
                "label": "TX in July (IN SEASON)",
                "item_sku": "FIRE-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Pickup allowed (in season), shipping blocked",
                "sellers": [],
                "context": {},
            },
            {
                "label": "TX in October (OFF SEASON)",
                "item_sku": "FIRE-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-10-15T14:00:00-05:00",
                "expected_outcome": "All paths gated/blocked (out of season)",
                "sellers": [],
                "context": {},
            },
            {
                "label": "Massachusetts (TOTAL BAN)",
                "item_sku": "FIRE-001",
                "market_code": "US-MA",
                "state": "MA",
                "zip": "02101",
                "timestamp": "2026-07-04T14:00:00-04:00",
                "expected_outcome": "All paths blocked (state ban)",
                "sellers": [],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 4: Supplement -- CA Prop 65 Warning
    # ------------------------------------------------------------------
    {
        "id": 4,
        "label": "Supplement -- CA Prop 65 Warning",
        "short_label": "Supplement CA",
        "what_it_proves": "WARN rules attach advisories without blocking eligibility",
        "variants": [
            {
                "label": "Supplement in California",
                "item_sku": "SUPP-001",
                "market_code": "US-CA",
                "state": "CA",
                "zip": "90210",
                "timestamp": "2026-07-04T14:00:00-07:00",
                "expected_outcome": "Eligible with Prop 65 warning",
                "sellers": [],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 5: Firearms -- 1P Allowed (with age), 3P Blocked
    # ------------------------------------------------------------------
    {
        "id": 5,
        "label": "Firearms -- 1P Allowed (with age), 3P Blocked",
        "short_label": "Rifle 1P/3P",
        "what_it_proves": "3P marketplace prohibition + age-gated 1P paths",
        "variants": [
            {
                "label": "Rifle, 1P, Age 25 (ALLOWED)",
                "item_sku": "FIRE-002",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "1P paths eligible with age verified, 3P blocked",
                "sellers": [],
                "context": {"customer_age": 25},
            },
            {
                "label": "Rifle, No Age (REQUIRE)",
                "item_sku": "FIRE-002",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Age verification required, 3P blocked",
                "sellers": [
                    {"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"},
                    {"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"},
                ],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 6: Seller Hazmat Quality Gate
    # ------------------------------------------------------------------
    {
        "id": 6,
        "label": "Seller Hazmat Quality Gate",
        "short_label": "Hazmat Seller",
        "what_it_proves": "Seller defect rate exceeding threshold gates marketplace path",
        "variants": [
            {
                "label": "Raid Spray via ChemSupply (GATED)",
                "item_sku": "CHEM-002",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Marketplace gated (4.5% defect > 3% threshold)",
                "seller_id": CHEMSUPPLY_SELLER_ID,
                "sellers": [
                    {"id": CHEMSUPPLY_SELLER_ID, "name": "ChemSupply Inc"},
                ],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 7: 3P Alcohol -- Seller Trust Gate
    # ------------------------------------------------------------------
    {
        "id": 7,
        "label": "3P Alcohol -- Seller Trust Gate",
        "short_label": "Alcohol Seller",
        "what_it_proves": "Seller trust tier determines marketplace eligibility for alcohol",
        "variants": [
            {
                "label": "White Claw via Acme Wines (ALLOWED)",
                "item_sku": "ALC-003",
                "market_code": "US-CO",
                "state": "CO",
                "zip": "80202",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "Marketplace eligible (trusted tier)",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [
                    {"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"},
                ],
                "context": {"customer_age": 25},
            },
            {
                "label": "Bourbon via NewSeller123 (GATED)",
                "item_sku": "ALC-002",
                "market_code": "US-CO",
                "state": "CO",
                "zip": "80202",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "Marketplace gated (new tier, requires trusted+)",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [
                    {"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"},
                ],
                "context": {"customer_age": 25},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 8: Electronics -- Seller Trust Gate
    # ------------------------------------------------------------------
    {
        "id": 8,
        "label": "Electronics -- Seller Trust Gate",
        "short_label": "Electronics Seller",
        "what_it_proves": "Seller trust tier determines marketplace eligibility for electronics",
        "variants": [
            {
                "label": "Samsung via TechGear (ALLOWED)",
                "item_sku": "ELEC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Marketplace eligible (trusted tier)",
                "seller_id": TECHGEAR_SELLER_ID,
                "sellers": [
                    {"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"},
                ],
                "context": {},
            },
            {
                "label": "Samsung via NewSeller123 (GATED)",
                "item_sku": "ELEC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Marketplace gated (new tier, requires trusted+)",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [
                    {"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"},
                ],
                "context": {},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 9: Pseudoephedrine -- Quantity Limit + ID Required
    # ------------------------------------------------------------------
    {
        "id": 9,
        "label": "Pseudoephedrine -- Quantity Limit + ID Required",
        "short_label": "Sudafed Qty",
        "what_it_proves": "Quantity limits and age/ID verification for controlled substances",
        "variants": [
            {
                "label": "Sudafed qty=2, age 30 (ALLOWED)",
                "item_sku": "PHARM-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Eligible (within quantity limit, ID verified)",
                "sellers": [],
                "context": {"customer_age": 30, "requested_quantity": 2},
            },
            {
                "label": "Sudafed qty=5, age 30 (BLOCKED)",
                "item_sku": "PHARM-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Blocked (exceeds 3-package limit)",
                "sellers": [],
                "context": {"customer_age": 30, "requested_quantity": 5},
            },
        ],
    },
    # ------------------------------------------------------------------
    # Scenario 10: Inventory Depletion
    # ------------------------------------------------------------------
    {
        "id": 10,
        "label": "Inventory Depletion",
        "short_label": "Milk Inventory",
        "what_it_proves": "Inventory state changes affect eligibility in real time",
        "variants": [
            {
                "label": "Check Milk (should be in stock)",
                "item_sku": "GROC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Eligible (qty=50 in stock)",
                "sellers": [],
                "context": {},
            },
            # Depletion variant is operator-assisted (SSH to server).
            # The React frontend cannot mutate inventory — mutation endpoints are blocked.
            # To demo: SSH, POST /v1/inventory/events with delta=-50, then re-evaluate.
        ],
    },
    {
        "id": 11,
        "label": "Cross-System Diagnosis Cascade",
        "short_label": "Diagnosis Cascade",
        "what_it_proves": "Diagnosis can separate a seller-quality root cause from a market regulation block",
        "narration": "A high-IPI seller clears the same cross-border workflow that a low-IPI seller and label issue break.",
        "variants": [
            {
                "label": "Acme Wines in Mexico (CLEAR)",
                "item_sku": "ALC-004",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "Eligible with IEPS warning",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
            {
                "label": "NewSeller in Mexico (BLOCKED)",
                "item_sku": "ALC-005",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "timestamp": "2026-07-04T14:00:00-06:00",
                "expected_outcome": "Seller IPI gate plus Spanish-label block",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [{"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
        ],
    },
    {
        "id": 12,
        "label": "Offer Exists, Inventory Missing",
        "short_label": "Offer No Inv",
        "what_it_proves": "Diagnosis points to inventory instead of returning a vague unavailable state",
        "narration": "The item offer exists, but one variant has no stock anywhere, so the diagnosis points directly to inventory-service.",
        "variants": [
            {
                "label": "Zero inventory demo item",
                "item_sku": "HOME-006",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Blocked by inventory availability",
                "sellers": [],
                "context": {},
            },
            {
                "label": "Comparable in-stock home item",
                "item_sku": "HOME-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Eligible",
                "sellers": [],
                "context": {},
            },
        ],
    },
    {
        "id": 13,
        "label": "School-Zone Alcohol Delivery",
        "short_label": "School Zone",
        "what_it_proves": "Same ZIP, different coordinates, different transactability outcome",
        "narration": "The school-zone overlay blocks one address while nearby households in the same ZIP remain eligible.",
        "variants": [
            {
                "label": "Inside school zone",
                "item_sku": "ALC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Delivery blocked with zone explanation",
                "sellers": [],
                "context": {"customer_age": 25},
                "customer_location": {
                    "state": "TX",
                    "zip": "75201",
                    "latitude": 32.7825,
                    "longitude": -96.8010,
                    "address_id": "school-zone-home",
                },
            },
            {
                "label": "Outside school zone",
                "item_sku": "ALC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Eligible with age verification",
                "sellers": [],
                "context": {"customer_age": 25},
                "customer_location": {
                    "state": "TX",
                    "zip": "75201",
                    "latitude": 32.7895,
                    "longitude": -96.7900,
                    "address_id": "outside-zone-home",
                },
            },
        ],
    },
    {
        "id": 14,
        "label": "Mexico NOM Certification",
        "short_label": "MX NOM",
        "what_it_proves": "Global market support is data-driven instead of branching code",
        "variants": [
            {
                "label": "Certified blender",
                "item_sku": "HOME-002",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Eligible",
                "sellers": [{"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"}],
                "seller_id": TECHGEAR_SELLER_ID,
                "context": {},
                "locale": "es",
            },
            {
                "label": "Uncertified blender",
                "item_sku": "HOME-005",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Blocked by NOM certification",
                "sellers": [{"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"}],
                "seller_id": TECHGEAR_SELLER_ID,
                "context": {},
                "locale": "es",
            },
        ],
    },
    {
        "id": 15,
        "label": "Mexico IEPS + Spanish Label",
        "short_label": "MX IEPS",
        "what_it_proves": "Warnings and blocks can coexist within a single international market",
        "variants": [
            {
                "label": "Spanish-labeled sugary alcohol",
                "item_sku": "ALC-004",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Eligible with IEPS warning",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
            {
                "label": "English-only sugary alcohol",
                "item_sku": "ALC-005",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Blocked by Spanish labeling",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
        ],
    },
    {
        "id": 16,
        "label": "Chile Black Label + Lithium Import",
        "short_label": "CL Labels",
        "what_it_proves": "Chile applies different regulation overlays by item class",
        "variants": [
            {
                "label": "Black-label cereal",
                "item_sku": "GROC-002",
                "market_code": "CL-RM",
                "state": "RM",
                "zip": "8320000",
                "expected_outcome": "Eligible with warning",
                "sellers": [],
                "context": {},
                "locale": "es",
            },
            {
                "label": "Lithium battery without import cert",
                "item_sku": "ELEC-003",
                "market_code": "CL-RM",
                "state": "RM",
                "zip": "8320000",
                "expected_outcome": "Blocked by import certificate rule",
                "sellers": [],
                "context": {},
                "locale": "es",
            },
        ],
    },
    {
        "id": 17,
        "label": "Costa Rica RTCA + VAT Registration",
        "short_label": "CR VAT",
        "what_it_proves": "Seller market readiness can gate regulated catalog expansion",
        "variants": [
            {
                "label": "VAT-registered seller",
                "item_sku": "GROC-003",
                "market_code": "CR-SJ",
                "state": "SJ",
                "zip": "10101",
                "expected_outcome": "Marketplace eligible",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {},
                "locale": "es",
            },
            {
                "label": "Seller missing VAT registration",
                "item_sku": "GROC-003",
                "market_code": "CR-SJ",
                "state": "SJ",
                "zip": "10101",
                "expected_outcome": "Marketplace gated",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [{"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"}],
                "context": {},
                "locale": "es",
            },
        ],
    },
    {
        "id": 18,
        "label": "Canada Bilingual + Metric Units",
        "short_label": "CA Labeling",
        "what_it_proves": "Canada-specific labeling rules are enforced independently from US defaults",
        "variants": [
            {
                "label": "Bilingual metric item",
                "item_sku": "HOME-003",
                "market_code": "CA-ON",
                "state": "ON",
                "zip": "M5H",
                "expected_outcome": "Eligible",
                "sellers": [],
                "context": {},
            },
            {
                "label": "Imperial-only item",
                "item_sku": "HOME-004",
                "market_code": "CA-ON",
                "state": "ON",
                "zip": "M5H",
                "expected_outcome": "Blocked by bilingual and metric rules",
                "sellers": [],
                "context": {},
            },
        ],
    },
    {
        "id": 19,
        "label": "FC Clear, Store Low Confidence",
        "short_label": "Low Conf",
        "what_it_proves": "Availability quality is confidence-weighted, not binary",
        "variants": [
            {
                "label": "Electronics stale store inventory",
                "item_sku": "ELEC-002",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Pickup low confidence, FC clear",
                "sellers": [],
                "context": {},
            },
        ],
    },
    {
        "id": 20,
        "label": "Inventory Service Outage Fallback",
        "short_label": "Breaker Fallback",
        "what_it_proves": "Risk-tiered fallback logic changes behavior when inventory-service is unavailable",
        "variants": [
            {
                "label": "Low-risk home item",
                "item_sku": "HOME-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Allow with warning during outage",
                "sellers": [],
                "context": {},
            },
            {
                "label": "Medium-risk electronics",
                "item_sku": "ELEC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Gate during outage",
                "sellers": [],
                "context": {},
            },
            {
                "label": "High-risk firearm",
                "item_sku": "FIRE-002",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Fail closed during outage",
                "sellers": [],
                "context": {"customer_age": 25},
            },
        ],
    },
    {
        "id": 21,
        "label": "Seller IPI Split",
        "short_label": "Seller IPI",
        "what_it_proves": "The same item can clear or gate solely from seller operational health",
        "variants": [
            {
                "label": "Trusted high-IPI seller",
                "item_sku": "ELEC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Marketplace eligible",
                "seller_id": TECHGEAR_SELLER_ID,
                "sellers": [{"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"}],
                "context": {},
            },
            {
                "label": "Critical IPI seller",
                "item_sku": "ELEC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Marketplace blocked or gated",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [{"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"}],
                "context": {},
            },
        ],
    },
    {
        "id": 22,
        "label": "Nearby Store Rescue",
        "short_label": "Store Rescue",
        "what_it_proves": "Nearby-store pooling can save a transaction when the primary node is empty",
        "variants": [
            {
                "label": "Primary store empty, Store B saves it",
                "item_sku": "TOY-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "expected_outcome": "Eligible with alternative nodes",
                "sellers": [],
                "context": {
                    "primary_node_id": "STORE-DAL-A",
                    "nearby_nodes": ["STORE-DAL-B", "STORE-DAL-C"],
                },
                "primary_node_id": "STORE-DAL-A",
                "nearby_nodes": ["STORE-DAL-B", "STORE-DAL-C"],
            },
        ],
    },
    {
        "id": 23,
        "label": "Impact Dashboard Story",
        "short_label": "Impact Dash",
        "what_it_proves": "Audit logs roll up into rule and market impact analytics",
        "variants": [
            {
                "label": "Blocked cross-market item",
                "item_sku": "ALC-005",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Generates blocked audit rows for analytics",
                "seller_id": NEWSELLER_SELLER_ID,
                "sellers": [{"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
        ],
    },
    {
        "id": 24,
        "label": "Side-by-Side Market Compare",
        "short_label": "Compare Mkts",
        "what_it_proves": "The same item produces different outcomes across countries without code branching",
        "variants": [
            {
                "label": "United States",
                "item_sku": "ALC-005",
                "market_code": "US-CA",
                "state": "CA",
                "zip": "90210",
                "expected_outcome": "Eligible with warnings",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
            },
            {
                "label": "Mexico",
                "item_sku": "ALC-005",
                "market_code": "MX-CDMX",
                "state": "CDMX",
                "zip": "01000",
                "expected_outcome": "Blocked by Spanish label",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
                "locale": "es",
            },
            {
                "label": "Canada",
                "item_sku": "ALC-005",
                "market_code": "CA-ON",
                "state": "ON",
                "zip": "M5H",
                "expected_outcome": "Blocked by bilingual rule",
                "seller_id": ACME_WINES_SELLER_ID,
                "sellers": [{"id": ACME_WINES_SELLER_ID, "name": "Acme Wines"}],
                "context": {"customer_age": 25},
            },
        ],
    },
]

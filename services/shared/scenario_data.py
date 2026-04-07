"""Canonical scenario definitions for all 10 demo scenarios -- single source of truth.
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
                "sellers": [
                    {"id": CHEMSUPPLY_SELLER_ID, "name": "ChemSupply Inc"},
                ],
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
                "sellers": [
                    {"id": TECHGEAR_SELLER_ID, "name": "TechGear Pro"},
                    {"id": NEWSELLER_SELLER_ID, "name": "NewSeller123"},
                ],
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
            {
                "label": "Deplete Milk Inventory (delta=-50)",
                "item_sku": "GROC-001",
                "market_code": "US-TX",
                "state": "TX",
                "zip": "75201",
                "timestamp": "2026-07-04T14:00:00-05:00",
                "expected_outcome": "Not eligible (inventory depleted to 0)",
                "sellers": [],
                "context": {},
                "inventory_action": {
                    "fulfillment_node": "FC-DAL-01",
                    "event_type": "adjustment",
                    "path_id": 1,
                    "seller_id": "00000000-0000-0000-0000-000000000001",
                    "delta": -50,
                },
            },
        ],
    },
]

"""Seed script for the Walmart Transactability Engine — all 10 demo scenarios.
Run with: python -m scripts.seed
Requires all services to be running (docker compose up).
"""
import asyncio
from typing import Any

import httpx

BASE_URL = "http://localhost"
EFFECTIVE_FROM = "2020-01-01T00:00:00-07:00"

# ---------------------------------------------------------------------------
# Seller UUIDs (deterministic for reproducibility)
# ---------------------------------------------------------------------------
WALMART_SELLER_ID = "00000000-0000-0000-0000-000000000001"
ACME_WINES_SELLER_ID = "00000000-0000-0000-0000-000000000002"
TECHGEAR_SELLER_ID = "00000000-0000-0000-0000-000000000003"
NEWSELLER_SELLER_ID = "00000000-0000-0000-0000-000000000004"
CHEMSUPPLY_SELLER_ID = "00000000-0000-0000-0000-000000000005"

ALL_PATHS = ["ship_to_home", "pickup", "ship_from_store", "marketplace_3p"]

# ---------------------------------------------------------------------------
# Data Definitions
# ---------------------------------------------------------------------------

ITEMS: list[dict[str, Any]] = [
    {
        "sku": "ALC-001",
        "name": "Caymus Cabernet Sauvignon 2021",
        "item_type": "base",
        "category_path": "alcohol.wine.red",
        "compliance_tags": ["alcohol", "age_restricted"],
        "attributes": {"weight_lbs": 3.2, "abv": 14.6},
    },
    {
        "sku": "CHEM-001",
        "name": "HTH Pool Chlorine Tabs 25lb",
        "item_type": "base",
        "category_path": "chemicals.pool",
        "compliance_tags": ["hazmat", "oxidizer"],
        "attributes": {"weight_lbs": 25, "hazmat_class": "5.1"},
    },
    {
        "sku": "FIRE-001",
        "name": "TNT Fireworks Assortment",
        "item_type": "base",
        "category_path": "seasonal.fireworks",
        "compliance_tags": ["fireworks", "hazmat", "seasonal"],
        "attributes": {"weight_lbs": 8},
    },
    {
        "sku": "SUPP-001",
        "name": "GNC Garcinia Cambogia 500mg",
        "item_type": "base",
        "category_path": "health.supplements",
        "compliance_tags": ["supplement", "prop_65"],
        "attributes": {"weight_lbs": 0.3},
    },
    {
        "sku": "FIRE-002",
        "name": "Remington 870 Shotgun",
        "item_type": "base",
        "category_path": "sporting.firearms",
        "compliance_tags": ["firearm", "age_restricted"],
        "attributes": {"weight_lbs": 7.5},
    },
    {
        "sku": "CHEM-002",
        "name": "Raid Ant Killer Spray",
        "item_type": "base",
        "category_path": "chemicals.pesticide",
        "compliance_tags": ["hazmat", "aerosol"],
        "attributes": {"weight_lbs": 0.8, "hazmat_class": "2.1"},
    },
    {
        "sku": "ELEC-001",
        "name": "Samsung Galaxy S24",
        "item_type": "base",
        "category_path": "electronics.phones",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 0.4},
    },
    {
        "sku": "ALC-002",
        "name": "Makers Mark Bourbon 750ml",
        "item_type": "base",
        "category_path": "alcohol.spirits.whiskey",
        "compliance_tags": ["alcohol", "age_restricted"],
        "attributes": {"weight_lbs": 3.3, "abv": 45},
    },
    {
        "sku": "PHARM-001",
        "name": "Sudafed PE 24ct",
        "item_type": "base",
        "category_path": "pharmacy.otc",
        "compliance_tags": ["pseudoephedrine", "age_restricted", "quantity_limited"],
        "attributes": {"weight_lbs": 0.2, "max_quantity": 3},
    },
    {
        "sku": "GROC-001",
        "name": "Organic Whole Milk 1gal",
        "item_type": "base",
        "category_path": "grocery.dairy",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 8.6},
    },
    {
        "sku": "CLOTH-001",
        "name": "Levi's 501 Jeans",
        "item_type": "base",
        "category_path": "apparel.pants",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 1.5},
    },
    {
        "sku": "TOY-001",
        "name": "LEGO Star Wars Set",
        "item_type": "base",
        "category_path": "toys.building",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 4.2},
    },
    {
        "sku": "HOME-001",
        "name": "Instant Pot 6qt",
        "item_type": "base",
        "category_path": "home.kitchen",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 12},
    },
    {
        "sku": "ELEC-002",
        "name": "Sony WH-1000XM5 Headphones",
        "item_type": "base",
        "category_path": "electronics.audio",
        "compliance_tags": [],
        "attributes": {"weight_lbs": 0.6},
    },
    {
        "sku": "ALC-003",
        "name": "White Claw Variety 12-Pack",
        "item_type": "base",
        "category_path": "alcohol.beer.seltzer",
        "compliance_tags": ["alcohol", "age_restricted"],
        "attributes": {"weight_lbs": 12.8, "abv": 5},
    },
]

FULFILLMENT_PATHS: list[dict[str, Any]] = [
    {
        "path_code": "ship_to_home",
        "display_name": "Ship to Home",
        "owner": "1p",
        "requires_inventory": True,
        "max_weight_lbs": 150,
    },
    {
        "path_code": "pickup",
        "display_name": "Store Pickup",
        "owner": "1p",
        "requires_inventory": True,
        "max_weight_lbs": None,
    },
    {
        "path_code": "ship_from_store",
        "display_name": "Ship from Store",
        "owner": "1p",
        "requires_inventory": True,
        "max_weight_lbs": 70,
    },
    {
        "path_code": "marketplace_3p",
        "display_name": "Marketplace (3P)",
        "owner": "3p",
        "requires_inventory": True,
        "max_weight_lbs": 70,
    },
]

MARKETS = ["US-CA", "US-TX", "US-CO", "US-UT", "US-MA", "US-NY", "US-HI", "US-KY"]

SELLERS: list[dict[str, Any]] = [
    {
        "seller_id": WALMART_SELLER_ID,
        "name": "Walmart",
        "trust_tier": "top_rated",
        "defect_rate": 0.001,
        "on_time_rate": 0.99,
        "total_orders": 1000000,
    },
    {
        "seller_id": ACME_WINES_SELLER_ID,
        "name": "Acme Wines",
        "trust_tier": "trusted",
        "defect_rate": 0.015,
        "on_time_rate": 0.96,
        "total_orders": 5000,
    },
    {
        "seller_id": TECHGEAR_SELLER_ID,
        "name": "TechGear Pro",
        "trust_tier": "trusted",
        "defect_rate": 0.02,
        "on_time_rate": 0.95,
        "total_orders": 8000,
    },
    {
        "seller_id": NEWSELLER_SELLER_ID,
        "name": "NewSeller123",
        "trust_tier": "new",
        "defect_rate": 0.08,
        "on_time_rate": 0.85,
        "total_orders": 50,
    },
    {
        "seller_id": CHEMSUPPLY_SELLER_ID,
        "name": "ChemSupply Inc",
        "trust_tier": "standard",
        "defect_rate": 0.045,
        "on_time_rate": 0.90,
        "total_orders": 2000,
    },
]

# Maps seller UUID -> list of SKUs they offer on marketplace
SELLER_OFFERS: dict[str, list[str]] = {
    ACME_WINES_SELLER_ID: ["ALC-001", "ALC-002", "ALC-003"],
    TECHGEAR_SELLER_ID: ["ELEC-001", "ELEC-002"],
    NEWSELLER_SELLER_ID: ["ELEC-001", "TOY-001", "ALC-002"],
    CHEMSUPPLY_SELLER_ID: ["CHEM-001", "CHEM-002"],
}

# ---------------------------------------------------------------------------
# Compliance Rules (25 total)
# ---------------------------------------------------------------------------


def _rule(
    rule_name: str,
    action: str,
    priority: int,
    conditions: dict,
    reason: str,
    *,
    rule_type: str = "geographic",
    conflict_group: str | None = None,
    market_codes: list[str] | None = None,
    category_paths: list[str] | None = None,
    compliance_tags: list[str] | None = None,
    blocked_paths: list[str] | None = None,
    requirement: dict | None = None,
    gate: dict | None = None,
    metadata: dict | None = None,
) -> dict:
    """Helper to build a rule payload with consistent structure."""
    rule_def: dict[str, Any] = {"conditions": conditions}
    if requirement:
        rule_def["requirement"] = requirement
    if gate:
        rule_def["gate"] = gate

    return {
        "rule_name": rule_name,
        "rule_type": rule_type,
        "action": action,
        "priority": priority,
        "conflict_group": conflict_group,
        "market_codes": market_codes,
        "category_paths": category_paths,
        "compliance_tags": compliance_tags,
        "blocked_paths": blocked_paths,
        "rule_definition": rule_def,
        "reason": reason,
        "metadata": metadata,
        "effective_from": EFFECTIVE_FROM,
        "enabled": True,
    }


COMPLIANCE_RULES: list[dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Scenario 1: Wine in UT vs CO
    # -----------------------------------------------------------------------
    _rule(
        "utah_alcohol_prohibition",
        "BLOCK",
        10,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "UT"},
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
            ]
        },
        "Utah prohibits alcohol delivery (Utah Code 32B-1-201)",
        market_codes=["US-UT"],
        compliance_tags=["alcohol"],
        blocked_paths=ALL_PATHS,
        metadata={"regulation": "Utah Code 32B-1-201", "jurisdiction": "state"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 2: Pool chlorine — hazmat blocks shipping, pickup allowed
    # -----------------------------------------------------------------------
    _rule(
        "hazmat_standard_carrier_ban",
        "BLOCK",
        20,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "hazmat"},
                {
                    "name": "fulfillment_path",
                    "operator": "in",
                    "value": ["ship_to_home", "ship_from_store"],
                },
            ]
        },
        "Hazmat items cannot be shipped via standard carriers (49 CFR 173)",
        rule_type="product",
        compliance_tags=["hazmat"],
        blocked_paths=["ship_to_home", "ship_from_store"],
        metadata={"regulation": "49 CFR 173", "jurisdiction": "federal"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 3: Fireworks — seasonal gate + MA total ban + carrier ban
    # -----------------------------------------------------------------------
    _rule(
        "fireworks_seasonal_gate_summer",
        "GATE",
        50,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "fireworks"},
                {"name": "request_month", "operator": "not_in", "value": [6, 7]},
            ]
        },
        "Fireworks sales restricted to June-July season",
        rule_type="seasonal",
        compliance_tags=["fireworks"],
        blocked_paths=["pickup"],
        gate={
            "type": "seasonal_window",
            "allowed_months": [6, 7],
        },
        metadata={"season": "summer", "note": "Fireworks gated outside Jun-Jul"},
    ),
    _rule(
        "ma_fireworks_total_ban",
        "BLOCK",
        30,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "MA"},
                {"name": "compliance_tags", "operator": "contains", "value": "fireworks"},
            ]
        },
        "Massachusetts bans all consumer fireworks (MGL Ch. 148 S39)",
        market_codes=["US-MA"],
        compliance_tags=["fireworks"],
        blocked_paths=ALL_PATHS,
        conflict_group="fireworks_ma",
        metadata={"regulation": "MGL Ch. 148 S39", "jurisdiction": "state"},
    ),
    _rule(
        "fireworks_carrier_ban",
        "BLOCK",
        10,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "fireworks"},
                {
                    "name": "fulfillment_path",
                    "operator": "not_equal_to",
                    "value": "pickup",
                },
            ]
        },
        "Fireworks cannot be shipped — pickup only",
        rule_type="product",
        compliance_tags=["fireworks"],
        blocked_paths=["ship_to_home", "ship_from_store", "marketplace_3p"],
        metadata={"regulation": "DOT/PHMSA", "jurisdiction": "federal"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 4: Supplement CA Prop 65 warning
    # -----------------------------------------------------------------------
    _rule(
        "prop_65_ca_warning",
        "WARN",
        100,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "CA"},
                {"name": "compliance_tags", "operator": "contains", "value": "prop_65"},
            ]
        },
        "California Prop 65 warning required for this product",
        market_codes=["US-CA"],
        compliance_tags=["prop_65"],
        metadata={"regulation": "CA Prop 65", "jurisdiction": "state"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 5: Firearms — 3P banned, 1P requires age 21, advisory
    # -----------------------------------------------------------------------
    _rule(
        "marketplace_firearms_prohibition",
        "BLOCK",
        5,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "firearm"},
                {
                    "name": "fulfillment_path",
                    "operator": "equal_to",
                    "value": "marketplace_3p",
                },
            ]
        },
        "Firearms prohibited on third-party marketplace",
        rule_type="product",
        compliance_tags=["firearm"],
        blocked_paths=["marketplace_3p"],
        metadata={"policy": "Walmart marketplace policy", "jurisdiction": "corporate"},
    ),
    _rule(
        "firearms_age_verification_21",
        "REQUIRE",
        30,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "firearm"},
            ]
        },
        "Firearms require age verification (21+)",
        rule_type="product",
        compliance_tags=["firearm"],
        blocked_paths=["pickup", "ship_to_home", "ship_from_store"],
        requirement={
            "type": "age_verification",
            "variable": "customer_age",
            "operator": "greater_than_or_equal_to",
            "value": 21,
        },
        metadata={"regulation": "18 USC 922(b)(1)", "jurisdiction": "federal"},
    ),
    _rule(
        "firearms_purchase_advisory",
        "WARN",
        100,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "firearm"},
            ]
        },
        "Firearm purchase — background check and ID required at pickup",
        rule_type="product",
        compliance_tags=["firearm"],
        metadata={"policy": "Walmart firearms policy", "jurisdiction": "corporate"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 6: Seller hazmat quality gate (ChemSupply defect > 3%)
    # -----------------------------------------------------------------------
    _rule(
        "hazmat_seller_quality_gate",
        "GATE",
        200,
        {
            "all": [
                {
                    "name": "seller_defect_rate",
                    "operator": "greater_than",
                    "value": 0.03,
                },
            ]
        },
        "Hazmat marketplace sellers must maintain <3% defect rate",
        rule_type="seller",
        category_paths=["chemicals"],
        blocked_paths=["marketplace_3p"],
        gate={
            "type": "metric_threshold",
            "thresholds": {
                "seller_defect_rate": {"operator": "less_than", "value": 0.03},
            },
        },
        metadata={"policy": "Walmart seller quality standards"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 7: 3P alcohol — age req + seller trust gate + advisory
    # -----------------------------------------------------------------------
    _rule(
        "alcohol_age_verification_21",
        "REQUIRE",
        30,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
            ]
        },
        "Alcohol purchases require age verification (21+)",
        rule_type="product",
        compliance_tags=["alcohol"],
        requirement={
            "type": "age_verification",
            "variable": "customer_age",
            "operator": "greater_than_or_equal_to",
            "value": 21,
        },
        metadata={"regulation": "21 USC", "jurisdiction": "federal"},
    ),
    _rule(
        "alcohol_seller_trust_gate",
        "GATE",
        200,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
                {
                    "name": "seller_trust_tier",
                    "operator": "in",
                    "value": ["new", "standard"],
                },
            ]
        },
        "Alcohol marketplace sellers must be trusted or top_rated tier",
        rule_type="seller",
        compliance_tags=["alcohol"],
        blocked_paths=["marketplace_3p"],
        gate={
            "type": "trust_tier",
            "required_tiers": ["trusted", "top_rated"],
        },
        metadata={"policy": "Walmart alcohol seller policy"},
    ),
    _rule(
        "alcohol_responsibility_advisory",
        "WARN",
        200,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
            ]
        },
        "Please drink responsibly. Must be 21+ to purchase.",
        rule_type="product",
        compliance_tags=["alcohol"],
        metadata={"policy": "Responsible alcohol messaging"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 8: Electronics — new/standard sellers gated from 3P
    # -----------------------------------------------------------------------
    _rule(
        "electronics_seller_trust_gate",
        "GATE",
        200,
        {
            "all": [
                {
                    "name": "seller_trust_tier",
                    "operator": "in",
                    "value": ["new", "standard"],
                },
            ]
        },
        "Electronics marketplace sellers must be trusted or top_rated tier",
        rule_type="seller",
        category_paths=["electronics"],
        blocked_paths=["marketplace_3p"],
        gate={
            "type": "trust_tier",
            "required_tiers": ["trusted", "top_rated"],
        },
        metadata={"policy": "Walmart electronics seller standards"},
    ),
    # -----------------------------------------------------------------------
    # Scenario 9: Pseudoephedrine — ID required + quantity limit
    # -----------------------------------------------------------------------
    _rule(
        "pseudoephedrine_id_requirement",
        "REQUIRE",
        40,
        {
            "all": [
                {
                    "name": "compliance_tags",
                    "operator": "contains",
                    "value": "pseudoephedrine",
                },
            ]
        },
        "Pseudoephedrine requires ID verification (18+) per CMEA",
        rule_type="product",
        compliance_tags=["pseudoephedrine"],
        requirement={
            "type": "id_verification",
            "variable": "customer_age",
            "operator": "greater_than_or_equal_to",
            "value": 18,
        },
        metadata={
            "regulation": "Combat Methamphetamine Epidemic Act",
            "jurisdiction": "federal",
        },
    ),
    _rule(
        "pseudoephedrine_quantity_limit",
        "BLOCK",
        20,
        {
            "all": [
                {
                    "name": "compliance_tags",
                    "operator": "contains",
                    "value": "quantity_limited",
                },
                {
                    "name": "requested_quantity",
                    "operator": "greater_than",
                    "value": 3,
                },
            ]
        },
        "Pseudoephedrine limited to 3 packages per transaction (CMEA)",
        rule_type="product",
        compliance_tags=["quantity_limited"],
        blocked_paths=ALL_PATHS,
        metadata={
            "regulation": "Combat Methamphetamine Epidemic Act",
            "jurisdiction": "federal",
        },
    ),
    _rule(
        "pseudoephedrine_quantity_acknowledgment",
        "REQUIRE",
        40,
        {
            "all": [
                {
                    "name": "compliance_tags",
                    "operator": "contains",
                    "value": "quantity_limited",
                },
            ]
        },
        "DEA requires quantity acknowledgment for pseudoephedrine products",
        rule_type="quantity",
        compliance_tags=["quantity_limited"],
        requirement={
            "type": "quantity_acknowledgment",
            "variable": "requested_quantity",
            "operator": "less_than_or_equal_to",
            "value": 3,
            "instructions": "Quantity limited to 3 per purchase (Combat Methamphetamine Act)",
        },
        metadata={
            "regulation": "Combat Methamphetamine Epidemic Act",
            "jurisdiction": "federal",
        },
    ),
    # -----------------------------------------------------------------------
    # Additional geographic rules (18-20)
    # -----------------------------------------------------------------------
    _rule(
        "hawaii_hazmat_shipping_ban",
        "BLOCK",
        15,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "HI"},
                {"name": "compliance_tags", "operator": "contains", "value": "hazmat"},
            ]
        },
        "Hazmat items cannot be shipped to Hawaii",
        market_codes=["US-HI"],
        compliance_tags=["hazmat"],
        blocked_paths=["ship_to_home", "ship_from_store"],
        metadata={"jurisdiction": "state", "note": "No ground shipping to Hawaii"},
    ),
    _rule(
        "ny_fireworks_ban",
        "BLOCK",
        30,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "NY"},
                {"name": "compliance_tags", "operator": "contains", "value": "fireworks"},
            ]
        },
        "New York bans consumer fireworks (NY Penal Law 270)",
        market_codes=["US-NY"],
        compliance_tags=["fireworks"],
        blocked_paths=ALL_PATHS,
        metadata={"regulation": "NY Penal Law 270", "jurisdiction": "state"},
    ),
    _rule(
        "alcohol_time_restriction_tx",
        "BLOCK",
        40,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "TX"},
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
                {"name": "request_hour", "operator": "less_than", "value": 10},
            ]
        },
        "Texas restricts alcohol pickup/delivery before 10am",
        market_codes=["US-TX"],
        compliance_tags=["alcohol"],
        blocked_paths=["ship_from_store", "pickup"],
        metadata={
            "regulation": "Texas Alcoholic Beverage Code",
            "jurisdiction": "state",
        },
    ),
    # -----------------------------------------------------------------------
    # Additional rules (21-25)
    # -----------------------------------------------------------------------
    _rule(
        "ky_dry_county_alcohol",
        "BLOCK",
        30,
        {
            "all": [
                {"name": "market_state", "operator": "equal_to", "value": "KY"},
                {"name": "county", "operator": "equal_to", "value": "Hardin"},
                {"name": "compliance_tags", "operator": "contains", "value": "alcohol"},
            ]
        },
        "Hardin County, KY is a dry county — alcohol sales prohibited",
        market_codes=["US-KY"],
        compliance_tags=["alcohol"],
        blocked_paths=ALL_PATHS,
        metadata={
            "regulation": "KY dry county law",
            "jurisdiction": "county",
            "county": "Hardin",
        },
    ),
    _rule(
        "aerosol_shipping_restriction",
        "BLOCK",
        25,
        {
            "all": [
                {"name": "compliance_tags", "operator": "contains", "value": "aerosol"},
                {
                    "name": "fulfillment_path",
                    "operator": "equal_to",
                    "value": "ship_to_home",
                },
            ]
        },
        "Aerosol products cannot be shipped to home (DOT regulations)",
        rule_type="product",
        compliance_tags=["aerosol"],
        blocked_paths=["ship_to_home"],
        metadata={"regulation": "DOT aerosol shipping", "jurisdiction": "federal"},
    ),
    _rule(
        "age_restricted_advisory",
        "WARN",
        150,
        {
            "all": [
                {
                    "name": "compliance_tags",
                    "operator": "contains",
                    "value": "age_restricted",
                },
            ]
        },
        "This product requires age verification at point of sale",
        rule_type="product",
        compliance_tags=["age_restricted"],
        metadata={"policy": "Age-restricted product advisory"},
    ),
    _rule(
        "seller_performance_minimum",
        "GATE",
        250,
        {
            "all": [
                {
                    "name": "seller_defect_rate",
                    "operator": "greater_than",
                    "value": 0.05,
                },
            ]
        },
        "Sellers with >5% defect rate are gated from marketplace",
        rule_type="seller",
        blocked_paths=["marketplace_3p"],
        gate={
            "type": "metric_threshold",
            "thresholds": {
                "seller_defect_rate": {"operator": "less_than", "value": 0.05},
            },
        },
        metadata={"policy": "Walmart seller performance standards"},
    ),
    _rule(
        "heavy_item_ship_from_store",
        "BLOCK",
        100,
        {
            "all": [
                {
                    "name": "item_weight_lbs",
                    "operator": "greater_than",
                    "value": 50,
                },
            ]
        },
        "Items over 50 lbs cannot be shipped from store",
        rule_type="product",
        blocked_paths=["ship_from_store"],
        metadata={"policy": "Ship-from-store weight limit"},
    ),
]


# ---------------------------------------------------------------------------
# Seed Functions
# ---------------------------------------------------------------------------


async def seed_sellers(client: httpx.AsyncClient) -> dict[str, dict]:
    """Create all sellers. Returns {seller_id: response_json}."""
    print("\n[1/8] Creating sellers...")
    results: dict[str, dict] = {}
    for seller in SELLERS:
        r = await client.post("/v1/sellers", json=seller)
        data = r.json()
        results[seller["seller_id"]] = data
        status = "OK" if r.status_code == 201 else f"ERR {r.status_code}"
        print(f"  [{status}] {seller['name']} (id={seller['seller_id']})")
    return results


async def seed_items(client: httpx.AsyncClient) -> dict[str, str]:
    """Create all items. Returns {sku: item_id}."""
    print("\n[2/8] Creating items...")
    sku_to_id: dict[str, str] = {}
    for item in ITEMS:
        r = await client.post("/v1/items", json=item)
        data = r.json()
        item_id = data.get("item_id", "?")
        sku_to_id[item["sku"]] = str(item_id)
        status = "OK" if r.status_code == 201 else f"ERR {r.status_code}"
        print(f"  [{status}] {item['sku']}: {item['name']} -> {item_id}")
    return sku_to_id


async def seed_fulfillment_paths(client: httpx.AsyncClient) -> dict[str, int]:
    """Create fulfillment paths. Returns {path_code: path_id}."""
    print("\n[3/8] Creating fulfillment paths...")
    code_to_id: dict[str, int] = {}
    for path in FULFILLMENT_PATHS:
        r = await client.post("/v1/fulfillment-paths", json=path)
        data = r.json()
        path_id = data.get("path_id", "?")
        code_to_id[path["path_code"]] = path_id
        weight = path.get("max_weight_lbs") or "unlimited"
        status = "OK" if r.status_code == 201 else f"ERR {r.status_code}"
        print(
            f"  [{status}] {path['path_code']} ({path['owner']}, "
            f"max_weight={weight}) -> path_id={path_id}"
        )
    return code_to_id


async def seed_markets(
    client: httpx.AsyncClient, path_ids: dict[str, int]
) -> None:
    """Enable all 4 fulfillment paths in all 8 markets."""
    print("\n[4/8] Creating market configurations...")
    for market in MARKETS:
        for i, path_code in enumerate(
            ["ship_to_home", "pickup", "ship_from_store", "marketplace_3p"]
        ):
            pid = path_ids[path_code]
            priority = (len(FULFILLMENT_PATHS) - i) * 10  # 40, 30, 20, 10
            r = await client.post(
                "/v1/markets",
                json={
                    "market_code": market,
                    "path_id": pid,
                    "enabled": True,
                    "priority": priority,
                },
            )
            if r.status_code != 201:
                print(f"  [ERR {r.status_code}] {market} / {path_code}: {r.text}")
        print(f"  [OK] {market}: 4 paths enabled")


async def seed_seller_offers(
    client: httpx.AsyncClient,
    sku_to_id: dict[str, str],
) -> None:
    """Link marketplace sellers to the items they offer."""
    print("\n[5/8] Creating seller offers...")
    for seller_id, skus in SELLER_OFFERS.items():
        seller_name = next(s["name"] for s in SELLERS if s["seller_id"] == seller_id)
        for sku in skus:
            item_id = sku_to_id[sku]
            r = await client.post(
                f"/v1/sellers/{seller_id}/offers",
                json={"item_id": item_id, "active": True},
            )
            status = "OK" if r.status_code == 201 else f"ERR {r.status_code}"
            print(f"  [{status}] {seller_name} -> {sku}")


async def seed_inventory(
    client: httpx.AsyncClient,
    sku_to_id: dict[str, str],
    path_ids: dict[str, int],
) -> None:
    """Create inventory positions for all items.

    - 1P items: qty=50 at FC-DAL-01 on ship_to_home, pickup, ship_from_store
    - 3P marketplace items: qty=25 at 3P-WAREHOUSE on marketplace_3p for each seller
    """
    print("\n[6/8] Creating inventory positions...")
    one_p_paths = ["ship_to_home", "pickup", "ship_from_store"]

    # 1P inventory for all 15 items at FC-DAL-01
    count = 0
    for item in ITEMS:
        sku = item["sku"]
        item_id = sku_to_id[sku]
        for path_code in one_p_paths:
            r = await client.post(
                "/v1/inventory/positions",
                json={
                    "item_id": item_id,
                    "fulfillment_node": "FC-DAL-01",
                    "path_id": path_ids[path_code],
                    "seller_id": WALMART_SELLER_ID,
                    "available_qty": 50,
                    "reserved_qty": 0,
                    "node_enabled": True,
                },
            )
            count += 1
    print(f"  [OK] {count} 1P positions (FC-DAL-01, Walmart, qty=50)")

    # 3P inventory for marketplace seller offers at 3P-WAREHOUSE
    mp_count = 0
    for seller_id, skus in SELLER_OFFERS.items():
        seller_name = next(s["name"] for s in SELLERS if s["seller_id"] == seller_id)
        for sku in skus:
            item_id = sku_to_id[sku]
            r = await client.post(
                "/v1/inventory/positions",
                json={
                    "item_id": item_id,
                    "fulfillment_node": "3P-WAREHOUSE",
                    "path_id": path_ids["marketplace_3p"],
                    "seller_id": seller_id,
                    "available_qty": 25,
                    "reserved_qty": 0,
                    "node_enabled": True,
                },
            )
            mp_count += 1
        print(f"  [OK] {seller_name}: {len(skus)} 3P positions (3P-WAREHOUSE, qty=25)")
    print(f"  Total: {count} 1P + {mp_count} 3P = {count + mp_count} positions")


async def seed_rules(client: httpx.AsyncClient) -> dict[str, int]:
    """Create all 25 compliance rules. Returns {rule_name: rule_id}."""
    print("\n[7/8] Creating compliance rules...")
    name_to_id: dict[str, int] = {}
    for i, rule in enumerate(COMPLIANCE_RULES, 1):
        r = await client.post("/v1/rules", json=rule)
        data = r.json()
        rule_id = data.get("rule_id", "?")
        name_to_id[rule["rule_name"]] = rule_id
        status = "OK" if r.status_code == 201 else f"ERR {r.status_code}"
        action = rule["action"]
        print(f"  [{status}] {i:2d}. [{action:7s}] {rule['rule_name']} -> rule_id={rule_id}")
    return name_to_id


def print_test_commands(sku_to_id: dict[str, str]) -> None:
    """Print curl commands for each of the 10 demo scenarios."""
    print("\n[8/8] Test curl commands for each scenario:")
    print("=" * 80)

    wine_id = sku_to_id["ALC-001"]
    chlorine_id = sku_to_id["CHEM-001"]
    fireworks_id = sku_to_id["FIRE-001"]
    supplement_id = sku_to_id["SUPP-001"]
    rifle_id = sku_to_id["FIRE-002"]
    raid_id = sku_to_id["CHEM-002"]
    samsung_id = sku_to_id["ELEC-001"]
    bourbon_id = sku_to_id["ALC-002"]
    sudafed_id = sku_to_id["PHARM-001"]
    milk_id = sku_to_id["GROC-001"]
    white_claw_id = sku_to_id["ALC-003"]

    def _curl(desc: str, body: dict) -> str:
        import json

        payload = json.dumps(body, separators=(",", ":"))
        return (
            f"\n# {desc}\n"
            f"curl -s -X POST {BASE_URL}/v1/evaluate "
            f'-H "Content-Type: application/json" '
            f"-d '{payload}' | python3 -m json.tool"
        )

    # Scenario 1: Wine in Utah (BLOCKED) vs Colorado (ALLOWED)
    print("\n--- Scenario 1: Wine in Utah vs Colorado ---")
    print(
        _curl(
            "Wine in UTAH -> BLOCKED (all paths)",
            {
                "item_id": wine_id,
                "market_code": "US-UT",
                "customer_location": {"state": "UT", "zip": "84101"},
                "timestamp": "2026-07-04T14:00:00-06:00",
            },
        )
    )
    print(
        _curl(
            "Wine in COLORADO -> ALLOWED (age req + advisory)",
            {
                "item_id": wine_id,
                "market_code": "US-CO",
                "customer_location": {"state": "CO", "zip": "80202"},
                "timestamp": "2026-07-04T14:00:00-06:00",
                "context": {"customer_age": 25},
            },
        )
    )

    # Scenario 2: Pool chlorine — hazmat blocks shipping, pickup OK
    print("\n--- Scenario 2: Pool Chlorine Paths ---")
    print(
        _curl(
            "Pool chlorine in TEXAS -> shipping BLOCKED, pickup ALLOWED",
            {
                "item_id": chlorine_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )

    # Scenario 3: Fireworks — seasonal + geography
    print("\n--- Scenario 3: Fireworks (TX Jul / TX Oct / MA) ---")
    print(
        _curl(
            "Fireworks in TEXAS, JULY -> pickup ALLOWED (in season)",
            {
                "item_id": fireworks_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )
    print(
        _curl(
            "Fireworks in TEXAS, OCTOBER -> GATED (out of season)",
            {
                "item_id": fireworks_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-10-15T14:00:00-05:00",
            },
        )
    )
    print(
        _curl(
            "Fireworks in MASSACHUSETTS -> BLOCKED (total ban)",
            {
                "item_id": fireworks_id,
                "market_code": "US-MA",
                "customer_location": {"state": "MA", "zip": "02101"},
                "timestamp": "2026-07-04T14:00:00-04:00",
            },
        )
    )

    # Scenario 4: Supplement in CA (Prop 65 warning)
    print("\n--- Scenario 4: Supplement Prop 65 in California ---")
    print(
        _curl(
            "Supplement in CALIFORNIA -> ALLOWED with Prop 65 WARNING",
            {
                "item_id": supplement_id,
                "market_code": "US-CA",
                "customer_location": {"state": "CA", "zip": "90210"},
                "timestamp": "2026-07-04T14:00:00-07:00",
            },
        )
    )

    # Scenario 5: Rifle — 1P OK (with age), 3P blocked
    print("\n--- Scenario 5: Rifle 1P vs 3P ---")
    print(
        _curl(
            "Rifle, 1P, age 25 -> ALLOWED on 1P (advisory warning)",
            {
                "item_id": rifle_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
                "context": {"customer_age": 25},
            },
        )
    )
    print(
        _curl(
            "Rifle, no age context -> REQUIRE age verification",
            {
                "item_id": rifle_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )

    # Scenario 6: Seller hazmat quality gate
    print("\n--- Scenario 6: Seller Hazmat Quality Gate ---")
    print(
        _curl(
            "Raid spray, ChemSupply (4.5% defect) -> marketplace GATED",
            {
                "item_id": raid_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "seller_id": CHEMSUPPLY_SELLER_ID,
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )

    # Scenario 7: 3P alcohol — seller trust gate
    print("\n--- Scenario 7: 3P Alcohol Seller Trust ---")
    print(
        _curl(
            "White Claw via Acme Wines (trusted) -> marketplace ALLOWED",
            {
                "item_id": white_claw_id,
                "market_code": "US-CO",
                "customer_location": {"state": "CO", "zip": "80202"},
                "seller_id": ACME_WINES_SELLER_ID,
                "timestamp": "2026-07-04T14:00:00-06:00",
                "context": {"customer_age": 25},
            },
        )
    )
    print(
        _curl(
            "Bourbon via NewSeller123 (new tier) -> marketplace GATED",
            {
                "item_id": bourbon_id,
                "market_code": "US-CO",
                "customer_location": {"state": "CO", "zip": "80202"},
                "seller_id": NEWSELLER_SELLER_ID,
                "timestamp": "2026-07-04T14:00:00-06:00",
                "context": {"customer_age": 25},
            },
        )
    )

    # Scenario 8: Electronics seller trust gate
    print("\n--- Scenario 8: Electronics Seller Trust ---")
    print(
        _curl(
            "Samsung via TechGear Pro (trusted) -> marketplace ALLOWED",
            {
                "item_id": samsung_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "seller_id": TECHGEAR_SELLER_ID,
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )
    print(
        _curl(
            "Samsung via NewSeller123 (new tier) -> marketplace GATED",
            {
                "item_id": samsung_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "seller_id": NEWSELLER_SELLER_ID,
                "timestamp": "2026-07-04T14:00:00-05:00",
            },
        )
    )

    # Scenario 9: Pseudoephedrine quantity limit
    print("\n--- Scenario 9: Pseudoephedrine Quantity Limit ---")
    print(
        _curl(
            "Sudafed, qty=2 -> ALLOWED (requires ID)",
            {
                "item_id": sudafed_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
                "context": {"customer_age": 30, "requested_quantity": 2},
            },
        )
    )
    print(
        _curl(
            "Sudafed, qty=5 -> BLOCKED (exceeds quantity limit)",
            {
                "item_id": sudafed_id,
                "market_code": "US-TX",
                "customer_location": {"state": "TX", "zip": "75201"},
                "timestamp": "2026-07-04T14:00:00-05:00",
                "context": {"customer_age": 30, "requested_quantity": 5},
            },
        )
    )

    # Scenario 10: Inventory depletion (use events endpoint)
    print("\n--- Scenario 10: Inventory Depletion ---")
    print(
        f"\n# First, check milk is available (qty=50)"
        f"\ncurl -s -X POST {BASE_URL}/v1/evaluate "
        f'-H "Content-Type: application/json" '
        f"-d '"
        f'{{"item_id":"{milk_id}","market_code":"US-TX",'
        f'"customer_location":{{"state":"TX","zip":"75201"}},'
        f'"timestamp":"2026-07-04T14:00:00-05:00"}}'
        f"' | python3 -m json.tool"
    )
    print(
        f"\n# Deplete inventory via event (delta=-50)"
        f"\ncurl -s -X POST {BASE_URL}/v1/inventory/events "
        f'-H "Content-Type: application/json" '
        f"-d '"
        f'{{"item_id":"{milk_id}","fulfillment_node":"FC-DAL-01",'
        f'"event_type":"adjustment","path_id":1,'
        f'"seller_id":"{WALMART_SELLER_ID}","delta":-50}}'
        f"' | python3 -m json.tool"
    )
    print(
        f"\n# Re-evaluate: milk should now be OUT OF STOCK"
        f"\ncurl -s -X POST {BASE_URL}/v1/evaluate "
        f'-H "Content-Type: application/json" '
        f"-d '"
        f'{{"item_id":"{milk_id}","market_code":"US-TX",'
        f'"customer_location":{{"state":"TX","zip":"75201"}},'
        f'"timestamp":"2026-07-04T14:00:00-05:00"}}'
        f"' | python3 -m json.tool"
    )

    print("\n" + "=" * 80)
    print("Seed complete. All 10 scenarios ready for testing.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def seed():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        print("=" * 60)
        print("  Walmart Transactability Engine — Full Demo Seed")
        print("=" * 60)
        print(f"  Target: {BASE_URL}")
        print(f"  Items: {len(ITEMS)}")
        print(f"  Sellers: {len(SELLERS)}")
        print(f"  Fulfillment Paths: {len(FULFILLMENT_PATHS)}")
        print(f"  Markets: {len(MARKETS)}")
        print(f"  Compliance Rules: {len(COMPLIANCE_RULES)}")
        print(f"  Seller Offer Links: {sum(len(v) for v in SELLER_OFFERS.values())}")

        # Step 1: Sellers
        await seed_sellers(client)

        # Step 2: Items
        sku_to_id = await seed_items(client)

        # Step 3: Fulfillment Paths
        path_ids = await seed_fulfillment_paths(client)

        # Step 4: Markets
        await seed_markets(client, path_ids)

        # Step 5: Seller Offers
        await seed_seller_offers(client, sku_to_id)

        # Step 6: Inventory
        await seed_inventory(client, sku_to_id, path_ids)

        # Step 7: Compliance Rules
        await seed_rules(client)

        # Step 8: Print test commands
        print_test_commands(sku_to_id)


if __name__ == "__main__":
    asyncio.run(seed())

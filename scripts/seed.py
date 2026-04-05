"""Seed script for the vertical slice demo.
Run with: python -m scripts.seed
Requires all services to be running (docker compose up).
"""
import asyncio

import httpx

BASE_URL = "http://localhost"
WALMART_SELLER_ID = "00000000-0000-0000-0000-000000000001"


async def seed():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
        print("=== Seeding Walmart Transactability Engine ===\n")

        # 1. Create Walmart seller
        print("1. Creating Walmart seller...")
        r = await client.post(
            "/v1/sellers",
            json={
                "seller_id": WALMART_SELLER_ID,
                "name": "Walmart",
                "trust_tier": "top_rated",
                "defect_rate": 0.001,
                "on_time_rate": 0.99,
                "total_orders": 1000000,
            },
        )
        print(f"   {r.status_code}: {r.json()}")

        # 2. Create wine item
        print("2. Creating wine item...")
        r = await client.post(
            "/v1/items",
            json={
                "sku": "ALC-001",
                "name": "Caymus Cabernet Sauvignon 2021",
                "item_type": "base",
                "category_path": "alcohol.wine.red",
                "attributes": {"weight_lbs": 3.2, "abv": 14.6, "volume_ml": 750},
                "compliance_tags": ["alcohol", "age_restricted"],
            },
        )
        wine = r.json()
        wine_id = wine["item_id"]
        print(f"   {r.status_code}: {wine['name']} ({wine_id})")

        # 3. Create fulfillment paths
        print("3. Creating fulfillment paths...")
        r1 = await client.post(
            "/v1/fulfillment-paths",
            json={
                "path_code": "ship_to_home",
                "display_name": "Ship to Home",
                "owner": "1p",
                "requires_inventory": True,
                "max_weight_lbs": 150,
            },
        )
        ship_path = r1.json()
        print(f"   ship_to_home: path_id={ship_path['path_id']}")

        r2 = await client.post(
            "/v1/fulfillment-paths",
            json={
                "path_code": "pickup",
                "display_name": "Store Pickup",
                "owner": "1p",
                "requires_inventory": True,
            },
        )
        pickup_path = r2.json()
        print(f"   pickup: path_id={pickup_path['path_id']}")

        # 4. Create market configs (US-UT and US-CO)
        print("4. Creating market configs...")
        for market in ["US-UT", "US-CO"]:
            for path in [ship_path, pickup_path]:
                r = await client.post(
                    "/v1/markets",
                    json={
                        "market_code": market,
                        "path_id": path["path_id"],
                        "enabled": True,
                        "priority": 10
                        if path["path_id"] == ship_path["path_id"]
                        else 5,
                    },
                )
            print(f"   {market}: 2 paths enabled")

        # 5. Create inventory positions
        print("5. Creating inventory positions...")
        for path in [ship_path, pickup_path]:
            r = await client.post(
                "/v1/inventory/positions",
                json={
                    "item_id": wine_id,
                    "fulfillment_node": "FC-DAL-01",
                    "path_id": path["path_id"],
                    "seller_id": WALMART_SELLER_ID,
                    "available_qty": 50,
                    "reserved_qty": 0,
                    "node_enabled": True,
                },
            )
            print(f"   FC-DAL-01, path_id={path['path_id']}: qty=50")

        # 6. Create compliance rule: Utah alcohol ban
        print("6. Creating compliance rules...")
        r = await client.post(
            "/v1/rules",
            json={
                "rule_name": "utah_alcohol_prohibition",
                "rule_type": "geographic",
                "action": "BLOCK",
                "priority": 10,
                "market_codes": ["US-UT"],
                "compliance_tags": ["alcohol"],
                "blocked_paths": ["ship_to_home", "pickup"],
                "rule_definition": {
                    "conditions": {
                        "all": [
                            {
                                "name": "market_state",
                                "operator": "equal_to",
                                "value": "UT",
                            },
                            {
                                "name": "compliance_tags",
                                "operator": "contains",
                                "value": "alcohol",
                            },
                        ]
                    }
                },
                "reason": "Utah prohibits alcohol delivery (Utah Code 32B-1-201)",
                "effective_from": "2020-01-01T00:00:00-07:00",
                "metadata": {
                    "regulation": "Utah Code 32B-1-201",
                    "jurisdiction": "state",
                },
            },
        )
        print(f"   utah_alcohol_prohibition: rule_id={r.json().get('rule_id')}")

        print(f"\n=== Seed complete ===")
        print(f"Wine item ID: {wine_id}")
        print(f"\nTest with:")
        print(
            f"  curl -s -X POST {BASE_URL}/v1/evaluate"
            f' -H "Content-Type: application/json"'
            f" -d '"
            f'{{"item_id":"{wine_id}","market_code":"US-UT",'
            f'"customer_location":{{"state":"UT","zip":"84101"}},'
            f'"timestamp":"2026-04-04T14:00:00-07:00"}}'
            f"' | python3 -m json.tool"
        )
        print(
            f"  curl -s -X POST {BASE_URL}/v1/evaluate"
            f' -H "Content-Type: application/json"'
            f" -d '"
            f'{{"item_id":"{wine_id}","market_code":"US-CO",'
            f'"customer_location":{{"state":"CO","zip":"80202"}},'
            f'"timestamp":"2026-04-04T14:00:00-07:00"}}'
            f"' | python3 -m json.tool"
        )


if __name__ == "__main__":
    asyncio.run(seed())

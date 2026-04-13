"""Tests for new features: debug mode, sellers list, display_metadata, demo scenarios, error shape.

Requires: docker compose up + seed script already run.
Run with: pytest tests/test_new_features.py -v
"""

import os

import pytest
import httpx

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost")
TIMEOUT = 15.0

PLATFORM_SELLER_ID = "00000000-0000-0000-0000-000000000001"
ACME_WINES_SELLER_ID = "00000000-0000-0000-0000-000000000002"
TECHGEAR_SELLER_ID = "00000000-0000-0000-0000-000000000003"
NEWSELLER_SELLER_ID = "00000000-0000-0000-0000-000000000004"
CHEMSUPPLY_SELLER_ID = "00000000-0000-0000-0000-000000000005"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def items(client):
    r = client.get("/v1/items")
    assert r.status_code == 200
    return {item["sku"]: item for item in r.json()}


# ---------------------------------------------------------------------------
# Debug mode tests
# ---------------------------------------------------------------------------


def test_evaluate_debug_flag(client, items):
    """?debug=true returns debug.per_path_evaluations."""
    item = items["ALC-001"]
    r = client.post(
        "/v1/evaluate?debug=true",
        json={
            "item_id": item["item_id"],
            "market_code": "US-UT",
            "customer_location": {"state": "UT", "zip": "84101"},
            "timestamp": "2026-07-04T14:00:00-06:00",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["debug"] is not None
    assert "per_path_evaluations" in data["debug"]
    assert len(data["debug"]["per_path_evaluations"]) > 0
    # Each path eval should have rules
    for pe in data["debug"]["per_path_evaluations"]:
        assert "path_code" in pe
        assert "rules" in pe
        assert len(pe["rules"]) > 0


def test_evaluate_debug_suppression(client, items):
    """A suppressed rule has matched=true, suppressed=true, suppressed_by={...}."""
    # Scenario 3 (fireworks in MA) has conflict resolution
    item = items["FIRE-001"]
    r = client.post(
        "/v1/evaluate?debug=true",
        json={
            "item_id": item["item_id"],
            "market_code": "US-MA",
            "customer_location": {"state": "MA", "zip": "02101"},
            "timestamp": "2026-07-04T14:00:00-04:00",
        },
    )
    assert r.status_code == 200
    data = r.json()
    debug = data["debug"]
    assert debug is not None

    # Check if any conflict resolutions exist
    if data["conflict_resolutions"]:
        suppressed_ids = {cr["suppressed_rule_id"] for cr in data["conflict_resolutions"]}
        # Find the suppressed rule in per_path_evaluations
        for pe in debug["per_path_evaluations"]:
            for rule in pe["rules"]:
                if rule["rule_id"] in suppressed_ids:
                    assert rule["matched"] is True
                    assert rule["suppressed"] is True
                    assert rule["suppressed_by"] is not None


def test_evaluate_debug_survived(client, items):
    """Non-suppressed matched rule has survived=true."""
    item = items["ALC-001"]
    r = client.post(
        "/v1/evaluate?debug=true",
        json={
            "item_id": item["item_id"],
            "market_code": "US-UT",
            "customer_location": {"state": "UT", "zip": "84101"},
            "timestamp": "2026-07-04T14:00:00-06:00",
        },
    )
    data = r.json()
    for pe in data["debug"]["per_path_evaluations"]:
        for rule in pe["rules"]:
            if rule["matched"] and not rule["suppressed"]:
                assert rule["survived"] is True


def test_evaluate_no_debug(client, items):
    """Without ?debug=true, response has debug: null."""
    item = items["ALC-001"]
    r = client.post(
        "/v1/evaluate",
        json={
            "item_id": item["item_id"],
            "market_code": "US-UT",
            "customer_location": {"state": "UT", "zip": "84101"},
            "timestamp": "2026-07-04T14:00:00-06:00",
        },
    )
    data = r.json()
    assert data["debug"] is None


def test_evaluate_rules_loaded_count(client, items):
    """rules_loaded counts all candidate rules, not just triggered."""
    item = items["ALC-001"]
    r = client.post(
        "/v1/evaluate?debug=true",
        json={
            "item_id": item["item_id"],
            "market_code": "US-UT",
            "customer_location": {"state": "UT", "zip": "84101"},
            "timestamp": "2026-07-04T14:00:00-06:00",
        },
    )
    data = r.json()
    assert data["rules_loaded"] >= data["rules_evaluated"]
    assert data["debug"]["rules_loaded"] == data["rules_loaded"]


# ---------------------------------------------------------------------------
# Demo scenarios endpoint
# ---------------------------------------------------------------------------


def test_demo_scenarios(client):
    """GET /v1/demo/scenarios returns the expanded scenario catalog."""
    r = client.get("/v1/demo/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 24
    for s in data:
        assert "id" in s
        assert "label" in s
        assert "short_label" in s
        assert "variants" in s
        assert len(s["variants"]) >= 1


def test_markets_endpoint_includes_international_markets(client):
    r = client.get("/v1/markets")
    assert r.status_code == 200
    market_codes = {market["market_code"] for market in r.json()}
    assert {"MX-CDMX", "CL-RM", "CR-SJ", "CA-ON"}.issubset(market_codes)


def test_seller_ipi_endpoint(client):
    r = client.get(f"/v1/sellers/{TECHGEAR_SELLER_ID}/ipi")
    assert r.status_code == 200
    data = r.json()
    assert data["ipi_score"] >= 0
    assert "tier" in data


def test_seller_performance_endpoint(client):
    r = client.get(f"/v1/sellers/{TECHGEAR_SELLER_ID}/performance")
    assert r.status_code == 200
    data = r.json()
    assert data["overall_status"] in {"good_standing", "action_required"}
    assert data["standards_last_updated"] == "2026-03-25"
    metric_codes = {metric["code"] for metric in data["metrics"]}
    assert {
        "cancellation_rate",
        "on_time_delivery_rate",
        "valid_tracking_rate",
        "seller_response_rate",
        "return_rate",
        "item_not_received_rate",
        "negative_feedback_rate",
    }.issubset(metric_codes)


# ---------------------------------------------------------------------------
# Sellers list endpoints
# ---------------------------------------------------------------------------


def test_sellers_list_excludes_platform_seller(client):
    """GET /v1/sellers excludes PLATFORM_SELLER_ID and includes expected 3P sellers."""
    r = client.get("/v1/sellers")
    assert r.status_code == 200
    data = r.json()
    seller_ids = {str(s["seller_id"]) for s in data}
    assert PLATFORM_SELLER_ID not in seller_ids
    assert ACME_WINES_SELLER_ID in seller_ids
    assert TECHGEAR_SELLER_ID in seller_ids
    assert NEWSELLER_SELLER_ID in seller_ids
    assert CHEMSUPPLY_SELLER_ID in seller_ids
    seller_map = {str(s["seller_id"]): s for s in data}
    assert seller_map[TECHGEAR_SELLER_ID]["performance_status"] in {
        "good_standing",
        "action_required",
    }
    assert "uses_wfs" in seller_map[TECHGEAR_SELLER_ID]


def test_sellers_for_item_returns_only_offerers(client, items):
    """GET /v1/sellers/for-item/{id} returns seller_ids {TECHGEAR, NEWSELLER} for ELEC-001."""
    item = items["ELEC-001"]
    r = client.get(f"/v1/sellers/for-item/{item['item_id']}")
    assert r.status_code == 200
    data = r.json()
    seller_ids = {str(s["seller_id"]) for s in data}
    assert seller_ids == {TECHGEAR_SELLER_ID, NEWSELLER_SELLER_ID}


def test_sellers_for_item_no_offers(client, items):
    """GET /v1/sellers/for-item/{id} returns empty list for 1P-only items."""
    item = items["GROC-001"]
    r = client.get(f"/v1/sellers/for-item/{item['item_id']}")
    assert r.status_code == 200
    data = r.json()
    assert data == []


# ---------------------------------------------------------------------------
# Display metadata
# ---------------------------------------------------------------------------


def test_items_display_metadata(client):
    """GET /v1/items includes display_metadata with price/emoji."""
    r = client.get("/v1/items")
    assert r.status_code == 200
    data = r.json()
    for item in data:
        assert "display_metadata" in item
        meta = item["display_metadata"]
        if meta:  # backfill may not have run on all items
            assert "price" in meta or "emoji" in meta


def test_items_create_with_metadata(client):
    """POST /v1/items with display_metadata persists and returns it."""
    import uuid
    unique_sku = f"TEST-META-{uuid.uuid4().hex[:8]}"
    payload = {
        "sku": unique_sku,
        "name": "Test Metadata Item",
        "display_metadata": {"price": "9.99", "emoji": "🧪", "description": "Test item"},
    }
    r = client.post("/v1/items", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["display_metadata"]["price"] == "9.99"
    assert data["display_metadata"]["emoji"] == "🧪"


# ---------------------------------------------------------------------------
# Error response shape
# ---------------------------------------------------------------------------


def test_evaluate_error_response_shape(client):
    """Error responses include rules_loaded: 0 and debug: null."""
    r = client.post(
        "/v1/evaluate",
        json={
            "item_id": "00000000-0000-0000-0000-999999999999",
            "market_code": "US-TX",
            "customer_location": {"state": "TX", "zip": "75201"},
            "timestamp": "2026-07-04T14:00:00-05:00",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["eligible"] is False
    assert len(data["errors"]) > 0
    assert data["rules_loaded"] == 0
    assert data["debug"] is None

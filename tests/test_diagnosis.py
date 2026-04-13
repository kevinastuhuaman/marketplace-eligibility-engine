"""Integration tests for diagnosis flows."""

import os

import httpx
import pytest

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost")
TIMEOUT = 15.0


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def items(client):
    response = client.get("/v1/items")
    assert response.status_code == 200
    return {item["sku"]: item for item in response.json()}


def test_diagnose_blocked_item_returns_primary_finding(client, items):
    wine = items["ALC-001"]
    response = client.post(
        "/v1/diagnose",
        json={
            "item_id": wine["item_id"],
            "market_code": "US-UT",
            "customer_location": {"state": "UT", "zip": "84101"},
            "timestamp": "2026-07-04T14:00:00-06:00",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "blocked"
    assert payload["primary_finding"] is not None
    assert len(payload["findings"]) >= 1
    assert "trace" in payload


def test_diagnose_spanish_market_uses_localized_explanation(client, items):
    item = items["ALC-005"]
    response = client.post(
        "/v1/diagnose",
        json={
            "item_id": item["item_id"],
            "market_code": "MX-CDMX",
            "customer_location": {"state": "CDMX", "zip": "01000"},
            "seller_id": "00000000-0000-0000-0000-000000000002",
            "timestamp": "2026-07-04T14:00:00-06:00",
            "context": {"customer_age": 25},
            "locale": "es",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["findings"]
    assert payload["findings"][0]["localized_explanation"]


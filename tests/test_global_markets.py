"""Integration tests for global market support."""

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


def test_markets_endpoint_lists_supported_paths(client):
    response = client.get("/v1/markets")
    assert response.status_code == 200
    markets = response.json()
    mexico = next(market for market in markets if market["market_code"] == "MX-CDMX")
    assert "ship_to_home" in mexico["supported_paths"]
    assert mexico["country_code"] == "MX"


def test_same_item_differs_across_markets(client, items):
    item = items["ALC-005"]
    us = client.post(
        "/v1/evaluate",
        json={
            "item_id": item["item_id"],
            "market_code": "US-CA",
            "customer_location": {"state": "CA", "zip": "90210"},
            "timestamp": "2026-07-04T14:00:00-07:00",
            "seller_id": "00000000-0000-0000-0000-000000000002",
            "context": {"customer_age": 25},
        },
    )
    mx = client.post(
        "/v1/evaluate",
        json={
            "item_id": item["item_id"],
            "market_code": "MX-CDMX",
            "customer_location": {"state": "CDMX", "zip": "01000"},
            "timestamp": "2026-07-04T14:00:00-06:00",
            "seller_id": "00000000-0000-0000-0000-000000000002",
            "context": {"customer_age": 25},
        },
    )
    assert us.status_code == 200
    assert mx.status_code == 200
    assert us.json()["market_code"] != mx.json()["market_code"]


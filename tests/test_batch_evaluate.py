"""Integration tests for batch evaluation."""

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


def test_batch_evaluate_returns_metrics(client, items):
    wine = items["ALC-001"]
    cereal = items["GROC-002"]
    response = client.post(
        "/v1/evaluate/batch",
        json={
            "requests": [
                {
                    "item_id": wine["item_id"],
                    "market_code": "US-UT",
                    "customer_location": {"state": "UT", "zip": "84101"},
                    "timestamp": "2026-07-04T14:00:00-06:00",
                },
                {
                    "item_id": cereal["item_id"],
                    "market_code": "CL-RM",
                    "customer_location": {"state": "RM", "zip": "8320000"},
                    "timestamp": "2026-07-04T14:00:00-04:00",
                },
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_requests"] == 2
    assert len(payload["results"]) == 2
    assert "p95_ms" in payload

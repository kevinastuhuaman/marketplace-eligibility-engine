import httpx
from time import perf_counter
from uuid import UUID

from app.config import settings
from app.services.circuit_breaker_service import (
    CircuitBreakerOpenError,
    ensure_request_allowed,
    record_failure,
    record_success,
)
from app.services.fallback_cache_service import get_cached, set_cached
from app.services.trace_context import record_trace
from shared.http_client import create_client, get_with_retry

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = create_client(settings.inventory_service_url)
    return _client


async def get_availability(
    item_id: UUID,
    path_ids: list[int],
    seller_id: UUID,
    *,
    primary_node: str | None = None,
    nearby_nodes: list[str] | None = None,
) -> dict:
    """Fetch inventory availability from inventory-service."""
    cache_key = f"{item_id}:{seller_id}:{','.join(str(path_id) for path_id in path_ids)}:{primary_node}:{','.join(nearby_nodes or [])}"
    client = get_client()
    state = ensure_request_allowed("inventory-service")
    params = {
        "item_id": str(item_id),
        "path_ids": ",".join(str(p) for p in path_ids),
        "seller_id": str(seller_id),
    }
    if primary_node:
        params["primary_node"] = primary_node
    if nearby_nodes:
        params["nearby_nodes"] = ",".join(nearby_nodes)
    started = perf_counter()
    try:
        response = await get_with_retry(
            client, "/v1/inventory/availability", params=params
        )
        payload = response.json()
        record_success("inventory-service")
        set_cached("inventory-service", cache_key, payload)
        record_trace(
            service="inventory-service",
            operation="GET /v1/inventory/availability",
            request_summary=params,
            response_summary={"paths": len(payload.get("paths", []))},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except CircuitBreakerOpenError:
        cached = get_cached("inventory-service", cache_key)
        if cached:
            record_trace(
                service="inventory-service",
                operation="GET /v1/inventory/availability",
                request_summary=params,
                response_summary={"fallback": "cache"},
                cache_hit=True,
                state="open",
            )
            return cached
        return {
            "item_id": str(item_id),
            "seller_id": str(seller_id),
            "paths": [
                {
                    "path_id": path_id,
                    "path_code": "",
                    "total_sellable": 0,
                    "nodes": [],
                    "service_unavailable": True,
                }
                for path_id in path_ids
            ],
        }
    except Exception as exc:
        record_failure("inventory-service", str(exc))
        cached = get_cached("inventory-service", cache_key)
        if cached:
            record_trace(
                service="inventory-service",
                operation="GET /v1/inventory/availability",
                request_summary=params,
                response_summary={"fallback": "cache"},
                duration_ms=int((perf_counter() - started) * 1000),
                cache_hit=True,
                state="open",
            )
            return cached
        return {
            "item_id": str(item_id),
            "seller_id": str(seller_id),
            "paths": [
                {
                    "path_id": path_id,
                    "path_code": "",
                    "total_sellable": 0,
                    "nodes": [],
                    "service_unavailable": True,
                }
                for path_id in path_ids
            ],
        }

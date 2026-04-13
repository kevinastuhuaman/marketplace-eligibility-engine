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
        _client = create_client(settings.item_service_url)
    return _client


async def get_item(item_id: UUID) -> dict | None:
    """Fetch item data from item-service. Returns None if not found."""
    cache_key = str(item_id)
    client = get_client()
    state = ensure_request_allowed("item-service")
    started = perf_counter()
    try:
        response = await get_with_retry(client, f"/v1/items/{item_id}")
        payload = response.json()
        record_success("item-service")
        set_cached("item-service", cache_key, payload)
        record_trace(
            service="item-service",
            operation="GET /v1/items/{item_id}",
            request_summary={"item_id": str(item_id)},
            response_summary={"found": True},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            record_trace(
                service="item-service",
                operation="GET /v1/items/{item_id}",
                request_summary={"item_id": str(item_id)},
                response_summary={"found": False},
                duration_ms=int((perf_counter() - started) * 1000),
                state=state.state,
            )
            return None
        record_failure("item-service", str(e))
        cached = get_cached("item-service", cache_key)
        if cached:
            record_trace(
                service="item-service",
                operation="GET /v1/items/{item_id}",
                request_summary={"item_id": str(item_id)},
                response_summary={"fallback": "cache"},
                duration_ms=int((perf_counter() - started) * 1000),
                cache_hit=True,
                state="open",
            )
            return cached
        raise
    except CircuitBreakerOpenError:
        cached = get_cached("item-service", cache_key)
        if cached:
            record_trace(
                service="item-service",
                operation="GET /v1/items/{item_id}",
                request_summary={"item_id": str(item_id)},
                response_summary={"fallback": "cache"},
                cache_hit=True,
                state="open",
            )
            return cached
        raise
    except Exception as exc:
        record_failure("item-service", str(exc))
        cached = get_cached("item-service", cache_key)
        if cached:
            record_trace(
                service="item-service",
                operation="GET /v1/items/{item_id}",
                request_summary={"item_id": str(item_id)},
                response_summary={"fallback": "cache"},
                duration_ms=int((perf_counter() - started) * 1000),
                cache_hit=True,
                state="open",
            )
            return cached
        raise

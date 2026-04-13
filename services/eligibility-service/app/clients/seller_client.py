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
        _client = create_client(settings.seller_service_url)
    return _client


async def get_seller(seller_id: UUID) -> dict | None:
    client = get_client()
    cache_key = str(seller_id)
    started = perf_counter()
    try:
        state = ensure_request_allowed("seller-service")
        response = await get_with_retry(client, f"/v1/sellers/{seller_id}")
        payload = response.json()
        record_success("seller-service")
        set_cached("seller-service", cache_key, payload)
        record_trace(
            service="seller-service",
            operation="GET /v1/sellers/{seller_id}",
            request_summary={"seller_id": str(seller_id)},
            response_summary={"found": True},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            record_trace(
                service="seller-service",
                operation="GET /v1/sellers/{seller_id}",
                request_summary={"seller_id": str(seller_id)},
                response_summary={"found": False},
                duration_ms=int((perf_counter() - started) * 1000),
                state=state.state,
            )
            return None
        record_failure("seller-service", str(e))
        cached = get_cached("seller-service", cache_key)
        if cached:
            record_trace(
                service="seller-service",
                operation="GET /v1/sellers/{seller_id}",
                request_summary={"seller_id": str(seller_id)},
                response_summary={"fallback": "cache"},
                duration_ms=int((perf_counter() - started) * 1000),
                cache_hit=True,
                state="open",
            )
            return cached
        raise
    except CircuitBreakerOpenError:
        cached = get_cached("seller-service", cache_key)
        if cached:
            record_trace(
                service="seller-service",
                operation="GET /v1/sellers/{seller_id}",
                request_summary={"seller_id": str(seller_id)},
                response_summary={"fallback": "cache"},
                cache_hit=True,
                state="open",
            )
            return cached
        raise
    except Exception as exc:
        record_failure("seller-service", str(exc))
        cached = get_cached("seller-service", cache_key)
        if cached:
            record_trace(
                service="seller-service",
                operation="GET /v1/sellers/{seller_id}",
                request_summary={"seller_id": str(seller_id)},
                response_summary={"fallback": "cache"},
                duration_ms=int((perf_counter() - started) * 1000),
                cache_hit=True,
                state="open",
            )
            return cached
        raise


async def check_offer(seller_id: UUID, item_id: UUID) -> dict:
    client = get_client()
    started = perf_counter()
    try:
        state = ensure_request_allowed("seller-service")
        response = await get_with_retry(
            client, f"/v1/sellers/{seller_id}/offers/{item_id}"
        )
        payload = response.json()
        record_success("seller-service")
        record_trace(
            service="seller-service",
            operation="GET /v1/sellers/{seller_id}/offers/{item_id}",
            request_summary={"seller_id": str(seller_id), "item_id": str(item_id)},
            response_summary={"exists": payload.get("exists", False)},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            record_trace(
                service="seller-service",
                operation="GET /v1/sellers/{seller_id}/offers/{item_id}",
                request_summary={"seller_id": str(seller_id), "item_id": str(item_id)},
                response_summary={"exists": False},
                duration_ms=int((perf_counter() - started) * 1000),
                state=state.state,
            )
            return {
                "seller_id": str(seller_id),
                "item_id": str(item_id),
                "active": False,
                "exists": False,
            }
        record_failure("seller-service", str(e))
        raise
    except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
        record_failure("seller-service", str(e))
        raise


async def get_ipi(seller_id: UUID) -> dict | None:
    client = get_client()
    started = perf_counter()
    try:
        state = ensure_request_allowed("seller-service")
        response = await get_with_retry(client, f"/v1/sellers/{seller_id}/ipi")
        payload = response.json()
        record_success("seller-service")
        record_trace(
            service="seller-service",
            operation="GET /v1/sellers/{seller_id}/ipi",
            request_summary={"seller_id": str(seller_id)},
            response_summary={"ipi_score": payload.get("ipi_score")},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        record_failure("seller-service", str(e))
        raise


async def get_performance(seller_id: UUID) -> dict | None:
    client = get_client()
    started = perf_counter()
    try:
        state = ensure_request_allowed("seller-service")
        response = await get_with_retry(client, f"/v1/sellers/{seller_id}/performance")
        payload = response.json()
        record_success("seller-service")
        record_trace(
            service="seller-service",
            operation="GET /v1/sellers/{seller_id}/performance",
            request_summary={"seller_id": str(seller_id)},
            response_summary={"overall_status": payload.get("overall_status")},
            duration_ms=int((perf_counter() - started) * 1000),
            state=state.state,
        )
        return payload
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        record_failure("seller-service", str(e))
        raise

import httpx
from uuid import UUID
from app.config import settings
from shared.http_client import create_client, get_with_retry

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = create_client(settings.seller_service_url)
    return _client


async def get_seller(seller_id: UUID) -> dict | None:
    client = get_client()
    try:
        response = await get_with_retry(client, f"/v1/sellers/{seller_id}")
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


async def check_offer(seller_id: UUID, item_id: UUID) -> dict:
    client = get_client()
    try:
        response = await get_with_retry(
            client, f"/v1/sellers/{seller_id}/offers/{item_id}"
        )
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "seller_id": str(seller_id),
                "item_id": str(item_id),
                "active": False,
                "exists": False,
            }
        raise

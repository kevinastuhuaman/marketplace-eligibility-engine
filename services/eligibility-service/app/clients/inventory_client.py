import httpx
from uuid import UUID
from app.config import settings
from shared.http_client import create_client, get_with_retry

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = create_client(settings.inventory_service_url)
    return _client


async def get_availability(
    item_id: UUID, path_ids: list[int], seller_id: UUID
) -> dict:
    """Fetch inventory availability from inventory-service."""
    client = get_client()
    params = {
        "item_id": str(item_id),
        "path_ids": ",".join(str(p) for p in path_ids),
        "seller_id": str(seller_id),
    }
    response = await get_with_retry(
        client, "/v1/inventory/availability", params=params
    )
    return response.json()

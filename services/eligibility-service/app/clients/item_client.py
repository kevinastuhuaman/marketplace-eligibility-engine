import httpx
from uuid import UUID
from app.config import settings
from shared.http_client import create_client, get_with_retry

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = create_client(settings.item_service_url)
    return _client


async def get_item(item_id: UUID) -> dict | None:
    """Fetch item data from item-service. Returns None if not found."""
    client = get_client()
    try:
        response = await get_with_retry(client, f"/v1/items/{item_id}")
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise

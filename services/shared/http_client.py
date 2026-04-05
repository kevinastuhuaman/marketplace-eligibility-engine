"""Configured HTTPX async client with retries."""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

TIMEOUT = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)


def create_client(base_url: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=TIMEOUT)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
async def get_with_retry(client: httpx.AsyncClient, path: str, params: dict | None = None) -> httpx.Response:
    response = await client.get(path, params=params)
    response.raise_for_status()
    return response


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=2))
async def post_with_retry(client: httpx.AsyncClient, path: str, json: dict) -> httpx.Response:
    response = await client.post(path, json=json)
    response.raise_for_status()
    return response

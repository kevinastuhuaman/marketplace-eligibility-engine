from __future__ import annotations

import json
import time

import redis.asyncio as aioredis

from app.config import settings

_redis_client = None
_local_cache: dict[str, tuple[float, list[dict]]] = {}


def _cache_key(market_code: str) -> str:
    return f"eligibility:rules:{market_code}"


async def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            _redis_client = False
    return None if _redis_client is False else _redis_client


async def get_cached_rules(market_code: str) -> list[dict] | None:
    now = time.time()
    cached = _local_cache.get(market_code)
    if cached and cached[0] > now:
        return cached[1]

    client = await _get_redis()
    if client is None:
        return None
    payload = await client.get(_cache_key(market_code))
    if not payload:
        return None
    try:
        rules = json.loads(payload)
    except json.JSONDecodeError:
        return None
    _local_cache[market_code] = (now + settings.rule_cache_ttl_seconds, rules)
    return rules


async def set_cached_rules(market_code: str, rules: list[dict]) -> None:
    ttl = max(1, settings.rule_cache_ttl_seconds)
    _local_cache[market_code] = (time.time() + ttl, rules)
    client = await _get_redis()
    if client is None:
        return
    await client.set(_cache_key(market_code), json.dumps(rules, default=str), ex=ttl)

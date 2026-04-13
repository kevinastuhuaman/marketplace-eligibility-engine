from __future__ import annotations

from copy import deepcopy

_cache: dict[str, dict[str, dict]] = {
    "item-service": {},
    "inventory-service": {},
    "seller-service": {},
}


def cache_value(service: str, key: str, value: dict) -> None:
    if service in _cache:
        _cache[service][key] = deepcopy(value)


def get_cached_value(service: str, key: str) -> dict | None:
    value = _cache.get(service, {}).get(key)
    return deepcopy(value) if value else None


def set_cached(service: str, key: str, value: dict) -> None:
    cache_value(service, key, value)


def get_cached(service: str, key: str) -> dict | None:
    return get_cached_value(service, key)

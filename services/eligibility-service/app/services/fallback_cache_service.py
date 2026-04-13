from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy

_MAX_ENTRIES_PER_SERVICE = 1024

_cache: dict[str, OrderedDict[str, dict]] = {
    "item-service": OrderedDict(),
    "inventory-service": OrderedDict(),
    "seller-service": OrderedDict(),
}


def cache_value(service: str, key: str, value: dict) -> None:
    if service not in _cache:
        return
    store = _cache[service]
    store[key] = deepcopy(value)
    store.move_to_end(key)
    while len(store) > _MAX_ENTRIES_PER_SERVICE:
        store.popitem(last=False)


def get_cached_value(service: str, key: str) -> dict | None:
    store = _cache.get(service)
    if not store:
        return None
    value = store.get(key)
    if value is None:
        return None
    store.move_to_end(key)
    return deepcopy(value)


def set_cached(service: str, key: str, value: dict) -> None:
    cache_value(service, key, value)


def get_cached(service: str, key: str) -> dict | None:
    return get_cached_value(service, key)

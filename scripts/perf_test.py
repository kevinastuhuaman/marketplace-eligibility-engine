"""Simple batch evaluation benchmark runner."""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time
from typing import Any

import httpx

_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_script_dir, ".."))
sys.path.insert(0, os.path.join(_script_dir, "..", "services"))

from shared.scenario_data import SCENARIOS


async def build_payloads(client: httpx.AsyncClient, total_requests: int) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    items = await client.get("/v1/items")
    items.raise_for_status()
    sku_to_id = {item["sku"]: item["item_id"] for item in items.json()}
    variants = [
        variant
        for scenario in SCENARIOS
        for variant in scenario.get("variants", [])
    ]
    if not variants:
        return payloads
    for index in range(total_requests):
        variant = variants[index % len(variants)]
        item_id = variant.get("item_id") or sku_to_id.get(variant.get("item_sku"))
        if not item_id:
            continue
        payloads.append(
            {
                "item_id": item_id,
                "market_code": variant["market_code"],
                "customer_location": {
                    "state": variant.get("customer_location", {}).get("state", variant["state"]),
                    "zip": variant.get("customer_location", {}).get("zip", variant["zip"]),
                    "county": variant.get("customer_location", {}).get("county", variant.get("county")),
                    "latitude": variant.get("customer_location", {}).get("latitude"),
                    "longitude": variant.get("customer_location", {}).get("longitude"),
                    "address_id": variant.get("customer_location", {}).get("address_id"),
                },
                "seller_id": variant.get("seller_id"),
                "timestamp": variant.get("timestamp"),
                "context": variant.get("context") or {},
            }
        )
    return payloads


async def run_batch(client: httpx.AsyncClient, payloads: list[dict[str, Any]]) -> tuple[int, list[int], int]:
    started = time.perf_counter()
    response = await client.post("/v1/evaluate/batch", json={"requests": payloads})
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    if not response.is_success:
        return elapsed_ms, [], len(payloads)
    batch = response.json()
    result_latencies = [result.get("evaluation_ms", 0) for result in batch.get("results", [])]
    return elapsed_ms, result_latencies, int(batch.get("failed", 0))


async def run_benchmark(base_url: str, total_requests: int, concurrency: int) -> dict[str, Any]:
    latencies: list[int] = []
    errors = 0
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        payloads = await build_payloads(client, total_requests)
        if not payloads:
            return {"count": 0, "p50": 0, "p95": 0, "p99": 0, "errors": 0}
        batches = [payloads[index:index + 100] for index in range(0, len(payloads), 100)]

        async def worker(batch_payloads: list[dict[str, Any]]) -> None:
            nonlocal errors
            async with semaphore:
                _elapsed_ms, result_latencies, batch_errors = await run_batch(client, batch_payloads)
                latencies.extend(result_latencies)
                errors += batch_errors

        await asyncio.gather(*(worker(batch) for batch in batches))

    if not latencies:
        return {"count": 0, "p50": 0, "p95": 0, "p99": 0, "errors": errors}

    sorted_latencies = sorted(latencies)
    return {
        "count": len(sorted_latencies),
        "p50": statistics.median(sorted_latencies),
        "p95": sorted_latencies[min(len(sorted_latencies) - 1, int(len(sorted_latencies) * 0.95))],
        "p99": sorted_latencies[min(len(sorted_latencies) - 1, int(len(sorted_latencies) * 0.99))],
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--base-url", type=str, default="http://localhost/api")
    args = parser.parse_args()

    results = asyncio.run(run_benchmark(args.base_url, args.requests, args.concurrency))
    print(
        f"count={results['count']} p50={results['p50']}ms "
        f"p95={results['p95']}ms p99={results['p99']}ms errors={results['errors']}"
    )


if __name__ == "__main__":
    main()

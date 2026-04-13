from __future__ import annotations

import statistics
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eligibility_service import evaluate


async def evaluate_batch(requests: list[dict], db: AsyncSession) -> dict:
    started_at = time.perf_counter()
    results = []
    latencies = []
    for request in requests:
        result = await evaluate(request, db)
        results.append(result)
        latencies.append(result.get("evaluation_ms", 0))

    sorted_latencies = sorted(latencies) or [0]
    total_ms = int((time.perf_counter() - started_at) * 1000)
    return {
        "results": results,
        "total_requests": len(results),
        "succeeded": sum(1 for result in results if not result.get("errors")),
        "failed": sum(1 for result in results if result.get("errors")),
        "total_ms": total_ms,
        "p50_ms": float(statistics.median(sorted_latencies)),
        "p95_ms": float(sorted_latencies[min(len(sorted_latencies) - 1, max(0, int(len(sorted_latencies) * 0.95) - 1))]),
        "p99_ms": float(sorted_latencies[min(len(sorted_latencies) - 1, max(0, int(len(sorted_latencies) * 0.99) - 1))]),
    }

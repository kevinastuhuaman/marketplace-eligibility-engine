from contextlib import asynccontextmanager
import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config import settings
from app.api.routes import router
from shared.redis_streams import StreamConsumer, StreamPublisher

logger = logging.getLogger(__name__)


async def handle_event(event_type: str, data: dict):
    try:
        logger.info(f"[eligibility-consumer] {event_type}: {data}")
    except Exception:
        logger.exception("Error handling stream event %s", event_type)


async def _run_consumer(consumer: StreamConsumer, name: str):
    """Wrapper that logs exceptions from background consumer tasks."""
    try:
        await consumer.consume(handle_event)
    except asyncio.CancelledError:
        logger.info("Consumer %s cancelled", name)
    except Exception:
        logger.exception("Consumer %s crashed", name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (with retry for DB readiness)
    from app.db import engine, Base
    from app.models import compliance, fulfillment, audit  # noqa: F401
    for attempt in range(1, 4):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception:
            if attempt == 3:
                raise
            logger.warning("DB not ready, retrying in 2s (attempt %d/3)", attempt)
            await asyncio.sleep(2)

    # Connect to Redis (no decode_responses — StreamConsumer expects bytes)
    app.state.redis = aioredis.from_url(settings.redis_url)

    # Start background consumers for inventory and seller events
    inv_consumer = StreamConsumer(
        app.state.redis, "inventory:state_changes",
        "eligibility-cg", "eligibility-1"
    )
    seller_consumer = StreamConsumer(
        app.state.redis, "seller:state_changes",
        "eligibility-cg", "eligibility-1"
    )

    app.state.stream_publisher = StreamPublisher(
        app.state.redis, "eligibility:evaluations"
    )

    inv_task = asyncio.create_task(_run_consumer(inv_consumer, "inventory"))
    seller_task = asyncio.create_task(_run_consumer(seller_consumer, "seller"))

    yield

    # Cleanup: stop consumers, cancel tasks, and await them
    inv_consumer.stop()
    seller_consumer.stop()
    inv_task.cancel()
    seller_task.cancel()
    await asyncio.gather(inv_task, seller_task, return_exceptions=True)
    await app.state.redis.aclose()


app = FastAPI(title="Eligibility Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

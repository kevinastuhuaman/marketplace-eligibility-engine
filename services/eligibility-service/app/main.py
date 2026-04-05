from contextlib import asynccontextmanager
import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config import settings
from app.api.routes import router
from shared.redis_streams import StreamConsumer

logger = logging.getLogger(__name__)


async def handle_event(event_type: str, data: dict):
    logger.info(f"[eligibility-consumer] {event_type}: {data}")


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    inv_task = asyncio.create_task(inv_consumer.consume(handle_event))
    seller_task = asyncio.create_task(seller_consumer.consume(handle_event))

    yield

    # Cleanup
    inv_consumer.stop()
    seller_consumer.stop()
    inv_task.cancel()
    seller_task.cancel()
    await app.state.redis.aclose()


app = FastAPI(title="Eligibility Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

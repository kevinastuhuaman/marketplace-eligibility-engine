import asyncio
import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config import settings
from app.api.routes import router
from shared.redis_streams import StreamPublisher

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (with retry for DB readiness)
    from app.db import engine, Base
    from app.models import inventory, events  # noqa: F401
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

    # Connect to Redis
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.stream_publisher = StreamPublisher(
        app.state.redis, "inventory:state_changes"
    )
    yield
    # Cleanup
    await app.state.redis.aclose()


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

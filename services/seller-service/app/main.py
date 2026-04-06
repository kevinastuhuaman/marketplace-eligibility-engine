from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config import settings
from app.api.routes import router
from shared.redis_streams import StreamPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    from app.db import engine, Base
    from app.models import sellers, offers  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Connect to Redis
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.stream_publisher = StreamPublisher(
        app.state.redis, "seller:state_changes"
    )
    yield
    # Cleanup
    await app.state.redis.aclose()


app = FastAPI(title="Seller Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import router
from app.config import settings
from app.db import engine, Base
from app.models import items  # noqa: F401 — register models

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (with retry for DB readiness)
    for attempt in range(1, 4):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Migration: add column if missing (idempotent)
                await conn.execute(text(
                    "ALTER TABLE item_svc.items "
                    "ADD COLUMN IF NOT EXISTS display_metadata JSONB"
                ))
                # Backfill NULL rows from shared catalog data
                from sqlalchemy import bindparam
                from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
                from shared.catalog_data import DISPLAY_METADATA
                stmt = text(
                    "UPDATE item_svc.items SET display_metadata = :meta "
                    "WHERE sku = :sku AND display_metadata IS NULL"
                ).bindparams(bindparam("meta", type_=PG_JSONB))
                for sku, meta in DISPLAY_METADATA.items():
                    await conn.execute(stmt, {"sku": sku, "meta": meta})
            break
        except Exception:
            if attempt == 3:
                raise
            logger.warning("DB not ready, retrying in 2s (attempt %d/3)", attempt)
            await asyncio.sleep(2)
    yield


app = FastAPI(title="Item Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

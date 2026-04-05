from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Start Redis stream consumers
    yield


app = FastAPI(title="Eligibility Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

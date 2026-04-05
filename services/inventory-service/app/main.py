from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Start Redis stream producer/consumer here
    yield


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

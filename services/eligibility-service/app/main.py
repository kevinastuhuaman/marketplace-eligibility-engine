from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Start Redis stream consumers here
    yield
    # TODO: Stop consumers here


app = FastAPI(title="Eligibility Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

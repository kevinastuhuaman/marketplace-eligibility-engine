from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Item Service", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

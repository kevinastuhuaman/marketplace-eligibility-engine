from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

app = FastAPI(title="Item Service", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.app_name}

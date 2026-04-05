from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/transactability"
    redis_url: str = "redis://localhost:6379"
    item_service_url: str = "http://localhost:8001"
    inventory_service_url: str = "http://localhost:8003"
    seller_service_url: str = "http://localhost:8004"
    app_name: str = "eligibility-service"
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

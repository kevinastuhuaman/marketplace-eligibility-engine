from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/transactability"
    redis_url: str = "redis://localhost:6379"
    app_name: str = "seller-service"
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

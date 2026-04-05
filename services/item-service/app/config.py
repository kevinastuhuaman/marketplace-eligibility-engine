from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/transactability"
    app_name: str = "item-service"
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

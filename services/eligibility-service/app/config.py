from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/transactability"
    redis_url: str = "redis://localhost:6379"
    item_service_url: str = "http://localhost:8001"
    inventory_service_url: str = "http://localhost:8003"
    seller_service_url: str = "http://localhost:8004"
    app_name: str = "eligibility-service"
    debug: bool = False
    enable_diagnosis: bool = True
    enable_geo_restrictions: bool = True
    enable_low_confidence: bool = True
    enable_circuit_breakers: bool = True
    enable_batch_evaluation: bool = True
    rule_cache_ttl_seconds: int = 60
    low_confidence_threshold: float = 0.65
    circuit_breaker_failure_threshold: int = 2
    circuit_breaker_recovery_seconds: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()

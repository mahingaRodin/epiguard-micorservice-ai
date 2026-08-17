from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    http_port: int = 8000
    grpc_port: int = 50051
    log_level: str = "INFO"

    model_path: Path = Path("app/model/epiguard-ai.pkl")
    model_type: str = "logistic_regression"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "epiguard"
    postgres_user: str = "epiguard"
    postgres_password: str = "epiguard_dev"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_dev"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

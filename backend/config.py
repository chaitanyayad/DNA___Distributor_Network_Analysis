from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Database — uses postgresql+asyncpg:// for FastAPI async driver
    database_url: str = Field(..., alias="DATABASE_URL")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_minutes: int = Field(default=480, alias="JWT_EXPIRY_MINUTES")

    # Mapbox (used by frontend but stored here for reference)
    mapbox_token: str = Field(default="", alias="MAPBOX_TOKEN")

    model_config = {
        "env_file": "backend/.env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings loader — reads .env once, reuses on every call.
    Use as a FastAPI dependency: settings: Settings = Depends(get_settings)
    Or import directly: from backend.config import get_settings
    """
    return Settings()
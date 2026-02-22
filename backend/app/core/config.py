from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://logist:logist_secret@127.0.0.1:5432/logist_zp"
    SECRET_KEY: str = "dev-secret-key"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 300
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALGORITHM: str = "HS256"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",")]




settings = Settings()

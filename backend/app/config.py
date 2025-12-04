from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 파일에서 환경변수 로드
# override=True: 기존 시스템 환경변수가 있어도 .env 값을 우선 사용
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/global_capflow",
        alias="DATABASE_URL",
        description="SQLAlchemy database URL",
    )
    
    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="OpenAI API key for GPT-4o",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance to avoid re-reading env files."""
    return Settings()


settings = get_settings()

# 디버깅: 로드된 OpenAI Key 확인 (앞/뒤 일부만 노출)
key = settings.openai_api_key
masked_key = (
    key[:5] + "..." + key[-5:]
    if key and len(key) > 10
    else ("(empty)" if key == "" else "None")
)
print(f"\n🔍 [Config] Loaded OpenAI Key: {masked_key} (Length: {len(key) if key is not None else 0})")


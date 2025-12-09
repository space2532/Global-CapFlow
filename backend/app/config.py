from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 프로젝트 루트 경로 찾기 (backend/app/config.py -> 프로젝트 루트)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# .env 파일에서 환경변수 로드
# override=True: 기존 시스템 환경변수가 있어도 .env 값을 우선 사용
load_dotenv(dotenv_path=ENV_FILE, override=True)


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
    
    fmp_api_key: str = Field(
        default="",
        alias="FMP_API_KEY",
        description="Financial Modeling Prep API key for company logos",
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
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

# 디버깅: 로드된 FMP API Key 확인
fmp_key = settings.fmp_api_key
masked_fmp_key = (
    fmp_key[:5] + "..." + fmp_key[-5:]
    if fmp_key and len(fmp_key) > 10
    else ("(empty)" if fmp_key == "" else "None")
)
print(f"🔍 [Config] Loaded FMP API Key: {masked_fmp_key} (Length: {len(fmp_key) if fmp_key is not None else 0})")

# backend/app/config.py 맨 아래에 추가
db_url = settings.database_url
masked_db_url = db_url.split("@")[-1] if "@" in db_url else "Unknown"
print(f"📡 [Config] Current Database Host: {masked_db_url}")
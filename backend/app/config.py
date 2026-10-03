import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "QueryGuard AI"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://postgres:postgres@localhost:5432/queryguard"
    )
    WORKLOAD_DATABASE_URL: str = os.getenv(
        "WORKLOAD_DATABASE_URL",
        "postgresql+psycopg2://workload_ro:workload_ro_pass@localhost:5433/workload_db"
    )
    WORKLOAD_ADMIN_DATABASE_URL: str = os.getenv(
        "WORKLOAD_ADMIN_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/workload_db"
    )
    TPCH_BASE_DIR: str = os.getenv("TPCH_BASE_DIR", "")
    HMAC_TOKEN_SECRET: str = os.getenv(
        "HMAC_TOKEN_SECRET",
        "qg-default-local-hmac-secret-salt-2026"
    )
    SQLITE_FALLBACK: str = "sqlite:///./queryguard.db"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    MOCK_DBA_USER_ID: str = "DBA_ADMIN_01"
    MOCK_DBA_USER_NAME: str = "Lead Database Architect"

    # Local Ollama / SLM Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
    OLLAMA_ENABLED: bool = os.getenv("OLLAMA_ENABLED", "true").lower() in ("true", "1", "yes")
    OLLAMA_TIMEOUT_SECONDS: int = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
    REWRITE_IMPROVEMENT_THRESHOLD_PCT: float = float(os.getenv("REWRITE_IMPROVEMENT_THRESHOLD_PCT", "10.0"))
    REWRITE_CACHE_TTL_SECONDS: int = int(os.getenv("REWRITE_CACHE_TTL_SECONDS", "300"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

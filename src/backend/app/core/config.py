from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, FieldValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the path to the project root (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), case_sensitive=True)

    # Project
    PROJECT_NAME: str = "TestOps Copilot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: FieldValidationInfo) -> Optional[str]:
        if isinstance(v, str):
            return v

        data = info.data or {}
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        host = data.get("POSTGRES_SERVER")
        db = data.get("POSTGRES_DB")

        if not all([user, password, host, db]):
            return None

        return f"postgresql+asyncpg://{user}:{password}@{host}/{db}"

    # Cloud.ru API
    CLOUD_API_KEY: str
    CLOUD_API_URL: str = "https://foundation-models.api.cloud.ru/v1"
    CLOUD_MODEL: str = "Qwen/Qwen3-Coder-480B-A35B-Instruct"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # GitLab
    GITLAB_URL: str
    GITLAB_TOKEN: str

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str], None]
    ) -> Union[List[str], str]:
        if v is None:
            return []
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_HOUR: int = 100

    # AI Settings
    MAX_TOKENS_GENERATION: int = 4000
    TEMPERATURE_GENERATION: float = 0.3
    TOP_P_GENERATION: float = 0.95

    # Vector DB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"

    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".py", ".txt", ".yaml", ".yml", ".json"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9091


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
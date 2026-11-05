import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve potential .env paths (root ExamForge/.env, backend/.env, or cwd/.env)
_current_dir = Path(__file__).resolve().parent
_backend_dir = _current_dir.parent.parent
_root_dir = _backend_dir.parent

_env_candidates = [
    _root_dir / ".env",
    _backend_dir / ".env",
    Path.cwd() / ".env",
]
_env_file = next((str(p) for p in _env_candidates if p.is_file()), ".env")


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/examforge"

    # JWT Security
    JWT_SECRET_KEY: str = "change-this-secret-key-before-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Provider Configuration (Strict Live Inference)
    AI_PROVIDER_MODE: str = "live"

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_ID: str = ""

    # IBM watsonx.ai / Granite
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    GRANITE_MODEL_ID: str = "ibm/granite-13b-instruct-v2"

    # File Upload & Vector Storage
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "storage/uploads"
    CHROMA_DIR: str = "storage/chroma"

    class Config:
        env_file = _env_file
        extra = "ignore"


settings = Settings()

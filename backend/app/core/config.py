from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/examforge"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Provider
    AI_PROVIDER_MODE: str = "mock"  # "mock" or "live"

    # Gemini
    GEMINI_API_KEY: str = ""

    # Watsonx / Granite
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    GRANITE_MODEL_ID: str = "ibm/granite-13b-instruct-v2"

    # File upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "storage/uploads"
    CHROMA_DIR: str = "storage/chroma"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    environment: str = "development"
    port: int = 8000
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_gateway"
    )

    # LLM Provider Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None

    # This tells Pydantic to read from the .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Create a global settings object to import across the app
settings = Settings()

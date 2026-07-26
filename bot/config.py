from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str

    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/bot.db"

    LOG_LEVEL: str = "INFO"

    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM: int = 384

    N_CLUSTERS: int = 10
    MIN_USERS_FOR_CLUSTERING: int = 20


settings = Settings()

from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    GEMINI_API_KEY: str
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

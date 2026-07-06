from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "commonvoice"
    admin_ids: list[int] = []
    log_level: str = "INFO"


settings = Settings()
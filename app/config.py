from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./todo.db"
    bedrock_model_id: str | None = None
    aws_region: str | None = None


settings = Settings()

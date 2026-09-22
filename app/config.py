from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    bedrock_model_id/aws_region are optional here since nothing outside the
    AI routes needs them - BedrockLLMClient (app/ai/tool_calling.py) is
    where a missing value actually raises, right before it would matter.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./todo.db"
    bedrock_model_id: str | None = None
    aws_region: str | None = None


settings = Settings()

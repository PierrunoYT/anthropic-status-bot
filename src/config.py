from typing import List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from enum import Enum

class LogLevel(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

class StatusConfig(BaseModel):
    url: str = "https://status.anthropic.com"
    timeout: int = 10000
    retries: int = 3
    components: List[str] = [
        "console.anthropic.com",
        "api.anthropic.com",
        "api.anthropic.com - Beta Features",
        "anthropic.com",
        "claude.ai",
        "Claude on Vertex AI",
        "Claude on AWS Bedrock"
    ]
    user_agent: str = "AnthropicStatusBot/1.0"

class DiscordConfig(BaseModel):
    token: str
    channel_id: str
    check_interval: int = Field(default=5, ge=1)

class LoggingConfig(BaseModel):
    level: LogLevel = LogLevel.INFO

class Settings(BaseSettings):
    discord: DiscordConfig
    status: StatusConfig = StatusConfig()
    logging: LoggingConfig = LoggingConfig()

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'extra': 'ignore',
        'env_nested_delimiter': '__'
    }

    @classmethod
    def from_env(cls) -> "Settings":
        from os import environ
        from dotenv import load_dotenv
        load_dotenv()

        # Map environment variables to nested structure
        return cls(
            discord=DiscordConfig(
                token=environ.get("DISCORD_TOKEN", ""),
                channel_id=environ.get("DISCORD_CHANNEL_ID", ""),
                check_interval=int(environ.get("CHECK_INTERVAL", "5"))
            ),
            status=StatusConfig(),
            logging=LoggingConfig(
                level=LogLevel(environ.get("LOG_LEVEL", "info").lower())
            )
        )

# Create a global config instance
config = Settings.from_env()
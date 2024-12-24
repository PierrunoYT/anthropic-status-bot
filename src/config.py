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
        "anthropic.com"
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

    class Config:
        env_file = ".env"
        env_prefix = ""
        env_nested_delimiter = "__"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            discord=DiscordConfig(
                token=cls._get_env_var("DISCORD_TOKEN"),
                channel_id=cls._get_env_var("DISCORD_CHANNEL_ID"),
                check_interval=cls._get_env_var("CHECK_INTERVAL", "5")
            )
        )

    @staticmethod
    def _get_env_var(key: str, default: str = None) -> str:
        from os import environ
        from dotenv import load_dotenv
        load_dotenv()
        return environ.get(key, default)

# Create a global config instance
config = Settings.from_env()
from typing import List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class StatusConfig(BaseModel):
    url: str = "https://status.anthropic.com"
    timeout: int = 10
    retries: int = 3
    components: List[str] = [
        "console.anthropic.com",
        "api.anthropic.com",
        "api.anthropic.com - Beta Features",
        "anthropic.com"
    ]
    user_agent: str = "StatusChecker/1.0"

class DiscordConfig(BaseModel):
    token: str
    channel_id: str
    check_interval: int

class LoggingConfig(BaseModel):
    level: str = Field(
        default="info",
        pattern="^(none|debug|info|warn|error)$"
    )

class Settings(BaseSettings):
    DISCORD_TOKEN: str
    DISCORD_CHANNEL_ID: str
    CHECK_INTERVAL: int = 5
    LOG_LEVEL: str = "info"

    class Config:
        env_file = ".env"
        case_sensitive = True

class AppConfig(BaseModel):
    status: StatusConfig = StatusConfig()
    discord: DiscordConfig
    logging: LoggingConfig

def create_config() -> AppConfig:
    """Create and validate application configuration."""
    try:
        settings = Settings()
        
        return AppConfig(
            status=StatusConfig(),
            discord=DiscordConfig(
                token=settings.DISCORD_TOKEN,
                channel_id=settings.DISCORD_CHANNEL_ID,
                check_interval=settings.CHECK_INTERVAL
            ),
            logging=LoggingConfig(
                level=settings.LOG_LEVEL
            )
        )
    except Exception as e:
        print(f"Configuration validation failed: {str(e)}")
        raise

# Create singleton config instance
config = create_config()
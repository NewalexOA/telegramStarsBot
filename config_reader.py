from enum import StrEnum
from typing import Any, Optional
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog

logger = structlog.get_logger()

class LogRenderer(StrEnum):
    JSON = "json"
    CONSOLE = "console"

class BotConfig(BaseSettings):
    """Bot configuration"""
    token: SecretStr
    owners: list[int]
    required_channel_id: int
    required_channel_invite: str
    provider_token: str = ""

    @field_validator("owners", mode="before")
    @classmethod
    def parse_owners(cls, v: Any) -> list[int]:
        if isinstance(v, str):
            try:
                v = v.strip('[]').replace(' ', '')
                return [int(x) for x in v.split(',') if x]
            except ValueError as e:
                logger.error("Failed to parse owners: Invalid format", error=str(e), value=v)
                raise ValueError(f"Invalid owners format: {v}")
        elif not isinstance(v, list):
            raise TypeError(f"Expected a list or a string, got {type(v).__name__}")
        return v

    model_config = SettingsConfigDict(
        env_prefix="BOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class LogConfig(BaseSettings):
    """Log configuration"""
    show_datetime: bool
    datetime_format: str
    show_debug_logs: bool
    time_in_utc: bool
    renderer: LogRenderer
    use_colors_in_console: bool

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_config(config_type: type[BaseSettings], root_key: Optional[str] = None) -> Any:
    """Get configuration instance"""
    try:
        # Пробуем загрузить из .env
        return config_type()
    except Exception as e:
        logger.warning("Failed to load config from .env", error=str(e))
        
        # Если не получилось, читаем из TOML
        import tomli
        config_path = "config.toml"
        
        with open(config_path, "rb") as f:
            config_dict = tomli.load(f)
            
        if root_key is not None:
            config_dict = config_dict[root_key]
            
        return config_type(**config_dict)

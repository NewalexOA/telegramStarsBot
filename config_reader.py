from enum import StrEnum
from pathlib import Path
from typing import Any, Type, Union
from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog
import tomli
from dotenv import load_dotenv, set_key

logger = structlog.get_logger()

class LogRenderer(StrEnum):
    """Log renderer type"""
    JSON = "json"
    CONSOLE = "console"

class BotConfig(BaseSettings):
    """Bot configuration"""
    token: SecretStr
    owners: list[int]
    required_channel_id: int
    required_channel_invite: str
    provider_token: str = ""
    openai_api_key: SecretStr
    assistant_id: str

    @field_validator("owners", mode="before")
    @classmethod
    def parse_owners(cls, v):
        if isinstance(v, str):
            try:
                v = v.strip('[]').replace(' ', '')
                return [int(x) for x in v.split(',') if x]
            except Exception as e:
                logger.error("Failed to parse owners", error=str(e), value=v)
                raise ValueError(f"Invalid owners format: {v}")
        return v

    model_config = SettingsConfigDict(
        env_prefix="BOT_",
        env_file=".env",
        env_file_encoding="utf-8"
    )

class LogConfig(BaseModel):
    """Log configuration"""
    show_datetime: bool
    datetime_format: str
    show_debug_logs: bool
    time_in_utc: bool
    renderer: LogRenderer
    use_colors_in_console: bool

def get_config(config_type: Type[Union[BotConfig, LogConfig]], root_key: str | None = None) -> Any:
    """Get configuration instance"""
    # Для BotConfig используем .env
    if config_type == BotConfig:
        return BotConfig()
        
    # Для LogConfig используем config.toml
    if config_type == LogConfig:
        try:
            config_path = Path(__file__).parent / "config.toml"
            if not config_path.exists():
                raise FileNotFoundError("config.toml not found")
                
            with open(config_path, "rb") as f:
                raw_config = tomli.load(f)
                
            if root_key not in raw_config:
                raise KeyError(f"Section {root_key} not found in config.toml")
                
            return LogConfig.model_validate(raw_config[root_key])
            
        except Exception as e:
            logger.error("Failed to load log config from TOML", error=str(e))
            raise
            
    raise ValueError(f"Unsupported config type: {config_type}")

bot_config = get_config(BotConfig, "bot")

def update_assistant_id(assistant_id: str) -> None:
    """Обновляет assistant_id в конфиге"""
    global bot_config
    bot_config.assistant_id = assistant_id
    logger.info(f"Assistant ID updated in config: {assistant_id}")

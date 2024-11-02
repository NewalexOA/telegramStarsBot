from enum import StrEnum, auto
from functools import lru_cache
from os import environ
from tomllib import load
from typing import Type, TypeVar
import structlog

from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()

ConfigType = TypeVar("ConfigType", bound=BaseModel)


class LogRenderer(StrEnum):
    JSON = auto()
    CONSOLE = auto()


class BotConfig(BaseSettings):
    token: SecretStr
    owners: list[int]
    required_channel_id: int
    required_channel_invite: str
    provider_token: SecretStr = SecretStr("")

    @field_validator("owners", mode="before")
    @classmethod
    def parse_owners(cls, v):
        if isinstance(v, str):
            try:
                # Убираем квадратные скобки и пробелы
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


class LogConfig(BaseSettings):
    show_datetime: bool
    datetime_format: str
    show_debug_logs: bool
    time_in_utc: bool
    use_colors_in_console: bool
    renderer: LogRenderer

    @field_validator('renderer', mode="before")
    @classmethod
    def log_renderer_to_lower(cls, v: str):
        return v.lower()

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8"
    )


def get_config(config_type: Type[ConfigType], root_key: str | None = None) -> ConfigType:
    """
    Get configuration from .env or fallback to TOML
    """
    try:
        # Пробуем загрузить из .env
        return config_type()  # type: ignore
    except Exception as e:
        logger.warning("Failed to load config from .env", error=str(e))
        
        # Если не получилось, читаем из TOML
        config_dict = parse_config_file()
        if root_key not in config_dict:
            raise ValueError(f"Key {root_key} not found in config")
            
        return config_type.model_validate(config_dict[root_key])  # type: ignore


@lru_cache
def parse_config_file() -> dict:
    """Parse TOML config file"""
    file_path = environ.get('CONFIG_FILE_PATH', "config.toml")
    
    try:
        with open(file_path, "rb") as file:
            return load(file)
    except Exception as e:
        logger.error("Failed to parse config file", error=str(e), path=file_path)
        raise

from functools import lru_cache
from enum import StrEnum
from pathlib import Path
from typing import Any, Type, Union
from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog
import tomli

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

@lru_cache()
def get_config(config_type: Type[Union[BotConfig, LogConfig]], root_key: str | None = None) -> Any:
    """Get configuration instance"""
    logger.info(f"Loading configuration for {config_type.__name__}")
    
    # Для BotConfig используем комбинацию config.toml и .env
    if config_type == BotConfig:
        try:
            # Сначала пытаемся загрузить config.toml
            config_path = Path(__file__).parent / "config.toml"
            toml_config = {}
            
            if config_path.exists():
                with open(config_path, "rb") as f:
                    raw_config = tomli.load(f)
                    if "bot" in raw_config:
                        toml_config = raw_config["bot"]
                        logger.info("Loaded bot config from TOML")
            
            # Создаем конфигурацию из .env
            env_config = BotConfig()
            
            # Для каждого поля проверяем наличие значения в TOML
            for field_name in BotConfig.model_fields.keys():
                toml_value = toml_config.get(field_name)
                env_value = getattr(env_config, field_name)
                
                if toml_value:  # Если есть значение в TOML
                    setattr(env_config, field_name, toml_value)
                    logger.info(f"{field_name}: using value from TOML")
                elif env_value:  # Если нет в TOML, но есть в .env
                    logger.info(f"{field_name}: using value from .env")
                else:
                    logger.warning(f"{field_name}: no value found in TOML or .env")
            
            return env_config
            
        except Exception as e:
            logger.error("Failed to load bot config", error=str(e))
            raise
    
    # Для LogConfig используем только config.toml
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

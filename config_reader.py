from typing import Optional, List
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import tomli
import os
from pathlib import Path
import ast
import structlog

logger = structlog.get_logger()

class BotConfig(BaseSettings):
    """Конфигурация бота"""
    token: SecretStr = SecretStr("")
    owners: List[int] = []
    required_channel_id: Optional[int] = None
    required_channel_url: Optional[str] = None
    openai_api_key: SecretStr = SecretStr("")
    assistant_id: str = ""
    provider_token: SecretStr = SecretStr("")
    
    @field_validator('owners', mode='before')
    @classmethod
    def parse_owners(cls, v):
        """Парсинг списка владельцев из строки"""
        if isinstance(v, str):
            try:
                # Безопасный парсинг строки списка
                parsed = ast.literal_eval(v)
                logger.debug(f"Parsed owners from {v} to {parsed}")
                return parsed
            except (ValueError, SyntaxError) as e:
                logger.error(f"Error parsing owners: {e}")
                return []
        return v
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow',
        env_mapping = {
            'token': 'BOT_TOKEN',
            'owners': 'BOT_OWNERS',
            'required_channel_id': 'BOT_REQUIRED_CHANNEL_ID',
            'required_channel_url': 'BOT_REQUIRED_CHANNEL_URL',
            'openai_api_key': 'BOT_OPENAI_API_KEY',
            'assistant_id': 'BOT_ASSISTANT_ID'
        }
    )

def load_toml_config() -> dict:
    """Загрузка конфигурации из config.toml"""
    config_path = Path('config.toml')
    if config_path.exists():
        with open(config_path, 'rb') as f:
            return tomli.load(f)
    return {}

def get_config(config_class: type[BaseSettings], section: str = None) -> BaseSettings:
    """
    Получение конфигурации с приоритетом config.toml над .env
    """
    # Загружаем config.toml
    toml_config = load_toml_config()
    logger.debug(f"Loaded TOML config: {toml_config}")
    
    # Получаем значения из нужной секции
    section_config = toml_config.get(section, {}) if section else toml_config
    
    # Маппинг имен переменных окружения
    env_mapping = config_class.model_config.get('env_mapping', {})
    
    # Создаем словарь с переменными окружения, используя маппинг
    env_values = {}
    for class_field, env_field in env_mapping.items():
        env_value = os.getenv(env_field.upper())
        if env_value is not None:
            env_values[class_field] = env_value
    
    logger.debug(f"Loaded ENV values: {env_values}")
    
    # Приоритет config.toml над .env
    combined_config = {**env_values, **section_config}
    logger.debug(f"Combined config: {combined_config}")
    
    config = config_class(**combined_config)
    logger.debug(f"Final config values: owners={config.owners}")
    return config

import logging
from json import dumps

import structlog
from structlog import WriteLoggerFactory

from config_reader import LogConfig, LogRenderer, get_config


def init_logging():
    """Initialize logging configuration"""
    # Получаем конфигурацию логирования
    log_config = get_config(LogConfig, "logs")
    
    # Устанавливаем базовый уровень логирования
    log_level = logging.DEBUG if log_config.show_debug_logs else logging.INFO
    
    # Настраиваем корневой логгер
    logging.basicConfig(level=log_level)
    
    # Настраиваем уровни логирования для библиотек
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)  # Только важные SQL сообщения
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)         # Только важные SQLite сообщения
    logging.getLogger('aiogram').setLevel(logging.INFO)             # Основные события бота
    
    # Настраиваем structlog
    structlog.configure(**get_structlog_config(log_config))

def get_structlog_config(
    log_config: LogConfig
) -> dict:
    """
    Get config for structlog
    :param log_config: объект LogConfig with log parameters
    :return: dict with structlog config
    """
    # Show debug level logs?
    min_level = logging.DEBUG if log_config.show_debug_logs else logging.INFO

    return {
        "processors": get_processors(log_config),
        "cache_logger_on_first_use": True,
        "wrapper_class": structlog.make_filtering_bound_logger(min_level),
        "logger_factory": WriteLoggerFactory()
    }

def get_processors(log_config: LogConfig) -> list:
    """
    Returns processors list for structlog
    :param log_config: LogConfig object with log parameters
    :return: processors list for structlog
    """
    def custom_json_serializer(data, *args, **kwargs):
        """
        JSON-objects custom serializer
        """
        result = dict()


        if log_config.show_datetime is True:
            result["timestamp"] = data.pop("timestamp")

        # Other two keys goes in this order
        for key in ("level", "event"):
            if key in data:
                result[key] = data.pop(key)

        # Remaining keys will be printed "as is"
        # (usually in alphabet order)
        result.update(**data)
        return dumps(result, default=str)

    processors = list()

    # In some cases there is no need to print a timestamp,
    # because it is already added by an upstream service, such as systemd
    if log_config.show_datetime is True:
        processors.append(structlog.processors.TimeStamper(
            fmt=log_config.datetime_format,
            utc=log_config.time_in_utc
            )
        )

    # Always add a log level
    processors.append(structlog.processors.add_log_level)

    # Render selection: JSON or for output to terminal
    if log_config.renderer == LogRenderer.JSON:
        processors.append(structlog.processors.JSONRenderer(serializer=custom_json_serializer))
    else:
        processors.append(structlog.dev.ConsoleRenderer(
            # You can turn off colors in the logs
            colors=log_config.use_colors_in_console,
            # You can remove padding in levels, i.e. instead of
            # [info   ] Some info log
            # [warning] Some warning log
            # will be
            # [info] Some info log
            # [warning] Some warning log
            pad_level=True
        ))
    return processors

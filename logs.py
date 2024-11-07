import logging
from json import dumps
import structlog
from structlog.stdlib import LoggerFactory, BoundLogger
from config_reader import LogConfig, LogRenderer, get_config

def init_logging():
    """Initialize logging configuration"""
    # Получаем конфигурацию логирования
    log_config = get_config(LogConfig, "logs")
    
    # Устанавливаем базовый уровень логирования
    log_level = logging.DEBUG if log_config.show_debug_logs else logging.INFO
    
    # Настраиваем корневой логгер
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt=log_config.datetime_format
    )
    
    # Настраиваем уровни логирования для библиотек
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('aiosqlite').setLevel(logging.INFO)
    
    # Остальные логгеры оставляем на уровне из конфига
    for logger_name in [
        'filters',
        'handlers',
        'middlewares',
        'services',
        'utils',
        'aiogram'
    ]:
        logging.getLogger(logger_name).setLevel(log_level)
    
    # Настраиваем structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt=log_config.datetime_format),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Создаем форматтер для structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=log_config.use_colors_in_console)
        if log_config.renderer == LogRenderer.CONSOLE
        else structlog.processors.JSONRenderer(serializer=lambda obj, *args, **kwargs: dumps(obj, default=str))
    )
    
    # Настраиваем handler для structlog
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Получаем корневой логгер structlog и добавляем handler
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

def get_logger() -> BoundLogger:
    """
    Returns configured structlog logger
    """
    return structlog.get_logger()

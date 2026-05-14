"""日志工具入口。"""

from src.infra.logging.color import color_for_log
from src.infra.logging.handlers import QueueLogHandler, SocketIOHandler
from src.infra.logging.setup import setup_logger, log_info, log_warning, log_error

__all__ = [
    "QueueLogHandler",
    "SocketIOHandler",
    "color_for_log",
    "log_error",
    "log_info",
    "log_warning",
    "setup_logger",
]

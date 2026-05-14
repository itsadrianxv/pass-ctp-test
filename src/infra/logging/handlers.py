import logging

from src.infra.logging.color import color_for_log


def _is_flask_noise(msg: str) -> bool:
    """过滤 Werkzeug/Flask 访问日志和 socket.io 轮询噪音。"""
    return "GET /" in msg or "POST /" in msg or "HTTP/1.1" in msg or "socket.io" in msg


class SocketIOHandler(logging.Handler):
    """直接推送到 SocketIO（Web 进程使用）。"""

    def __init__(self, socketio):
        """初始化 SocketIO 处理器。"""
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        """发送日志记录。"""
        try:
            msg = self.format(record)
            if _is_flask_noise(msg):
                return
            color = color_for_log(record.levelno, msg)
            self.socketio.emit("new_log", {"message": msg, "color": color})
        except Exception:
            self.handleError(record)


class QueueLogHandler(logging.Handler):
    """通过队列转发日志（Worker 子进程使用）。原 _SocketLogHandler。"""

    def __init__(self, out_queue):
        """初始化队列处理器。"""
        super().__init__()
        self.out_queue = out_queue

    def emit(self, record):
        """写入日志转发队列。"""
        try:
            msg = self.format(record)
            if _is_flask_noise(msg):
                return
            color = color_for_log(record.levelno, msg)
            self.out_queue.put(("new_log", {"message": msg, "color": color}))
        except Exception:
            self.handleError(record)

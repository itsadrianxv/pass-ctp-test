"""Worker 到 Web 的 SocketIO 通知。"""

import logging
import queue
import threading
import time

from src.infra.logging.handlers import QueueLogHandler

try:
    import socketio as socketio_client
except Exception:
    socketio_client = None


class WorkerNotifier:
    """负责连接 Web SocketIO 并转发日志/状态。"""

    def __init__(self, controller, web_socketio_url: str):
        """初始化通知器。"""
        self.controller = controller
        self.web_socketio_url = web_socketio_url
        self.out_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.sio = None

        if socketio_client is not None:
            self.sio = socketio_client.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=1)

        root_logger = logging.getLogger()
        if not any(isinstance(h, QueueLogHandler) for h in root_logger.handlers):
            handler = QueueLogHandler(self.out_queue)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
            root_logger.addHandler(handler)

    def start(self) -> None:
        """启动后台通知线程。"""
        threading.Thread(target=self._socketio_connect_loop, daemon=True).start()
        threading.Thread(target=self._socketio_emit_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def emit(self, event: str, payload: dict) -> None:
        """发送 SocketIO 事件。"""
        try:
            if self.sio and self.sio.connected:
                self.sio.emit(event, payload)
        except Exception:
            pass

    def stop(self) -> None:
        """停止通知器。"""
        self.stop_event.set()
        try:
            if self.sio and self.sio.connected:
                self.sio.disconnect()
        except Exception:
            pass

    def _socketio_connect_loop(self) -> None:
        """维持 SocketIO 连接。"""
        if not self.sio:
            return
        while not self.stop_event.is_set():
            try:
                if self.sio.connected:
                    time.sleep(1)
                    continue
                self.sio.connect(self.web_socketio_url, transports=["polling"])
            except Exception:
                time.sleep(2)

    def _socketio_emit_loop(self) -> None:
        """转发日志队列。"""
        while not self.stop_event.is_set():
            try:
                event, payload = self.out_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self.emit(event, payload)

    def _heartbeat_loop(self) -> None:
        """定期发送 Worker 状态。"""
        while not self.stop_event.is_set():
            self.emit("worker_status", self.controller.get_status())
            time.sleep(1)

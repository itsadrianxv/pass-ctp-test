"""SocketIO 事件注册。"""


def register_events(socketio) -> None:
    """注册 Web 事件转发。"""

    @socketio.on("new_log")
    def _relay_new_log(data):
        """转发日志事件。"""
        socketio.emit("new_log", data)

    @socketio.on("worker_status")
    def _relay_worker_status(data):
        """转发 Worker 状态事件。"""
        socketio.emit("worker_status", data)

    @socketio.on("case_started")
    def _relay_case_started(data):
        """转发用例开始事件。"""
        socketio.emit("case_started", data)

    @socketio.on("case_finished")
    def _relay_case_finished(data):
        """转发用例结束事件。"""
        socketio.emit("case_finished", data)

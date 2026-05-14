"""Worker 管理 API 路由。"""

from flask import jsonify

from src.app.web.errors import rpc_error_response
from src.app.web.rpc_api import request_worker_rpc
from src.app.web.state import process_manager


def register_routes(app) -> None:
    """注册 Worker 路由。"""

    @app.route("/api/worker/status", methods=["GET"])
    def worker_status():
        """读取 Worker 状态。"""
        resp = request_worker_rpc("GET_STATUS", timeout=2.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data")})

    @app.route("/api/worker/restart", methods=["POST"])
    def worker_restart():
        """重启 Worker。"""
        process_manager.restart_worker()
        return jsonify({"status": "success", "msg": "Worker 已重启"})

    @app.route("/api/worker/kill", methods=["POST"])
    def worker_kill():
        """终止 Worker。"""
        process_manager.kill_worker()
        return jsonify({"status": "success", "msg": "Worker 已终止"})

"""风控和测试配置 API 路由。"""

from flask import jsonify, request

from src.app.web.errors import rpc_error_response
from src.app.web.rpc_api import request_worker_rpc


def _copy_keys(body: dict, keys: list[str]) -> dict:
    """按白名单复制请求字段。"""
    return {key: body.get(key) for key in keys if key in body}


def register_routes(app) -> None:
    """注册风控相关路由。"""

    @app.route("/api/risk/thresholds", methods=["GET"])
    def get_risk_thresholds():
        """读取风控阈值。"""
        resp = request_worker_rpc("GET_THRESHOLDS", timeout=2.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data") or {}})

    @app.route("/api/risk/thresholds", methods=["POST"])
    def set_risk_thresholds():
        """设置风控阈值。"""
        body = request.get_json(silent=True) or {}
        payload = _copy_keys(body, ["max_order_count", "max_cancel_count", "max_repeat_count"])
        resp = request_worker_rpc("SET_THRESHOLDS", payload, timeout=3.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data") or {}})

    @app.route("/api/test/config", methods=["GET"])
    def get_test_config():
        """读取测试配置。"""
        resp = request_worker_rpc("GET_TEST_CONFIG", timeout=2.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data") or {}})

    @app.route("/api/test/config", methods=["POST"])
    def set_test_config():
        """设置测试配置。"""
        body = request.get_json(silent=True) or {}
        payload = _copy_keys(
            body,
            [
                "test_symbol",
                "safe_buy_price",
                "deal_buy_price",
                "repeat_open_threshold",
                "repeat_close_threshold",
                "volume_limit_volume",
                "order_monitor_threshold",
                "cancel_monitor_threshold",
            ],
        )
        resp = request_worker_rpc("SET_TEST_CONFIG", payload, timeout=3.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data") or {}})

    @app.route("/api/risk/snapshot", methods=["GET"])
    def get_risk_snapshot():
        """读取风控快照。"""
        resp = request_worker_rpc("GET_RISK_SNAPSHOT", timeout=2.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "data": resp.get("data") or {}})

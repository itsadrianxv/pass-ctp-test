"""Web RPC 错误处理。"""

from flask import jsonify


def rpc_error_response(resp: dict, default_msg: str = "RPC 调用失败"):
    """转换 RPC 错误为 HTTP 响应。"""
    error = str(resp.get("error", "") or "").strip()
    if error == "rpc_timeout":
        return jsonify({"status": "error", "msg": "Worker RPC 请求超时，请稍后重试"}), 503
    if error == "rpc_unavailable":
        return jsonify({"status": "error", "msg": "Worker 暂未就绪，请稍后重试"}), 503
    return jsonify({"status": "error", "msg": error or default_msg}), 500

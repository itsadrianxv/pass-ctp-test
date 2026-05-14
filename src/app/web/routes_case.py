"""测试用例 API 路由。"""

from flask import jsonify

from src.app.web.errors import rpc_error_response
from src.app.web.hard_cases import hard_disconnect_only, hard_reconnect_only, now_text
from src.app.web.rpc_api import request_worker_rpc
from src.app.web.state import log, process_manager


def register_routes(app) -> None:
    """注册测试用例路由。"""

    @app.route("/api/run/<case_id>", methods=["POST"])
    def run_case(case_id):
        """启动指定测试用例。"""
        case_id = (case_id or "").strip()

        if case_id == "2.2.1.2":
            ok, data = hard_disconnect_only(case_id)
            return jsonify(
                {
                    "status": "success" if ok else "error",
                    "msg": "强制断线完成" if ok else "强制断线失败",
                    "data": data,
                }
            ), (200 if ok else 500)

        if case_id == "2.2.1.3":
            ok, data = hard_reconnect_only(case_id)
            return jsonify(
                {
                    "status": "success" if ok else "error",
                    "msg": "强制重连完成" if ok else "强制重连失败",
                    "data": data,
                }
            ), (200 if ok else 500)

        if case_id == "2.5.1.3":
            log.info(f"【{case_id}】2.5.1.3：强制账号退出（模拟断电/进程终止） {now_text()}")
            process_manager.kill_worker()
            log.info(f"【{case_id}】Worker 已终止")
            return jsonify({"status": "success", "msg": "Worker 已强制终止", "data": {"action": "kill"}})

        resp = request_worker_rpc("RUN_CASE", {"case_id": case_id}, timeout=3.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)

        accepted = bool((resp.get("data") or {}).get("accepted"))
        return jsonify(
            {
                "status": "success" if accepted else "busy",
                "msg": "测试任务已启动" if accepted else "当前有测试正在运行，请等待结束",
            }
        )

    @app.route("/api/control/reset", methods=["POST"])
    def reset_system():
        """重置系统风控状态。"""
        resp = request_worker_rpc("RESET_RISK", timeout=3.0, autostart=True)
        if not resp.get("ok"):
            return rpc_error_response(resp)
        return jsonify({"status": "success", "msg": "系统状态已重置"})

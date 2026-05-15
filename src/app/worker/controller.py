"""Worker 调度控制器。"""

import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

import src.infra.path_setup  # noqa: F401
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy_ctptest import CtptestGateway

from src.app.worker.notifier import WorkerNotifier
from src.app.worker.rpc_handlers import handle_rpc_request as dispatch_rpc_request
from src.app.worker.status import get_risk_snapshot as build_risk_snapshot
from src.app.worker.status import get_status as build_status
from src.domain.cases.registry import CASE_MAP
from src.domain.app import TestApp
from src.infra.logging import log_error, log_info


class WorkerController:
    """管理交易引擎、测试任务和 RPC 调度。"""

    def __init__(self, web_socketio_url: str = "http://127.0.0.1:5006"):
        """初始化 Worker 控制器。"""
        self.web_socketio_url = web_socketio_url
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.main_engine.add_gateway(CtptestGateway)
        self.engine = self.main_engine.add_app(TestApp)  # 由 WorkerController 持有 MainEngine
        self.engine.connect()

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.task_lock = threading.Lock()
        self.current_case_id = None
        self.last_error = None
        self.last_case_finished_at = None
        self.stopped = False

        self.notifier = WorkerNotifier(self, web_socketio_url)
        self.notifier.start()

    def get_status(self) -> dict:
        """读取 Worker 状态。"""
        return build_status(self)

    def get_risk_snapshot(self) -> dict:
        """读取风控快照。"""
        return build_risk_snapshot(self.engine)

    def set_thresholds(self, max_order_count=None, max_cancel_count=None, max_repeat_count=None) -> dict:
        """设置风控阈值。"""
        rm = getattr(self.engine, "risk_manager", None)
        if not rm:
            raise RuntimeError("risk_manager_not_ready")
        rm.set_thresholds(max_order=max_order_count, max_cancel=max_cancel_count, max_repeat=max_repeat_count)
        return self.get_risk_snapshot()

    def reset_risk(self) -> None:
        """重置风控状态。"""
        if self.engine and self.engine.risk_manager:
            self.engine.risk_manager.active = True
            self.engine.risk_manager.reset_counters()

    def run_case(self, case_id: str) -> bool:
        """提交测试用例任务。"""
        case_id = (case_id or "").strip()
        func = CASE_MAP.get(case_id)
        if not func:
            raise ValueError(f"未找到测试项 {case_id}")

        if not self.task_lock.acquire(blocking=False):
            return False

        self.executor.submit(self._wrapped_case, case_id, func)
        return True

    def _wrapped_case(self, case_id: str, func) -> None:
        """包裹执行测试用例并发送状态事件。"""
        start = time.time()
        self.current_case_id = case_id
        self.last_error = None
        try:
            if hasattr(self.engine, "session_order_ids") and self.engine.session_order_ids is not None:
                self.engine.session_order_ids.clear()
            self.notifier.emit("case_started", {"case_id": case_id, "started_at": time.time()})
            log_info(f"=== 开始执行: {case_id} ===")
            func(self.engine)
            log_info(f"=== 执行结束: {case_id} ===")
            self.notifier.emit(
                "case_finished",
                {"case_id": case_id, "ok": True, "elapsed_s": round(time.time() - start, 3)},
            )
        except Exception as exc:
            self.last_error = str(exc)
            log_error(f"测试执行异常: {exc}")
            log_error(traceback.format_exc())
            self.notifier.emit(
                "case_finished",
                {"case_id": case_id, "ok": False, "elapsed_s": round(time.time() - start, 3), "error": str(exc)},
            )
        finally:
            self.last_case_finished_at = time.time()
            self.current_case_id = None
            self.task_lock.release()

    def handle_rpc_request(self, req: dict) -> dict:
        """处理 RPC 请求。"""
        return dispatch_rpc_request(self, req)

    def disconnect(self) -> None:
        """断开交易连接。"""
        self.engine.disconnect()

    def reconnect(self) -> None:
        """重连交易连接。"""
        if self.engine.gateway_name not in self.main_engine.gateways:
            self.main_engine.add_gateway(CtptestGateway)
        self.engine.reconnect()

    def pause(self) -> None:
        """暂停交易。"""
        self.engine.pause()

    def stop(self) -> None:
        """停止 Worker 控制器。"""
        if self.stopped:
            return
        self.stopped = True
        self.notifier.stop()
        if self.engine:
            self.engine.disconnect()
        if self.main_engine:
            self.main_engine.close()

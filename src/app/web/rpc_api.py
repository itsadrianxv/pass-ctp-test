"""Web 调用 Worker RPC 的封装。"""

from src.app.web.state import log, process_manager, rpc


def request_worker_rpc(req_type: str, payload: dict | None = None, timeout: float = 5.0, autostart: bool = False) -> dict:
    """请求 Worker RPC。"""
    if autostart:
        process_manager.start_worker()

    try:
        return rpc.request(req_type, payload or {}, timeout=timeout)
    except TimeoutError:
        log.warning("RPC request timed out: %s", req_type)
        return {"ok": False, "error": "rpc_timeout"}
    except OSError as exc:
        log.warning("RPC request failed: %s (%s)", req_type, exc)
        return {"ok": False, "error": "rpc_unavailable"}

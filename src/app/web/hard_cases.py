"""Web 侧强制断线和重连流程。"""

import os
import time

from src.app.web.state import log, process_manager, rpc


def now_text() -> str:
    """返回当前时间文本。"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def wait_ping_ok(timeout_s: float) -> bool:
    """等待 Worker Ping 成功。"""
    deadline = time.time() + max(0.1, float(timeout_s))
    while time.time() < deadline:
        try:
            resp = rpc.request("PING", {}, timeout=1.0)
            if resp.get("ok"):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def hard_disconnect_only(case_id: str) -> tuple[bool, dict]:
    """执行强制断线流程。"""
    ping_timeout_s = float(os.environ.get("HARD_DISCONNECT_PING_TIMEOUT_S", "10"))

    log.info(f"【{case_id}】>>> [2.2.1.2] 断线模拟测试")
    log.info(f"【{case_id}】策略: 强制终止 Worker 进程 (OS 级 kill)，使 CTP 前置检测到 TCP 连接断开")

    process_manager.exit_disconnect_mode()
    log.info(f"【{case_id}】步骤1: 确认 Worker 进程在线...")
    process_manager.start_worker(force=True)

    status_resp = None
    try:
        status_resp = rpc.request("GET_STATUS", {}, timeout=2.0)
    except Exception:
        status_resp = None

    if status_resp and status_resp.get("ok"):
        data = status_resp.get("data") or {}
        if data.get("busy"):
            log.warning(f"【{case_id}】Worker 正忙，无法执行断线测试")
            return False, {"reason": "busy", "status": data}

    log.info(f"【{case_id}】步骤2: Ping Worker 确认 CTP 连接正常 (超时={ping_timeout_s}s)...")
    if not wait_ping_ok(timeout_s=ping_timeout_s):
        log.error(f"【{case_id}】Ping 超时，Worker 可能未就绪")
        return False, {"reason": "ping_timeout_before_kill"}

    t1 = time.time()
    log.info(f"【{case_id}】✓ T1 连接确认: Worker 在线，CTP 会话活跃 ({now_text()})")

    process_manager.enter_disconnect_mode()
    log.info(f"【{case_id}】步骤3: 执行强制断线 — kill Worker 进程...")
    log.info(f"【{case_id}】  → 进程终止后，OS 将回收 TCP socket，CTP 前置将检测到连接断开")
    process_manager.kill_worker()
    t2 = time.time()
    elapsed_ms = int((t2 - t1) * 1000)
    log.info(f"【{case_id}】✓ T2 断线完成: Worker 进程已终止 ({now_text()})，耗时 {elapsed_ms}ms")
    log.info(f"【{case_id}】  → CTP 前置将通过心跳超时或 TCP RST 检测到会话断开")
    log.info(f"【{case_id}】  → 对端断线判定窗口取决于前置配置（通常 5~30 秒）")
    log.info(f"【{case_id}】  → 已进入断线模式，Worker 不会自动重启")
    log.info(f"【{case_id}】断线模拟完成。如需验证重连，请执行 2.2.1.3")

    return True, {"t1": t1, "t2": t2}


def hard_reconnect_only(case_id: str) -> tuple[bool, dict]:
    """执行强制重连流程。"""
    restart_ping_timeout_s = float(os.environ.get("HARD_DISCONNECT_RESTART_PING_TIMEOUT_S", "60"))

    log.info(f"【{case_id}】>>> [2.2.1.3] 重连模拟测试")
    log.info(f"【{case_id}】策略: 重启 Worker 进程，CTP 网关将自动重新连接并登录")

    process_manager.exit_disconnect_mode()
    log.info(f"【{case_id}】步骤1: 启动 Worker 进程...")
    process_manager.start_worker(force=True)

    status_resp = None
    try:
        status_resp = rpc.request("GET_STATUS", {}, timeout=2.0)
    except Exception:
        status_resp = None

    if status_resp and status_resp.get("ok"):
        data = status_resp.get("data") or {}
        if data.get("busy"):
            log.warning(f"【{case_id}】Worker 正忙，无法执行重连测试")
            return False, {"reason": "busy", "status": data}

    t3_start = time.time()
    log.info(f"【{case_id}】步骤2: 等待 Worker 完成 CTP 重连 (超时={restart_ping_timeout_s}s)...")
    log.info(f"【{case_id}】  → Worker 启动后将依次执行: 初始化网关 → 连接前置 → 授权认证 → 登录 → 查询合约")
    if not wait_ping_ok(timeout_s=restart_ping_timeout_s):
        elapsed = round(time.time() - t3_start, 1)
        log.error(f"【{case_id}】Ping 超时 ({elapsed}s)，Worker 重连可能失败")
        return False, {"reason": "ping_timeout_after_start", "t3_start": t3_start}

    t3 = time.time()
    elapsed = round(t3 - t3_start, 1)
    log.info(f"【{case_id}】✓ T3 重连成功: Worker 已上线，CTP 新会话已建立 ({now_text()})，耗时 {elapsed}s")
    log.info(f"【{case_id}】重连模拟完成。新的 CTP 会话已就绪，可继续执行后续测试")

    return True, {"t3_start": t3_start, "t3": t3}

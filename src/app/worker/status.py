"""Worker 状态快照。"""


def get_risk_snapshot(engine) -> dict:
    """读取风控快照。"""
    rm = getattr(engine, "risk_manager", None)
    if not rm:
        return {}
    thresholds = {}
    metrics = {}
    try:
        thresholds = rm.get_thresholds()
    except Exception:
        thresholds = {}
    try:
        metrics = rm.get_metrics()
    except Exception:
        metrics = {}
    return {
        "active": bool(getattr(rm, "active", True)),
        "thresholds": thresholds,
        "metrics": metrics,
    }


def get_status(controller) -> dict:
    """读取 Worker 当前状态。"""
    gateway = None
    try:
        gateway = controller.engine.main_engine.get_gateway(controller.engine.gateway_name)
    except Exception:
        gateway = None

    return {
        "state": "RUNNING",
        "busy": controller.task_lock.locked(),
        "current_case_id": controller.current_case_id,
        "gateway_exists": bool(gateway),
        "last_error": controller.last_error,
        "last_case_finished_at": controller.last_case_finished_at,
        "risk": get_risk_snapshot(controller.engine),
    }

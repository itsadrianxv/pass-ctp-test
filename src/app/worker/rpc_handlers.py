"""Worker RPC 请求处理。"""

from src.config import settings as read_config
from src.config.yaml import save_yaml_config


def _test_config_data() -> dict:
    """读取测试配置响应。"""
    return {
        "test_symbol": read_config.TEST_SYMBOL,
        "safe_buy_price": read_config.SAFE_BUY_PRICE,
        "deal_buy_price": read_config.DEAL_BUY_PRICE,
        "repeat_open_threshold": getattr(read_config, "REPEAT_OPEN_THRESHOLD", 2),
        "repeat_close_threshold": getattr(read_config, "REPEAT_CLOSE_THRESHOLD", 2),
        "volume_limit_volume": getattr(read_config, "VOLUME_LIMIT_VOLUME", 10000),
        "order_monitor_threshold": getattr(read_config, "ORDER_MONITOR_THRESHOLD", 1),
        "cancel_monitor_threshold": getattr(read_config, "CANCEL_MONITOR_THRESHOLD", 1),
    }


def _set_if_present(payload: dict, key: str, attr: str, caster, data_to_save: dict) -> None:
    """按需写入内存配置和待保存配置。"""
    value = payload.get(key)
    if value is None or str(value).strip() == "":
        return
    cast_value = caster(value)
    setattr(read_config, attr, cast_value)
    data_to_save[key] = cast_value


def set_test_config(payload: dict) -> dict:
    """更新测试配置。"""
    data_to_save = {}
    _set_if_present(payload, "test_symbol", "TEST_SYMBOL", str, data_to_save)
    _set_if_present(payload, "safe_buy_price", "SAFE_BUY_PRICE", float, data_to_save)
    _set_if_present(payload, "deal_buy_price", "DEAL_BUY_PRICE", float, data_to_save)
    _set_if_present(payload, "repeat_open_threshold", "REPEAT_OPEN_THRESHOLD", int, data_to_save)
    _set_if_present(payload, "repeat_close_threshold", "REPEAT_CLOSE_THRESHOLD", int, data_to_save)
    _set_if_present(payload, "volume_limit_volume", "VOLUME_LIMIT_VOLUME", int, data_to_save)
    _set_if_present(payload, "order_monitor_threshold", "ORDER_MONITOR_THRESHOLD", int, data_to_save)
    _set_if_present(payload, "cancel_monitor_threshold", "CANCEL_MONITOR_THRESHOLD", int, data_to_save)

    if data_to_save:
        save_yaml_config(read_config.CONFIG_YAML_PATH, data_to_save)

    return _test_config_data()


def handle_rpc_request(controller, req: dict) -> dict:
    """分发 Worker RPC 请求。"""
    request_id = req.get("request_id")
    req_type = str(req.get("type", "")).upper()
    payload = req.get("payload") or {}

    try:
        if req_type == "PING":
            return {"request_id": request_id, "ok": True, "data": {"pong": True}}
        if req_type == "GET_STATUS":
            return {"request_id": request_id, "ok": True, "data": controller.get_status()}
        if req_type == "GET_THRESHOLDS":
            return {"request_id": request_id, "ok": True, "data": (controller.get_risk_snapshot().get("thresholds") or {})}
        if req_type == "GET_RISK_SNAPSHOT":
            return {"request_id": request_id, "ok": True, "data": controller.get_risk_snapshot()}
        if req_type == "GET_TEST_CONFIG":
            return {"request_id": request_id, "ok": True, "data": _test_config_data()}
        if req_type == "SET_TEST_CONFIG":
            return {"request_id": request_id, "ok": True, "data": set_test_config(payload)}
        if req_type == "SET_THRESHOLDS":
            data = controller.set_thresholds(
                max_order_count=payload.get("max_order_count"),
                max_cancel_count=payload.get("max_cancel_count"),
                max_repeat_count=payload.get("max_repeat_count"),
            )
            return {"request_id": request_id, "ok": True, "data": data}
        if req_type == "RESET_RISK":
            controller.reset_risk()
            return {"request_id": request_id, "ok": True}
        if req_type == "RUN_CASE":
            accepted = controller.run_case(str(payload.get("case_id", "")))
            return {"request_id": request_id, "ok": True, "data": {"accepted": bool(accepted)}}
        if req_type == "DISCONNECT":
            controller.engine.disconnect()
            return {"request_id": request_id, "ok": True}
        if req_type == "RECONNECT":
            controller.engine.reconnect()
            return {"request_id": request_id, "ok": True}
        if req_type == "PAUSE":
            controller.engine.pause()
            return {"request_id": request_id, "ok": True}
        return {"request_id": request_id, "ok": False, "error": f"unknown_type: {req_type}"}
    except Exception as exc:
        return {"request_id": request_id, "ok": False, "error": str(exc)}

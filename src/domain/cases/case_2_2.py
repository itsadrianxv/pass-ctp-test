import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

# =============================================================================
# 2.2 异常监测
# =============================================================================

def test_2_2_1_1_connect_status(engine: TestEngine):
    """
    2.2.1.1 连接状态
    """
    log_info("\n>>> [2.2.1.1] 连接状态测试")
    
    log_info("--- 测试点 2.2.1.1: 当前连接状态 ---")
    gateway = engine.main_engine.get_gateway(engine.gateway_name)
    if gateway:
        log_info("当前网关对象: 存在（真实连接状态以底层回调/日志为准）")
    else:
        log_error("当前网关对象: 不存在（可能未完成初始化或已被逻辑断开）")

def test_2_2_1_2_disconnect(engine: TestEngine):
    """
    2.2.1.2 断线模拟
    """
    log_info("\n>>> [2.2.1.2] 断线模拟测试")

    log_info("--- 测试点 2.2.1.2: 模拟断线（强制断线） ---")


def test_2_2_1_3_reconnect(engine: TestEngine):
    """
    2.2.1.3 重连模拟
    """
    log_info("\n>>> [2.2.1.3] 重连模拟测试")

    log_info("--- 测试点 2.2.1.3: 模拟重连（强制断线后重连） ---")


def test_2_2_3_1_repeat_open(engine: TestEngine):
    """
    2.2.3.1 重复开仓
    """
    log_info("\n>>> [2.2.3.1] 重复开仓测试")
    if not check_contract(engine):
        return

    # 1. 重复开仓
    log_info("--- 测试点 2.2.3.1: 重复开仓 ---")
    repeat_open_threshold = int(getattr(config, "REPEAT_OPEN_THRESHOLD", 2) or 2)
    deal_count = max(1, repeat_open_threshold)
    safe_count = 1

    deal_vt_orderids = []
    safe_vt_orderid = ""

    for _ in range(deal_count):
        req = OrderRequest(
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,
            price=config.DEAL_BUY_PRICE,
            offset=Offset.OPEN,
            reference="RepeatOpen",
        )
        vt_id = engine.send_order(req)
        if vt_id:
            deal_vt_orderids.append(vt_id)

    for _ in range(safe_count):
        req = OrderRequest(
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,
            price=config.SAFE_BUY_PRICE,
            offset=Offset.OPEN,
            reference="RepeatOpen",
        )
        vt_id = engine.send_order(req)
        if vt_id and not safe_vt_orderid:
            safe_vt_orderid = vt_id

    engine.repeat_monitor_last = {
        "deal_open_vt_orderids": deal_vt_orderids,
        "safe_open_vt_orderid": safe_vt_orderid,
        "vt_symbol": getattr(engine.contract, "vt_symbol", ""),
    }
    wait_for_reaction(2, "等待重复开仓反馈")

def test_2_2_3_2_repeat_close(engine: TestEngine):
    """
    2.2.3.2 重复平仓
    """
    log_info("\n>>> [2.2.3.2] 重复平仓测试")
    if not check_contract(engine):
        return

    # 2. 重复平仓
    log_info("--- 测试点 2.2.3.2: 重复平仓 ---")
    repeat_close_threshold = int(getattr(config, "REPEAT_CLOSE_THRESHOLD", 2) or 2)
    info = getattr(engine, "repeat_monitor_last", None) or {}
    deal_open_vt_orderids = list(info.get("deal_open_vt_orderids") or [])
    close_count = min(max(1, repeat_close_threshold), len(deal_open_vt_orderids) or max(1, repeat_close_threshold))

    for _ in range(close_count):
        req = OrderRequest(
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
            direction=Direction.SHORT,
            type=OrderType.LIMIT,
            volume=1,
            price=config.SAFE_BUY_PRICE,
            offset=Offset.CLOSE,
            reference="RepeatClose",
        )
        engine.send_order(req)
    wait_for_reaction(2, "等待重复平仓反馈")

def test_2_2_3_3_repeat_cancel(engine: TestEngine):
    """
    2.2.3.3 重复撤单
    """
    log_info("\n>>> [2.2.3.3] 重复撤单测试")
    if not check_contract(engine):
        return

    # 3. 重复撤单 (构造一个存在的订单ID进行重复撤销)
    log_info("--- 测试点 2.2.3.3: 重复撤单 ---")
    info = getattr(engine, "repeat_monitor_last", None) or {}
    safe_open_vt_orderid = str(info.get("safe_open_vt_orderid") or "").strip()

    if safe_open_vt_orderid:
        wait_for_reaction(1, "等待挂单进入可撤状态")
        order = engine.orders.get(safe_open_vt_orderid)
        if order and order.is_active():
            engine.cancel_order(order.create_cancel_request())
        else:
            orderid = safe_open_vt_orderid.split(".")[-1]
            req_c = CancelRequest(
                orderid=orderid,
                symbol=engine.contract.symbol,
                exchange=engine.contract.exchange,
            )
            engine.cancel_order(req_c)
        wait_for_reaction(2, "等待撤单反馈")
        return

    req_base = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN,
    )
    vt_orderid = engine.send_order(req_base)
    wait_for_reaction(1)

    if vt_orderid:
        orderid = vt_orderid.split(".")[-1]
        req_c = CancelRequest(
            orderid=orderid,
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
        )
        engine.cancel_order(req_c)
        wait_for_reaction(2, "等待撤单反馈")

# =============================================================================
# 2.3 阈值管理
# =============================================================================


import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest, SubscribeRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def _list_data(data):
    """兼容 vn.py 列表和旧字典缓存返回。"""
    if isinstance(data, dict):
        return list(data.values())
    return list(data) if data else []


def _sample_cancel_request(engine: TestEngine) -> CancelRequest:
    """构造异常连接下的撤单请求。"""
    exchange = engine.contract.exchange if engine.contract else Exchange.CFFEX
    symbol = engine.contract.symbol if engine.contract else config.TEST_SYMBOL
    return CancelRequest(orderid="DISCONNECTED", symbol=symbol, exchange=exchange)


def _sample_order_request(engine: TestEngine) -> OrderRequest:
    """构造异常连接下的委托请求。"""
    exchange = engine.contract.exchange if engine.contract else Exchange.CFFEX
    symbol = engine.contract.symbol if engine.contract else config.TEST_SYMBOL
    return OrderRequest(
        symbol=symbol,
        exchange=exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN,
        reference="Disconnected",
    )


def _sample_subscribe_request(engine: TestEngine) -> SubscribeRequest:
    """构造异常连接下的行情订阅请求。"""
    exchange = engine.contract.exchange if engine.contract else Exchange.CFFEX
    symbol = engine.contract.symbol if engine.contract else config.TEST_SYMBOL
    return SubscribeRequest(symbol=symbol, exchange=exchange)


def test_2_1_1_1_normal_connectivity(engine: TestEngine):
    """
    2.1.1.1 正常连接适应性测试。
    """
    log_info("\n>>> [2.1.1.1] 正常连接适应性测试")
    # 检查连接
    if not engine.is_gateway_ready():
        log_info("正在建立连接...")
        engine.connect()
    else:
        log_info("网关已连接，正在检查登录状态...")
    
    # 实际上 connect 是异步的，这里只能通过日志观察
    wait_for_reaction(3, "等待连接与认证回调...")

    # 查询账户资金
    log_info("正在查询账户资金...")
    wait_for_reaction(2, "等待流控冷却...")
    gateway = engine.main_engine.get_gateway(engine.gateway_name)
    if gateway:
        gateway.query_account()
        wait_for_reaction(5, "等待账户资金回报")
        engine.log_current_account()

    log_info("正在获取所有订单...")
    orders = _list_data(engine.main_engine.get_all_orders())
    log_info(f"当前订单数量: {len(orders)}")
    for order in orders:
        log_info(f"订单: {order}")

    log_info("正在获取所有持仓...")
    positions = _list_data(engine.main_engine.get_all_positions())
    log_info(f"当前持仓数量: {len(positions)}")
    for pos in positions:
        log_info(f"持仓: {pos}")

    log_info("正在检查合约同步状态...")
    if check_contract(engine):
        log_info(f"测试合约已同步: {engine.contract.vt_symbol}")
        ok = engine.subscribe(_sample_subscribe_request(engine))
        log_info(f"行情订阅请求结果: {'已提交' if ok else '未提交'}")
    else:
        log_warning("测试合约未同步，跳过行情订阅检查。")


def test_2_1_1_2_abnormal_connectivity(engine: TestEngine):
    """
    2.1.1.2 异常连接适应性测试。
    """
    log_info("\n>>> [2.1.1.2] 异常连接适应性测试")
    log_info("正在通过移除 MainEngine 网关模拟连接异常...")
    engine.disconnect()

    if engine.is_gateway_ready():
        log_error("异常连接模拟失败：网关仍然存在。")
        return

    log_info("网关已不存在，开始验证接口异常路径...")
    vt_orderid = engine.send_order(_sample_order_request(engine))
    cancel_ok = engine.cancel_order(_sample_cancel_request(engine))
    sub_ok = engine.subscribe(_sample_subscribe_request(engine))

    log_info(f"断连发单结果: {'异常' if not vt_orderid else vt_orderid}")
    log_info(f"断连撤单结果: {'异常' if not cancel_ok else '已提交'}")
    log_info(f"断连订阅结果: {'异常' if not sub_ok else '已提交'}")

    if vt_orderid or cancel_ok or sub_ok:
        log_error("异常连接适应性检查失败：存在接口在断连状态下被提交。")
    else:
        log_info("异常连接适应性检查通过：断连状态下交易/行情接口均被拦截。")

    log_info("正在恢复连接，避免影响后续测试...")
    engine.reconnect()
    wait_for_reaction(3, "等待重连回调...")


def test_2_1_2_1_open(engine: TestEngine):
    """
    2.1.2.1 开仓测试
    """
    log_info("\n>>> [2.1.2.1] 开仓测试")
    
    if not check_contract(engine):
        return

    # 0. 环境清理
    clean_environment(engine)

    # 1. 开仓 (2.1.2.1)
    log_info("--- 测试点 2.1.2.1: 开仓 ---")
    req_open = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.DEAL_BUY_PRICE,
        offset=Offset.OPEN,
        reference="TestOpen"
    )
    engine.send_order(req_open)
    wait_for_reaction(10, "等待开仓成交")

def test_2_1_2_2_close(engine: TestEngine):
    """
    2.1.2.2 平仓测试
    """
    log_info("\n>>> [2.1.2.2] 平仓测试")
    
    if not check_contract(engine):
        return

    # 2. 平仓 (2.1.2.2)
    log_info("--- 测试点 2.1.2.2: 平仓 ---")
    req_close = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.SHORT,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE, # 确保成交
        offset=Offset.CLOSE,
        reference="TestClose"
    )
    engine.send_order(req_close)
    wait_for_reaction(10, "等待平仓成交")

def test_2_1_2_3_cancel(engine: TestEngine):
    """
    2.1.2.3 撤单测试
    """
    log_info("\n>>> [2.1.2.3] 撤单测试")
    
    if not check_contract(engine):
        return

    # 3. 撤单 (2.1.2.3)
    log_info("--- 测试点 2.1.2.3: 撤单 ---")
    req_cancel_test = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE, # 远离市价
        offset=Offset.OPEN,
        reference="TestCancel"
    )
    vt_orderid = engine.send_order(req_cancel_test)
    wait_for_reaction(10, "等待挂单确认")
    
    if vt_orderid:
        orderid = vt_orderid.split(".")[-1]
        req_c = CancelRequest(
            orderid=orderid,
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange
        )
        engine.cancel_order(req_c)
        wait_for_reaction(10, "等待撤单回报")

import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def test_2_1_1_connectivity(engine: TestEngine):
    """
    2.1.1 连通性测试
    覆盖: 2.1.1.1 登录认证
    """
    log_info("\n>>> [2.1.1] 连通性测试")
    # 检查连接
    if not engine.main_engine.get_gateway(engine.gateway_name):
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
    all_orders = engine.main_engine.get_all_orders()
    orders = list(all_orders.values()) if isinstance(all_orders, dict) else (list(all_orders) if all_orders else [])
    log_info(f"当前订单数量: {len(orders)}")
    for order in orders:
        log_info(f"订单: {order}")



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

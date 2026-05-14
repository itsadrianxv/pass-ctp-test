import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def test_2_4_1_1_code_error(engine: TestEngine):
    """
    2.4.1.1 合约代码错误
    """
    log_info("\n>>> [2.4.1.1] 合约代码错误测试")
    
    # 1. 代码错误
    log_info("--- 测试点 2.4.1.1: 合约代码错误 ---")
    req_err_sym = OrderRequest(
        symbol="INVALID_CODE",
        exchange=Exchange.SHFE,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=4000,
        offset=Offset.OPEN
    )
    engine.send_order(req_err_sym)
    wait_for_reaction(5, "等待 5 秒，查看是否出现错误日志")

def test_2_4_1_2_price_error(engine: TestEngine):
    """
    2.4.1.2 最小变动价位错误
    """
    log_info("\n>>> [2.4.1.2] 价格错误测试")

    # 2. 价格错误
    log_info("--- 测试点 2.4.1.2: 最小变动价位错误 ---")
    if engine.contract:
        req_err_tick = OrderRequest(
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,
            price=config.SAFE_BUY_PRICE + 0.0001, # 假设 tick > 0.0001
            offset=Offset.OPEN
        )
        engine.send_order(req_err_tick)
        wait_for_reaction(5, "等待 5 秒，查看是否出现错误日志")

def test_2_4_1_3_volume_error(engine: TestEngine):
    """
    2.4.1.3 委托数量超限
    """
    log_info("\n>>> [2.4.1.3] 数量超限测试")

    # 3. 数量超限
    log_info("--- 测试点 2.4.1.3: 委托数量超限 ---")
    volume_limit = int(getattr(config, "VOLUME_LIMIT_VOLUME", 10000) or 10000)
    symbol = str(getattr(config, "TEST_SYMBOL", "") or "").strip()
    if not symbol and engine.contract:
        symbol = engine.contract.symbol
    if not symbol:
        log_error("未设置测试合约代码，跳过测试")
        return

    exchange = engine.contract.exchange if engine.contract else Exchange.SHFE
    req_err_vol = OrderRequest(
        symbol=symbol,
        exchange=exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=max(1, volume_limit),
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN,
    )
    engine.send_order(req_err_vol)
    
    wait_for_reaction(2, "验证红色错误日志")

def test_2_4_2_1_fund_error(engine: TestEngine):
    """
    2.4.2.1 资金不足回报
    """
    log_info("\n>>> [2.4.2.1] 资金不足测试")
    if not engine.contract: return

    # 1. 资金不足
    log_info("--- 测试点 2.4.2.1: 资金不足回报 ---")
    req_fund = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=50000, # 足够大
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN,
        reference="FundTest"
    )
    engine.send_order(req_fund)
    wait_for_reaction(5, "等待 5 秒，查看是否出现错误日志")

def test_2_4_2_2_pos_error(engine: TestEngine):
    """
    2.4.2.2 持仓不足回报
    """
    log_info("\n>>> [2.4.2.2] 持仓不足测试")
    if not engine.contract: return

    # 2. 持仓不足
    log_info("--- 测试点 2.4.2.2: 持仓不足回报 ---")
    req_pos = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.SHORT,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE,
        offset=Offset.CLOSE, # 平仓
        reference="CloseEmpty"
    )
    engine.send_order(req_pos)
    
    wait_for_reaction(3, "等待 CTP 错误回报")
    wait_for_reaction(5, "等待 5 秒，查看是否出现错误日志")

def test_2_4_2_3_market_error(engine: TestEngine):
    """
    2.4.2.3 市场状态错误回报
    """
    log_info("\n>>> [2.4.2.3] 市场状态错误测试")
    if not engine.contract: return

    # 3. 市场状态错误 (2.4.2.3)
    log_info("--- 测试点 2.4.2.3: 市场状态错误回报 ---")
    
    # 优先使用专用测试合约的交易所信息
    exchange = engine.contract.exchange
    if engine.rest_test_contract:
        exchange = engine.rest_test_contract.exchange
    elif config.REST_TEST_SYMBOL == "LC2607":
        exchange = Exchange.GFEX
    else:
        log_warning(f"未找到测试合约 {config.REST_TEST_SYMBOL} 的合约信息，将使用默认交易所 {exchange.value}，可能导致测试失败。")

    req_market = OrderRequest(
        symbol=config.REST_TEST_SYMBOL,
        exchange=exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.REST_TEST_PRICE,
        offset=Offset.OPEN,
        reference="MarketErrTest"
    )
    engine.send_order(req_market)
    wait_for_reaction(5, "等待可能出现的市场状态错误回报")


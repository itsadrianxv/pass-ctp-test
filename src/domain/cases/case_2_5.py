import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def test_2_5_1_1_limit_perms(engine: TestEngine):
    """
    2.5.1.1 限制账号交易权限
    """
    log_info("\n>>> [2.5.1.1] 限制权限测试")
    if not engine.contract:
        log_error("未获取到合约，跳过测试")
        return

    req = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN
    )

    # ==========================================
    # 2.5.1.1 限制账号交易权限
    # ==========================================
    log_info("--- 测试点 2.5.1.1: 限制账号交易权限 ---")
    # 模拟权限限制 (通过 RiskManager active=False 模拟本地权限锁)
    engine.risk_manager.active = False
    log_info("已限制交易权限 (Active=False)")
    
    engine.send_order(req)
    wait_for_reaction(1, "验证权限限制下被拦截")
    
    # 恢复
    engine.risk_manager.active = True
    log_info("已恢复交易权限")
    wait_for_reaction(2)

def test_2_5_1_2_pause_strategy(engine: TestEngine):
    """
    2.5.1.2 暂停策略执行
    """
    log_info("\n>>> [2.5.1.2] 暂停策略测试")
    if not engine.contract:
        log_error("未获取到合约，跳过测试")
        return
    
    req = OrderRequest(
        symbol=engine.contract.symbol,
        exchange=engine.contract.exchange,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=config.SAFE_BUY_PRICE,
        offset=Offset.OPEN
    )

    # ==========================================
    # 2.5.1.2 暂停策略执行
    # ==========================================
    log_info("--- 测试点 2.5.1.2: 暂停策略执行 ---")
    
    # 执行暂停
    engine.pause() # 调用 emergency_stop
    
    engine.send_order(req)
    wait_for_reaction(1, "验证暂停策略下被拦截")
    
    # 恢复
    engine.risk_manager.active = True
    log_info("已恢复策略执行")
    wait_for_reaction(2)

def test_2_5_2_1_cancel_part(engine: TestEngine):
    """
    2.5.2.1 撤销部分成交（模拟撤单）
    """
    log_info("\n>>> [2.5.2.1] 撤销指定订单测试")
    
    # 确保活跃
    engine.risk_manager.active = True
    
    # 发送挂单
    if engine.contract:
        req = OrderRequest(
            symbol=engine.contract.symbol,
            exchange=engine.contract.exchange,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,
            price=config.SAFE_BUY_PRICE,
            offset=Offset.OPEN,
            reference=f"PartCancel"
        )
        vt_id = engine.send_order(req)
        wait_for_reaction(2, "等待挂单生效")
        
        if vt_id:
            active = engine.get_order(vt_id)
            if active and active.is_active():
                engine.cancel_order(active.create_cancel_request())
                wait_for_reaction(2, "撤单已发送")
            else:
                log_warning("订单未激活，跳过撤单")

def test_2_5_2_2_cancel_all(engine: TestEngine):
    """
    2.5.2.2 批量撤销所有订单
    """
    log_info("\n>>> [2.5.2.2] 批量撤销所有订单测试")
    
    # 确保活跃
    engine.risk_manager.active = True
    
    # 发送几笔挂单
    for i in range(3):
        if engine.contract:
            req = OrderRequest(
                symbol=engine.contract.symbol,
                exchange=engine.contract.exchange,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=1,
                price=config.SAFE_BUY_PRICE,
                offset=Offset.OPEN,
                reference=f"Batch{i}"
            )
            engine.send_order(req)
    
    wait_for_reaction(2, "等待挂单生效")
    
    # 执行批量撤单
    log_info("--- 执行批量撤单 ---")
    active_orders = engine.get_all_active_orders()
    log_info(f"检测到 {len(active_orders)} 笔活动订单，开始撤销...")
    
    for order in active_orders:
        engine.cancel_order(order.create_cancel_request())
        
    wait_for_reaction(3, "等待所有撤单完成")

# =============================================================================
# 2.6 日志记录
# =============================================================================


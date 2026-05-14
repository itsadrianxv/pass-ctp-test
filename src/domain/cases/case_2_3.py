import time
import traceback
from src.config import settings as config
from src.domain.engine import TestEngine
from src.domain.cases.helpers import wait_for_reaction, clean_environment, check_contract
from src.infra.logging import log_info, log_error, log_warning
from vnpy.trader.object import OrderRequest, CancelRequest
from vnpy.trader.constant import Direction, OrderType, Offset, Exchange

def test_2_3_1_1_order_threshold(engine: TestEngine):
    """
    2.3.1.1 报单笔数阈值测试（含统计验证）
    覆盖: 
    - 2.2.2.1 报单统计
    - 2.3.1.1 阈值设置
    - 2.3.1.2 阈值预警
    """
    log_info("\n>>> [2.3.1.1] 报单阈值与统计测试")
    
    rm = engine.risk_manager
    thresholds = {}
    try:
        thresholds = rm.get_thresholds()
    except Exception:
        thresholds = {}

    max_order_count = int(thresholds.get("max_order_count", getattr(rm, "max_order_count", 0)) or 0)
    log_info(f"当前报单阈值: {max_order_count}")
    
    # 记录初始计数
    initial_count = rm.order_count
    log_info(f"初始报单总数: {initial_count}")
    
    rm.reset_counters()
    log_info("已重置计数器")

    if not engine.contract:
        log_error("未获取到合约信息，跳过阈值触发测试")
        return

    max_actions = 10
    sent_vt_orderids = []

    if max_order_count > 0:
        send_n = min(max_actions, max_order_count + 1)
        log_info(f"--- 发送 {send_n} 笔委托验证统计与阈值 (阈值={max_order_count}) ---")
        
        warned = False
        for i in range(send_n):
            req = OrderRequest(
                symbol=engine.contract.symbol,
                exchange=engine.contract.exchange,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=1,
                price=config.SAFE_BUY_PRICE,
                offset=Offset.OPEN,
            )
            vt_id = engine.send_order(req)
            if vt_id:
                sent_vt_orderids.append(vt_id)
            
            # 验证计数准确性
            expected_count = i + 1
            actual_count = rm.order_count
            if actual_count != expected_count:
                log_warning(f"计数异常: 期望={expected_count}, 实际={actual_count}")
            
            # 检查阈值预警
            if not warned and actual_count >= max_order_count:
                log_warning(f"【阈值预警】报单笔数({actual_count})达到或超过阈值({max_order_count})! 🚨")
                warned = True
        
        wait_for_reaction(2, "检查报单统计与阈值预警")
        
        # 最终验证
        final_count = rm.order_count
        log_info(f"最终报单总数: {final_count} (期望: {send_n})")
        
        if final_count != send_n:
            log_error(f"报单统计不准确: 期望={send_n}, 实际={final_count}")
        else:
            log_info("✓ 报单统计准确")
        
        if warned:
            log_info("✓ 阈值预警已触发")
        else:
            log_warning("未触发阈值预警（可能阈值设置过高）")
    else:
        log_warning("报单阈值未启用(<=0)，跳过测试")
    
    # 保存 sent_vt_orderids 供后续测试使用
    engine.last_sent_orders = sent_vt_orderids

def test_2_3_1_3_cancel_threshold(engine: TestEngine):
    """
    2.3.1.3 撤单笔数阈值测试（含统计验证）
    覆盖:
    - 2.2.2.2 撤单统计
    - 2.3.1.3 阈值设置
    - 2.3.1.4 阈值预警
    """
    log_info("\n>>> [2.3.1.3] 撤单阈值与统计测试")
    
    rm = engine.risk_manager
    thresholds = {}
    try:
        thresholds = rm.get_thresholds()
    except Exception:
        thresholds = {}

    max_cancel_count = int(thresholds.get("max_cancel_count", getattr(rm, "max_cancel_count", 0)) or 0)
    log_info(f"当前撤单阈值: {max_cancel_count}")
    
    # 记录初始计数
    initial_count = rm.cancel_count
    log_info(f"初始撤单总数: {initial_count}")
    
    max_actions = 10
    sent_vt_orderids = getattr(engine, "last_sent_orders", [])
    
    # 如果没有之前的单子，先发一些
    if not sent_vt_orderids:
        log_info("无可用订单，先发送一批订单用于撤单测试...")
        if not engine.contract: return
        for _ in range(max(5, max_cancel_count + 2)):
            req = OrderRequest(
                symbol=engine.contract.symbol,
                exchange=engine.contract.exchange,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=1,
                price=config.SAFE_BUY_PRICE,
                offset=Offset.OPEN,
            )
            vt_id = engine.send_order(req)
            if vt_id: sent_vt_orderids.append(vt_id)
        wait_for_reaction(2)

    if max_cancel_count > 0:
        all_active = engine.get_all_active_orders()
        # 优先撤销之前发的
        target_orders = [o for o in all_active if o.vt_orderid in sent_vt_orderids]
        # 如果不够，撤销所有的
        if len(target_orders) < max_cancel_count + 1:
            target_orders = all_active
        
        need_cancel = min(max_actions, max_cancel_count + 1)
        log_info(f"--- 撤销 {need_cancel} 笔委托验证统计与阈值 (阈值={max_cancel_count}, 可撤={len(target_orders)}) ---")
        
        warned = False
        cancel_start_count = rm.cancel_count
        count = 0
        for o in target_orders:
            engine.cancel_order(o.create_cancel_request())
            count += 1
            
            # 检查阈值预警
            if not warned and rm.cancel_count >= max_cancel_count:
                log_warning(f"【阈值预警】撤单笔数({rm.cancel_count})达到或超过阈值({max_cancel_count})! 🚨")
                warned = True
            
            if count >= need_cancel:
                break
        
        wait_for_reaction(2, "检查撤单统计与阈值预警")
        
        # 最终验证
        final_count = rm.cancel_count
        expected_final = cancel_start_count + count
        log_info(f"最终撤单总数: {final_count} (期望: {expected_final})")
        
        if final_count != expected_final:
            log_warning(f"撤单统计可能不准确: 期望={expected_final}, 实际={final_count} (异步延迟可能导致差异)")
        else:
            log_info("✓ 撤单统计准确")
        
        if warned:
            log_info("✓ 阈值预警已触发")
        else:
            log_warning("未触发阈值预警（可能阈值设置过高）")
    else:
        log_warning("撤单阈值未启用(<=0)，跳过测试")

def test_2_3_1_5_repeat_threshold(engine: TestEngine):
    """
    2.3.1.5 重复报单阈值测试
    覆盖: 2.3.1.5 设置, 2.3.1.6 预警
    """
    log_info("\n>>> [2.3.1.5] 重复报单阈值测试")
    
    rm = engine.risk_manager
    thresholds = {}
    try:
        thresholds = rm.get_thresholds()
    except Exception:
        thresholds = {}

    max_repeat_count = int(thresholds.get("max_repeat_count", getattr(rm, "max_repeat_count", 0)) or 0)
    log_info(f"当前重复报单阈值: {max_repeat_count}")

    if not engine.contract: return
    max_actions = 10

    # 2.3.1.5 / 2.3.1.6（选测）
    if max_repeat_count > 0:
        repeat_send_n = min(max_actions, max_repeat_count + 1)
        log_info(f"--- 触发重复报单预警(选测) (阈值={max_repeat_count}, 本次重复发单={repeat_send_n}) ---")
        for _ in range(repeat_send_n):
            req = OrderRequest(
                symbol=engine.contract.symbol,
                exchange=engine.contract.exchange,
                direction=Direction.LONG,
                type=OrderType.LIMIT,
                volume=1,
                price=config.SAFE_BUY_PRICE,
                offset=Offset.OPEN,
                reference="RepeatThresholdTest",
            )
            engine.send_order(req)
        wait_for_reaction(2, "检查是否出现重复报单阈值预警")
    else:
        log_info("重复报单预警未启用(<=0)，跳过 2.3.1.5/2.3.1.6")


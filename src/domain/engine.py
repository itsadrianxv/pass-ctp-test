import src.infra.path_setup  # noqa: F401 — must be first to override pip vnpy
from typing import Dict, Optional, List
from vnpy.event import EventEngine, Event
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import EVENT_LOG, EVENT_CONTRACT, EVENT_ORDER, EVENT_TRADE, EVENT_ACCOUNT
from vnpy.trader.object import OrderRequest, CancelRequest, SubscribeRequest, ContractData, OrderData, TradeData, LogData, AccountData
from vnpy.trader.constant import Status

from src.config import settings as config
from src.infra.logging import log_info, log_error, log_warning
from src.domain.risk import TestRiskManager

class TestEngine(BaseEngine):
    """
    渗透测试的 function engine。
    集成：
    - 风控管理器
    - 测试状态缓存
    - 事件处理
    """
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """初始化测试引擎。"""
        super().__init__(main_engine, event_engine, "test")
        self.gateway_name = "CTPTEST"
        
        self.risk_manager = TestRiskManager(self)
        
        # 状态
        self.contract: Optional[ContractData] = None
        self.rest_test_contract: Optional[ContractData] = None
        self.orders: Dict[str, OrderData] = {}
        self.account: Optional[AccountData] = None # 缓存最新的账户信息
        self.session_order_ids = set() # 记录本次会话发出的订单ID
        self._removed_gateway = None
        
        # 错误码处理
        self.rejected_orders: Dict[str, OrderData] = {}
        
        # 事件钩子
        self.event_engine.register(EVENT_LOG, self.on_log)
        self.event_engine.register(EVENT_ORDER, self.on_order)
        self.event_engine.register(EVENT_TRADE, self.on_trade)
        self.event_engine.register(EVENT_CONTRACT, self.on_contract)
        self.event_engine.register(EVENT_ACCOUNT, self.on_account)

    def connect(self):
        """连接 CTP 测试网关。"""
        log_info("正在连接 CTP 测试环境...")
        if self.gateway_name not in self.main_engine.gateways:
            log_error("CTP 测试网关未注册，请先在 MainEngine 中添加 CtptestGateway。")
            return
        self.main_engine.connect(config.CTP_SETTING, self.gateway_name)

    def is_gateway_ready(self) -> bool:
        """判断 CTP 测试网关是否可用。"""
        return bool(self.main_engine.get_gateway(self.gateway_name))

    def _require_gateway(self, action: str) -> bool:
        """检查网关可用性，不可用时记录连接异常。"""
        if self.is_gateway_ready():
            return True
        log_error(f"{action}失败：CTP 测试网关不存在，当前处于连接异常状态。")
        return False

    def disconnect(self):
        """断开 CTP 测试网关。"""
        log_info("正在执行断线操作 (DISCONNECT)...")
        # 此处采用从 MainEngine 当中移除 ctp 网关连接，来模拟断连
        
        if self.gateway_name in self.main_engine.gateways:
            self._removed_gateway = self.main_engine.gateways.pop(self.gateway_name)
            log_info("CTP网关实例已从MainEngine当中移除")
        else:
            log_info("CTP网关实例不在MainEngine中，无需移除。")

        # 立即返回，确保 Web 服务存活
        log_info("断线操作已完成")

    def reconnect(self):
        """重新连接 CTP 测试网关。"""
        log_info("正在执行重连操作")
        # 强制垃圾回收 (尝试性)
        import gc
        gc.collect()

        if self.gateway_name not in self.main_engine.gateways and self._removed_gateway:
            self.main_engine.gateways[self.gateway_name] = self._removed_gateway
            log_info("已恢复从MainEngine当中被移除的CTP网关。")
        
        self.connect()

    def pause(self):
        """暂停交易。"""
        log_info("正在执行暂停交易操作")
        self.risk_manager.emergency_stop()

    def send_order(self, req: OrderRequest) -> str:
        """发送委托。"""
        if not self._require_gateway("发送委托"):
            return ""
        if self.risk_manager.check_order(req):
            returned_id = self.main_engine.send_order(req, self.gateway_name)
            vt_orderid = str(returned_id or "").strip()
            if vt_orderid and "." not in vt_orderid:
                vt_orderid = f"{self.gateway_name}.{vt_orderid}"

            log_info(f"【发单】{req.symbol} {req.direction.value} Price:{req.price} -> ID:{vt_orderid}")
            
            # 在风控管理器中注册订单以进行会话追踪
            if vt_orderid:
                self.risk_manager.register_order(vt_orderid)
                self.session_order_ids.add(vt_orderid)
            
            return vt_orderid
        else:
            log_warning("订单被风控管理器拒绝。")
        return ""

    def cancel_order(self, req: CancelRequest) -> bool:
        """发送撤单。"""
        if not self._require_gateway("发送撤单"):
            return False
        if self.risk_manager.check_cancel(req):
            self.risk_manager.register_cancel_request(req)
            log_info(f"【撤单】Req Cancel OrderID: {req.orderid}")
            self.main_engine.cancel_order(req, self.gateway_name)
            return True
        else:
            log_warning("撤单被风控管理器拒绝。")
        return False

    def subscribe(self, req: SubscribeRequest) -> bool:
        """订阅行情。"""
        if not self._require_gateway("订阅行情"):
            return False
        self.main_engine.subscribe(req, self.gateway_name)
        log_info(f"Subscribed to {req.symbol}")
        return True

    def on_log(self, event: Event):
        """处理网关日志事件。"""
        log: LogData = event.data
        # 我们将所有底层日志记录到我们的文件中
        # 如果 logger 已经处理了 stdout，则避免重复打印，
        # 但 vnpy 日志可能有助于清晰查看。
        # logger.py 处理格式化，所以我们只传递消息。
        # 检查是否为错误
        msg = f"[Gateway] {log.msg}"
        log_info(msg)

    def on_order(self, event: Event):
        """处理委托回报事件。"""
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order
        
        # 仅当订单是本次会话产生的才打印日志
        if order.vt_orderid in self.session_order_ids:
            log_info(f"-> 收到委托回报: {order.vt_orderid} Status:{order.status.value}")
        
        if order.status == "AllTraded" or order.status == "PartTraded":
            pass # 在 trade 中处理
        
        # === 新增：错误码处理 ===
        try:
            self._process_rejection(order)
        except Exception as e:
            log_error(f"错误码处理异常: {e}")
        
        # 更新风控管理器
        # 我们需要检测“已提交”（刚发送）与“已撤销”
        # 因为 on_order 会在状态变更时触发。
        # 我们只需将所有内容传递给风控管理器并让其过滤。
        # 但风控管理器期望每个订单只触发一次 "on_order_submitted"？
        # 简化：实际上风控管理器在 'send_order' 中计数提交（check_order 增加计数）。
        # 等等，check_order 在发送前增加计数。
        # 以前的代码有：
        # check_order -> count++
        # on_order_submitted -> 打印日志
        # on_order_cancelled -> count++ 并打印日志
        
        self.risk_manager.on_order_submitted(order)
        if order.status == Status.CANCELLED:
            self.risk_manager.on_order_cancelled(order)

    def on_trade(self, event: Event):
        """处理成交回报事件。"""
        trade: TradeData = event.data
        vt_orderid = getattr(trade, "vt_orderid", "") or ""
        if not vt_orderid and getattr(trade, "orderid", None):
            vt_orderid = f"{self.gateway_name}.{trade.orderid}"

        if vt_orderid in self.session_order_ids:
            log_info(f"-> 收到成交回报: {vt_orderid} {trade.vt_tradeid} Price:{trade.price} Vol:{trade.volume}")

    def on_contract(self, event: Event):
        """处理合约事件。"""
        contract: ContractData = event.data
        # 仅处理测试目标合约
        if contract.symbol == config.TEST_SYMBOL:
            self.contract = contract
            log_info(f"Contract found: {contract.vt_symbol}")
        elif contract.symbol == config.REST_TEST_SYMBOL:
            self.rest_test_contract = contract
            log_info(f"Rest Test Contract found: {contract.vt_symbol}")
        # 其他合约静默处理，避免日志刷屏

    def on_account(self, event: Event):
        """处理账户事件。"""
        # 仅缓存数据，不再自动打印日志
        self.account = event.data

    def log_current_account(self):
        """主动打印当前账户资金"""
        if self.account:
             log_info(f"-> 账户资金: 余额={self.account.balance} 可用={self.account.available}")
        else:
             log_info("-> 尚未获取到账户资金信息")

    def get_all_active_orders(self) -> List[OrderData]:
        """读取所有活动订单。"""
        return [o for o in self.orders.values() if o.is_active()]

    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        """按 vt_orderid 读取订单。"""
        return self.orders.get(vt_orderid)

    def _process_rejection(self, order: OrderData):
        """
        处理被拒绝的订单，执行日志记录、存储、风控通知和事件发射。
        """
        reject_code = getattr(order, 'reject_code', None)
        status_msg = getattr(order, 'status_msg', '') or ''
        
        # 条件1: 有明确的 reject_code
        # 条件2: 状态为 REJECTED
        has_reject = reject_code is not None
        is_rejected_status = order.status == Status.REJECTED
        
        if not has_reject and not is_rejected_status:
            # 对于非拒绝订单，如果 status_msg 非空且包含有用信息，记录诊断日志
            if status_msg and order.status == Status.CANCELLED:
                log_info(f"【委托状态】{order.vt_orderid} 已撤销, StatusMsg: {status_msg}")
            return
        
        reject_reason = getattr(order, 'reject_reason', '') or ''
        
        # 1. 日志记录
        log_warning(
            f"【CTP拒绝】{order.vt_orderid} "
            f"错误码:{reject_code} 原因:{reject_reason} "
            f"合约:{order.symbol} 方向:{order.direction.value} "
            f"价格:{order.price} 数量:{order.volume}"
        )
        
        # 2. 存储
        self.rejected_orders[order.vt_orderid] = order
        
        # 3. 风控通知
        self.risk_manager.on_order_rejected(order)
        
    def close(self):
        """关闭测试引擎。"""
        return

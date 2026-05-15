"""验证重构后的包结构。"""

import inspect

import src.infra.path_setup  # noqa: F401


def test_new_layout_imports():
    """新目录中的核心模块应该可以导入。"""
    from src.app.web.factory import create_app
    from src.app.worker.controller import WorkerController
    from src.config import settings
    from src.domain.app import TestApp
    from src.domain.engine import TestEngine
    from src.infra.rpc.client import RpcClient

    assert create_app
    assert WorkerController
    assert settings.RPC_HOST
    assert TestApp
    assert TestEngine
    assert RpcClient


def test_test_engine_is_vnpy_app_engine():
    """测试引擎应该作为 vn.py App 的 function engine 注册。"""
    from vnpy.trader.engine import BaseEngine

    from src.domain.app import TestApp
    from src.domain.engine import TestEngine

    params = list(inspect.signature(TestEngine).parameters)

    assert issubclass(TestEngine, BaseEngine)
    assert TestApp.engine_class is TestEngine
    assert params == ["main_engine", "event_engine"]


def test_worker_controller_owns_main_engine(monkeypatch):
    """Worker 应该创建唯一 MainEngine 并通过 TestApp 获取测试引擎。"""
    from vnpy.trader.gateway import BaseGateway

    from src.app.worker import controller as controller_mod
    from src.domain.engine import TestEngine

    class FakeGateway(BaseGateway):
        """测试用轻量网关。"""

        default_name = "CTPTEST"
        exchanges = []

        def connect(self, setting):
            """跳过真实连接。"""

        def subscribe(self, req):
            """跳过真实订阅。"""

        def send_order(self, req):
            """返回固定委托号。"""
            return "1"

        def cancel_order(self, req):
            """跳过真实撤单。"""

        def query_account(self):
            """跳过账户查询。"""

        def query_position(self):
            """跳过持仓查询。"""

        def close(self):
            """跳过关闭。"""

    class FakeNotifier:
        """测试用通知器。"""

        def __init__(self, controller, web_socketio_url):
            """保存控制器引用。"""
            self.controller = controller

        def start(self):
            """跳过后台线程。"""

        def stop(self):
            """跳过停止逻辑。"""

    monkeypatch.setattr(controller_mod, "CtptestGateway", FakeGateway)
    monkeypatch.setattr(controller_mod, "WorkerNotifier", FakeNotifier)
    monkeypatch.setattr(TestEngine, "connect", lambda self: None)

    controller = controller_mod.WorkerController()

    try:
        assert controller.main_engine is controller.engine.main_engine
        assert controller.event_engine is controller.engine.event_engine
        assert "TestApp" in controller.main_engine.apps
        assert "test" in controller.main_engine.engines
        assert controller.main_engine.get_engine("test") is controller.engine
    finally:
        controller.main_engine.close()


def test_test_engine_delegates_requests_to_main_engine(monkeypatch):
    """测试引擎应该通过 MainEngine 路由交易请求。"""
    from vnpy.event import EventEngine
    from vnpy.trader.constant import Direction, Exchange, Offset, OrderType
    from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

    from src.domain.engine import TestEngine

    class FakeMainEngine:
        """记录调用的主引擎。"""

        def __init__(self):
            """初始化调用记录。"""
            self.gateways = {"CTPTEST": object()}
            self.calls = []

        def get_gateway(self, gateway_name):
            """读取测试网关。"""
            return self.gateways.get(gateway_name)

        def send_order(self, req, gateway_name):
            """记录发单调用。"""
            self.calls.append(("send_order", req, gateway_name))
            return "123"

        def cancel_order(self, req, gateway_name):
            """记录撤单调用。"""
            self.calls.append(("cancel_order", req, gateway_name))

        def subscribe(self, req, gateway_name):
            """记录订阅调用。"""
            self.calls.append(("subscribe", req, gateway_name))

    main_engine = FakeMainEngine()
    event_engine = EventEngine()
    engine = TestEngine(main_engine, event_engine)
    monkeypatch.setattr(engine.risk_manager, "check_order", lambda req: True)
    monkeypatch.setattr(engine.risk_manager, "check_cancel", lambda req: True)

    order_req = OrderRequest(
        symbol="IF2406",
        exchange=Exchange.CFFEX,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=100,
        offset=Offset.OPEN,
    )
    cancel_req = CancelRequest(orderid="123", symbol="IF2406", exchange=Exchange.CFFEX)
    sub_req = SubscribeRequest(symbol="IF2406", exchange=Exchange.CFFEX)

    vt_orderid = engine.send_order(order_req)
    engine.cancel_order(cancel_req)
    engine.subscribe(sub_req)

    assert vt_orderid == "CTPTEST.123"
    assert "CTPTEST.123" in engine.session_order_ids
    assert main_engine.calls == [
        ("send_order", order_req, "CTPTEST"),
        ("cancel_order", cancel_req, "CTPTEST"),
        ("subscribe", sub_req, "CTPTEST"),
    ]


def test_case_registry_contains_existing_cases():
    """测试用例注册表应该保留原有 case_id。"""
    from src.domain.cases.registry import CASE_MAP

    assert "2.1.1.1" in CASE_MAP
    assert "2.1.1.2" in CASE_MAP
    assert "2.6.1" in CASE_MAP
    assert callable(CASE_MAP["2.1.1.1"])
    assert callable(CASE_MAP["2.1.1.2"])


def test_test_engine_blocks_gateway_calls_when_disconnected(monkeypatch):
    """断连后测试引擎不应继续向 MainEngine 转发交易接口调用。"""
    from vnpy.event import EventEngine
    from vnpy.trader.constant import Direction, Exchange, Offset, OrderType
    from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

    from src.domain.engine import TestEngine

    class FakeMainEngine:
        """记录断连状态下的主引擎调用。"""

        def __init__(self):
            """初始化网关和调用记录。"""
            self.gateways = {}
            self.calls = []

        def get_gateway(self, gateway_name):
            """按名称读取网关。"""
            self.calls.append(("get_gateway", gateway_name))
            return self.gateways.get(gateway_name)

        def send_order(self, req, gateway_name):
            """记录不应出现的发单调用。"""
            self.calls.append(("send_order", req, gateway_name))
            return "123"

        def cancel_order(self, req, gateway_name):
            """记录不应出现的撤单调用。"""
            self.calls.append(("cancel_order", req, gateway_name))

        def subscribe(self, req, gateway_name):
            """记录不应出现的订阅调用。"""
            self.calls.append(("subscribe", req, gateway_name))

    main_engine = FakeMainEngine()
    engine = TestEngine(main_engine, EventEngine())
    monkeypatch.setattr(engine.risk_manager, "check_order", lambda req: True)
    monkeypatch.setattr(engine.risk_manager, "check_cancel", lambda req: True)

    order_req = OrderRequest(
        symbol="IF2406",
        exchange=Exchange.CFFEX,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=1,
        price=100,
        offset=Offset.OPEN,
    )
    cancel_req = CancelRequest(orderid="123", symbol="IF2406", exchange=Exchange.CFFEX)
    sub_req = SubscribeRequest(symbol="IF2406", exchange=Exchange.CFFEX)

    assert engine.is_gateway_ready() is False
    assert engine.send_order(order_req) == ""
    assert engine.cancel_order(cancel_req) is False
    assert engine.subscribe(sub_req) is False
    assert [call[0] for call in main_engine.calls] == ["get_gateway", "get_gateway", "get_gateway", "get_gateway"]


def test_index_has_split_connectivity_buttons():
    """页面应展示正常和异常两类接口适应性测试按钮。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (root / "src/app/web/templates/index.html").read_text(encoding="utf-8")

    assert "runTest('2.1.1.1')" in text
    assert "runTest('2.1.1.2')" in text
    assert "正常连接适应性" in text
    assert "异常连接适应性" in text


def test_run_bat_uses_existing_web_entry():
    """启动脚本应该调用当前存在的 Web 入口。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = root / "run.bat"
    text = script.read_text(encoding="utf-8").replace("\\", "/")

    assert "src/web/app.py" not in text
    assert "src/app/web/main.py" in text
    assert (root / "src/app/web/main.py").is_file()


def test_run_bat_is_cmd_compatible():
    """启动脚本应该使用 cmd 兼容的 ASCII 和 CRLF 格式。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    data = (root / "run.bat").read_bytes()

    assert data.decode("ascii")
    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")

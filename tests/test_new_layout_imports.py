"""验证重构后的包结构。"""


def test_new_layout_imports():
    """新目录中的核心模块应该可以导入。"""
    from src.app.web.factory import create_app
    from src.app.worker.controller import WorkerController
    from src.config import settings
    from src.domain.engine import TestEngine
    from src.infra.rpc.client import RpcClient

    assert create_app
    assert WorkerController
    assert settings.RPC_HOST
    assert TestEngine
    assert RpcClient


def test_case_registry_contains_existing_cases():
    """测试用例注册表应该保留原有 case_id。"""
    from src.domain.cases.registry import CASE_MAP

    assert "2.1.1" in CASE_MAP
    assert "2.6.1" in CASE_MAP
    assert callable(CASE_MAP["2.1.1"])


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

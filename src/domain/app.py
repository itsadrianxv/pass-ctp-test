"""vn.py 测试应用壳。"""

from pathlib import Path

import src.infra.path_setup  # noqa: F401
from vnpy.trader.app import BaseApp

from src.domain.engine import TestEngine


class TestApp(BaseApp):
    """注册测试 function engine 的 vn.py App。"""

    app_name = "TestApp"
    app_module = "src.domain"
    app_path = Path(__file__).resolve().parent
    display_name = "测试引擎"
    engine_class = TestEngine
    widget_name = ""
    icon_name = ""

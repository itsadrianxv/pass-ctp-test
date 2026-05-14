"""业务域包入口。"""

__all__ = ["TestEngine", "TestRiskManager"]


def __getattr__(name: str):
    """按需导出业务域对象。"""
    if name == "TestEngine":
        from src.domain.engine import TestEngine

        return TestEngine
    if name == "TestRiskManager":
        from src.domain.risk import TestRiskManager

        return TestRiskManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

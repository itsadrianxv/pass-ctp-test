"""测试用例包入口。"""

__all__ = [
    "CASE_MAP",
    "case_2_1",
    "case_2_2",
    "case_2_3",
    "case_2_4",
    "case_2_5",
    "case_2_6",
    "check_contract",
    "clean_environment",
    "wait_for_reaction",
]


def __getattr__(name: str):
    """按需导出测试用例和助手。"""
    if name == "CASE_MAP":
        from src.domain.cases.registry import CASE_MAP

        return CASE_MAP
    if name in {"case_2_1", "case_2_2", "case_2_3", "case_2_4", "case_2_5", "case_2_6"}:
        import importlib

        return importlib.import_module(f"src.domain.cases.{name}")
    if name in {"check_contract", "clean_environment", "wait_for_reaction"}:
        from src.domain.cases import helpers

        return getattr(helpers, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

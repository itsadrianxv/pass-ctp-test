"""基础设施包入口。"""

__all__ = ["CommandServer", "ProcessManager", "RpcClient"]


def __getattr__(name: str):
    """按需导出基础设施组件。"""
    if name == "CommandServer":
        from src.infra.rpc.server import CommandServer

        return CommandServer
    if name == "ProcessManager":
        from src.infra.process import ProcessManager

        return ProcessManager
    if name == "RpcClient":
        from src.infra.rpc.client import RpcClient

        return RpcClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

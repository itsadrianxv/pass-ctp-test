"""Worker 应用包入口。"""

__all__ = ["WorkerController", "WorkerNotifier", "main"]


def __getattr__(name: str):
    """按需导出 Worker 组件。"""
    if name == "WorkerController":
        from src.app.worker.controller import WorkerController

        return WorkerController
    if name == "WorkerNotifier":
        from src.app.worker.notifier import WorkerNotifier

        return WorkerNotifier
    if name == "main":
        from src.app.worker.main import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

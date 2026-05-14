"""Web 应用包入口。"""

__all__ = [
    "allow_unsafe_werkzeug",
    "create_app",
    "load_socketio_cors_allowed_origins",
]


def __getattr__(name: str):
    """按需导出 Web 工厂函数。"""
    if name in __all__:
        from src.app.web import factory

        return getattr(factory, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

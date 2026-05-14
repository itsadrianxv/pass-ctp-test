"""Flask 和 SocketIO 应用工厂。"""

import logging
import os

import engineio
from flask import Flask
from flask_socketio import SocketIO

from src.app.web import events, routes_auth, routes_case, routes_risk, routes_worker
from src.config import settings as config
from src.infra.logging import setup_logger
from src.infra.logging.handlers import SocketIOHandler


engineio.payload.Payload.max_decode_packets = 100


def load_socketio_cors_allowed_origins():
    """读取 SocketIO 的跨域白名单。"""
    raw_value = os.environ.get("WEB_CORS_ALLOWED_ORIGINS", "").strip()
    if not raw_value:
        return None
    if raw_value == "*":
        return "*"
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def allow_unsafe_werkzeug() -> bool:
    """读取本地启动时是否允许 Werkzeug。"""
    raw_value = os.environ.get("WEB_ALLOW_UNSAFE_WERKZEUG", "true").strip().lower()
    return raw_value not in {"0", "false", "no", "off"}


def create_app() -> tuple[Flask, SocketIO]:
    """创建 Web 应用和 SocketIO。"""
    template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "templates"))
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.update(
        SECRET_KEY=config.get_web_secret_key(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("WEB_SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
        TEMPLATES_AUTO_RELOAD=True,
        SEND_FILE_MAX_AGE_DEFAULT=0,
    )
    app.jinja_env.auto_reload = True

    socketio = SocketIO(app, cors_allowed_origins=load_socketio_cors_allowed_origins(), async_mode="threading")
    setup_logger()

    root_logger = logging.getLogger()
    if not any(isinstance(h, SocketIOHandler) for h in root_logger.handlers):
        socket_handler = SocketIOHandler(socketio)
        socket_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        root_logger.addHandler(socket_handler)

    events.register_events(socketio)
    routes_auth.register_routes(app)
    routes_case.register_routes(app)
    routes_risk.register_routes(app)
    routes_worker.register_routes(app)
    return app, socketio

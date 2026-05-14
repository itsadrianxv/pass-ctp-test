"""Web 进程入口。"""

import os

from src.app.web.factory import allow_unsafe_werkzeug, create_app


app, socketio = create_app()


def main() -> None:
    """启动 Web 服务。"""
    web_host = os.environ.get("WEB_HOST", "127.0.0.1").strip() or "127.0.0.1"
    web_port = int(os.environ.get("WEB_PORT", "5006"))
    socketio.run(
        app,
        host=web_host,
        port=web_port,
        debug=False,
        allow_unsafe_werkzeug=allow_unsafe_werkzeug(),
    )


if __name__ == "__main__":
    main()

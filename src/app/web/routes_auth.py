"""登录和页面路由。"""

from flask import jsonify, redirect, render_template, request, session, url_for

from src.app.web.state import log, process_manager
from src.config import settings as config
from src.config.env import load_env, save_env


def get_masked_env() -> dict:
    """读取页面展示配置。"""
    env_vars = load_env(config.ENV_PATH)
    return {
        "CTP_NAME": env_vars.get("CTP_NAME", "Unknown"),
        "CTP_USERNAME": env_vars.get("CTP_USERNAME", ""),
        "CTP_TD_SERVER": env_vars.get("CTP_TD_SERVER", ""),
        "CTP_MD_SERVER": env_vars.get("CTP_MD_SERVER", ""),
    }


def _is_logged_in() -> bool:
    """判断用户是否登录。"""
    return bool(session.get("logged_in"))


def _form_value(name: str) -> str:
    """读取表单字段。"""
    return str(request.form.get(name, "") or "").strip()


def register_routes(app) -> None:
    """注册登录和首页路由。"""

    @app.before_request
    def _require_login():
        """校验页面和 API 登录状态。"""
        if request.endpoint in {"login", "static"}:
            return None
        if request.path.startswith("/socket.io/"):
            return None
        if _is_logged_in():
            return None
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "msg": "authentication_required"}), 401
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """处理登录配置页面。"""
        if request.method == "POST":
            data = {
                "CTP_NAME": _form_value("CTP_NAME"),
                "CTP_USERNAME": _form_value("CTP_USERNAME"),
                "CTP_PASSWORD": _form_value("CTP_PASSWORD"),
                "CTP_BROKER_ID": _form_value("CTP_BROKER_ID"),
                "CTP_TD_SERVER": _form_value("CTP_TD_SERVER"),
                "CTP_MD_SERVER": _form_value("CTP_MD_SERVER"),
                "APPID": _form_value("APPID"),
                "CTP_AUTH_CODE": _form_value("CTP_AUTH_CODE"),
                "CTP_PRODUCT_INFO": _form_value("CTP_PRODUCT_INFO"),
            }

            try:
                save_env(config.ENV_PATH, data)
            except ValueError as exc:
                log.warning("Rejected invalid login payload: %s", exc)
                return render_template("login.html", env=data, error=str(exc)), 400

            session.clear()
            session["logged_in"] = True

            if process_manager.is_running():
                process_manager.restart_worker()
            else:
                process_manager.start_worker(force=True)

            return redirect(url_for("index"))

        env_vars = load_env(config.ENV_PATH)
        return render_template("login.html", env=env_vars)

    @app.route("/")
    def index():
        """渲染首页。"""
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return render_template("index.html", env=get_masked_env())

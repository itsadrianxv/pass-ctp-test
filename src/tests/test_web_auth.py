import importlib
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.config import reader as config_reader
import src.logging as logging_module
import src.web.process_manager as process_manager_module
import src.web.rpc_client as rpc_client_module


def _load_app_module():
    sys.modules.pop("src.web.app", None)

    with (
        patch.object(config_reader, "get_web_secret_key", return_value="test-secret"),
        patch.object(logging_module, "setup_logger"),
        patch.object(process_manager_module, "ProcessManager", return_value=MagicMock()),
        patch.object(rpc_client_module, "RpcClient", return_value=MagicMock()),
    ):
        return importlib.import_module("src.web.app")


class WebAuthTests(unittest.TestCase):
    def test_dashboard_route_uses_trimmed_template(self):
        """首页路由渲染时不应再带被删掉的辅助块。"""
        app_module = _load_app_module()
        client = app_module.app.test_client()

        with client.session_transaction() as flask_session:
            flask_session["logged_in"] = True

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("CTP 穿透测试", html)
        self.assertIn("执行日志", html)
        self.assertIn('id="mobile-rail-toggle"', html)
        self.assertNotIn("CTP WORKSPACE", html)
        self.assertNotIn("主工作区", html)
        self.assertNotIn("主终端", html)
        self.assertNotIn("最近状态", html)
        self.assertNotIn("socket-state", html)
        self.assertNotIn("worker-state", html)
        self.assertNotIn("执行与追踪", html)
        self.assertNotIn("workspace-copy", html)
        self.assertNotIn("workspace-top", html)

    def test_web_app_disables_template_and_static_cache(self):
        """本地页面样式改动后应尽快看到最新内容。"""
        app_module = _load_app_module()

        self.assertTrue(app_module.app.config["TEMPLATES_AUTO_RELOAD"])
        self.assertEqual(app_module.app.config["SEND_FILE_MAX_AGE_DEFAULT"], 0)

    def test_api_requires_login(self):
        app_module = _load_app_module()
        client = app_module.app.test_client()

        response = client.post("/api/worker/kill")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"status": "error", "msg": "authentication_required"})

    def test_logged_in_session_can_access_protected_api(self):
        app_module = _load_app_module()
        client = app_module.app.test_client()

        with client.session_transaction() as flask_session:
            flask_session["logged_in"] = True

        response = client.post("/api/worker/kill")

        self.assertEqual(response.status_code, 200)

    def test_worker_status_returns_json_when_rpc_times_out(self):
        app_module = _load_app_module()
        app_module.rpc.request.side_effect = TimeoutError("timed out")
        client = app_module.app.test_client()

        with client.session_transaction() as flask_session:
            flask_session["logged_in"] = True

        response = client.get("/api/worker/status")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {"status": "error", "msg": "Worker RPC 请求超时，请稍后重试"},
        )

    def test_allow_unsafe_werkzeug_defaults_true(self):
        """本地直接启动时默认允许 Werkzeug。"""
        app_module = _load_app_module()

        self.assertTrue(app_module._allow_unsafe_werkzeug())

    def test_allow_unsafe_werkzeug_can_be_disabled(self):
        """需要时可通过环境变量关闭 Werkzeug 放行。"""
        app_module = _load_app_module()

        with patch.dict("os.environ", {"WEB_ALLOW_UNSAFE_WERKZEUG": "false"}):
            self.assertFalse(app_module._allow_unsafe_werkzeug())


if __name__ == "__main__":
    unittest.main()

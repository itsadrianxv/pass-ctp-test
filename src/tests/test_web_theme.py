"""Web 主题与布局静态测试。"""

from pathlib import Path
import unittest


CSS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "css" / "style.css"
INDEX_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "web" / "templates" / "index.html"
LOGIN_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "web" / "templates" / "login.html"


class WebThemeTests(unittest.TestCase):
    """校验控制台与登录页的主题和布局契约。"""

    @classmethod
    def setUpClass(cls):
        cls.css = CSS_PATH.read_text(encoding="utf-8")
        cls.index_html = INDEX_TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.login_html = LOGIN_TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_dual_theme_tokens_are_defined(self):
        """应定义浅色与深色双主题令牌。"""
        expected_tokens = {
            "--bg": "#eef3f8",
            "--surface": "#f8fbff",
            "--surface-subtle": "#eef4fb",
            "--log-surface": "#f3f7fc",
            "--log-text": "#112031",
            "--log-muted": "#526273",
            "--border": "rgba(133, 158, 186, 0.28)",
            "--text": "#102033",
            "--text-muted": "#5f7085",
            "--accent": "#2f6fed",
            "--accent-strong": "#1f5ad0",
            "--success": "#167d54",
            "--warning": "#b87416",
            "--danger": "#c74b4b",
            "--focus-ring": "color-mix(in srgb, var(--accent) 18%, transparent)",
            "--font-display": '"Microsoft YaHei UI", "Segoe UI", sans-serif',
        }

        for token_name, token_value in expected_tokens.items():
            self.assertIn(f"{token_name}: {token_value};", self.css)

        self.assertIn('[data-bs-theme="dark"] {', self.css)
        self.assertIn("--bg: #111822;", self.css)
        self.assertIn("--log-surface: #151e2b;", self.css)
        self.assertIn("--log-text: #e4edf7;", self.css)

    def test_legacy_warm_palette_is_removed(self):
        """旧暖色调不应残留。"""
        legacy_tokens = [
            "#171411",
            "#211d19",
            "#2a241f",
            "#12100e",
            "#433b33",
            "#f4eee6",
            "#b5a99b",
            "#d49a6a",
            "#eab583",
            "#8faa8a",
            "#d3a15d",
            "#cf7b6a",
            "rgba(212, 154, 106",
            "rgba(234, 181, 131",
            "rgba(87, 67, 52",
            "rgba(207, 123, 106",
            "rgba(143, 170, 138",
            "Georgia",
        ]

        for legacy_token in legacy_tokens:
            self.assertNotIn(legacy_token, self.css)

    def test_key_surfaces_follow_new_terminal_rules(self):
        """核心界面应使用新主题和新布局规则。"""
        expectations = [
            ":root {\n    color-scheme: light;",
            '[data-bs-theme="dark"] {\n    color-scheme: dark;',
            ".workspace-grid {\n    display: grid;\n    grid-template-columns: 416px minmax(0, 1fr);",
            '.workspace-grid[data-rail-state="collapsed"] {\n    grid-template-columns: 84px minmax(0, 1fr);',
            "height: calc(100vh - 48px);",
            ".ops-rail {\n    position: sticky;\n    top: 24px;\n    height: 100%;",
            ".rail-scroll {\n    display: grid;\n    grid-template-columns: minmax(0, 3fr) minmax(0, 1fr);\n    gap: 12px;\n    min-height: 0;\n    overflow: hidden;",
            ".rail-tests {\n    grid-column: 1 / -1;",
            ".action-stack {\n    display: grid;\n    grid-template-columns: repeat(2, minmax(0, 1fr));",
            ".terminal-workspace {\n    min-width: 0;\n    height: 100%;\n    min-height: 0;\n    display: flex;\n    flex-direction: column;",
            "#log-container {\n    flex: 1;\n    min-height: 0;\n    background:\n        linear-gradient(180deg, color-mix(in srgb, var(--log-surface) 82%, transparent), var(--log-surface)),",
        ]

        for expected_snippet in expectations:
            self.assertIn(expected_snippet, self.css)

    def test_templates_use_runtime_theme_hook(self):
        """模板应改为运行时写入 Bootstrap 主题。"""
        self.assertIn("<html lang=\"zh-CN\">", self.index_html)
        self.assertIn("<html lang=\"zh-CN\">", self.login_html)
        self.assertIn("window.__ctpTheme = {", self.index_html)
        self.assertIn("window.__ctpTheme = {", self.login_html)
        self.assertIn("document.documentElement.setAttribute('data-bs-theme', nextTheme);", self.index_html)
        self.assertIn("document.documentElement.setAttribute('data-bs-theme', nextTheme);", self.login_html)

    def test_dashboard_template_supports_collapsible_rail(self):
        """控制台模板应支持侧栏收起。"""
        self.assertIn('class="workspace-grid" data-rail-state="expanded"', self.index_html)
        self.assertIn('class="rail-toggle"', self.index_html)
        self.assertIn("const railStorageKey = 'ctp_workspace_rail_state';", self.index_html)
        self.assertIn("function applyRailState(nextState)", self.index_html)
        self.assertIn("localStorage.setItem(railStorageKey, safeState);", self.index_html)

    def test_dashboard_sidebar_aligns_title_and_balances_info_space(self):
        """侧栏标题应与收起按钮同排，信息区应为左宽右窄。"""
        rail_head = """<div class="rail-head">
                    <div class="brand-block">
                        <h1>CTP 穿透测试</h1>
                    </div>
                    <button id="rail-toggle\""""
        self.assertIn(rail_head, self.index_html)
        self.assertIn(
            ".rail-scroll {\n    display: grid;\n    grid-template-columns: minmax(0, 3fr) minmax(0, 1fr);",
            self.css,
        )
        self.assertIn(
            ".info-row,\n.metric-row {\n    display: flex;\n    justify-content: space-between;\n    gap: 12px;\n    align-items: flex-start;",
            self.css,
        )
        self.assertIn(
            ".info-value {\n    flex: 1 1 auto;\n    min-width: 0;\n    max-width: none;",
            self.css,
        )
        self.assertIn("white-space: normal;", self.css)
        self.assertIn("overflow-wrap: anywhere;", self.css)

    def test_dashboard_template_removes_marked_auxiliary_blocks(self):
        """首页应移除被标记的辅助信息块。"""
        removed_snippets = [
            '<div class="brand-mark" aria-hidden="true">CTP</div>',
            '<p class="eyebrow">CTP Workspace</p>',
            "把环境、统计、动作与日志拉回同一条工作流里",
            '<p class="panel-kicker">当前环境</p>',
            '<p class="panel-kicker">实时统计</p>',
            '<p class="panel-kicker">测试入口</p>',
            '<p class="eyebrow">主工作区</p>',
            '<section class="status-bar" aria-label="运行状态">',
            '<p class="panel-kicker">主终端</p>',
            '<div class="terminal-meta">',
            '<section class="workspace-top">',
            '<div class="workspace-copy">',
            "<h2>执行与追踪</h2>",
        ]

        for snippet in removed_snippets:
            self.assertNotIn(snippet, self.index_html)

    def test_login_template_removes_marked_auxiliary_copy(self):
        """登录页应移除指定的辅助文案。"""
        removed_snippets = [
            "CTP Workspace",
            '<p class="eyebrow">CTP Workspace</p>',
            "给交易员和开发运维一套同样轻、稳、顺手的接入界面。字段、接口和后端流程不变，只把信息关系梳理得更清楚。",
            "<h3>账户凭证</h3>",
            "公司名称、BrokerID、账号与密码放在一起，减少来回核对。",
            "<h3>连接地址</h3>",
            "长地址保持单列展示，读写更稳，不容易截断看错。",
            "<h3>应用认证</h3>",
            "AppID、授权码和产品信息沿用原字段，便于重复回填。",
            '<p class="section-kicker">接入参数</p>',
            "<code>POST /login</code> 与全部原有表单 <code>name</code> 字段保持不变。",
            "短字段双列，优先照顾快速录入和核对。",
            "服务器地址保持单列，避免长串地址挤成一团。",
            "保留原字段语义与必填校验，减少切换成本。",
            "登录后沿用现有 worker 重启与配置回填流程。",
        ]

        for snippet in removed_snippets:
            self.assertNotIn(snippet, self.login_html)

    def test_login_template_uses_access_title_as_only_main_panel(self):
        """登录页应只保留接入表单主面板。"""
        self.assertIn("<h2>CTP 穿透测试接入</h2>", self.login_html)
        self.assertNotIn("<h2>登录与连接</h2>", self.login_html)
        self.assertNotIn('class="login-side"', self.login_html)
        self.assertNotIn('class="login-brand"', self.login_html)
        self.assertIn(
            ".login-layout {\n"
            "    position: relative;\n"
            "    z-index: 1;\n"
            "    width: min(1160px, 100%);\n"
            "    display: grid;\n"
            "    grid-template-columns: minmax(0, 1fr);",
            self.css,
        )
        self.assertNotIn("grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);", self.css)
        self.assertNotIn(".login-side,", self.css)

    def test_light_theme_log_area_is_not_dark_only(self):
        """浅色主题的日志区不应继续写死深色。"""
        self.assertNotIn("--log-bg: #0B1220;", self.css)
        self.assertNotIn(
            "background:\n        radial-gradient(circle at top center, rgba(37, 99, 235, 0.12), transparent 34%),\n        var(--log-bg);",
            self.css,
        )


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


CSS_PATH = Path(__file__).resolve().parents[1] / "web" / "static" / "css" / "style.css"
INDEX_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "web" / "templates" / "index.html"
LOGIN_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "web" / "templates" / "login.html"


class WebThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS_PATH.read_text(encoding="utf-8")
        cls.index_html = INDEX_TEMPLATE_PATH.read_text(encoding="utf-8")
        cls.login_html = LOGIN_TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_fintech_palette_tokens_are_defined(self):
        expected_tokens = {
            "--bg": "#F5F7FB",
            "--surface": "#FFFFFF",
            "--surface-2": "#F8FAFC",
            "--log-bg": "#0B1220",
            "--border": "#E2E8F0",
            "--text": "#0F172A",
            "--text-muted": "#667085",
            "--accent": "#2563EB",
            "--accent-strong": "#1D4ED8",
            "--success": "#12B76A",
            "--warning": "#F79009",
            "--danger": "#F04438",
            "--focus-ring": "rgba(37, 99, 235, 0.18)",
            "--font-display": '"Microsoft YaHei UI", "Segoe UI", sans-serif',
        }

        for token_name, token_value in expected_tokens.items():
            self.assertIn(f"{token_name}: {token_value};", self.css)

    def test_legacy_warm_palette_is_removed(self):
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

    def test_key_surfaces_follow_light_saas_rules(self):
        expectations = [
            ".form-control,\n.form-select {\n    min-height: 48px;\n    border-radius: var(--radius-control);\n    border: 1px solid var(--border);\n    background: var(--surface);",
            ".accordion-button:not(.collapsed) {\n    background: var(--surface-hover);",
            ".btn-outline-secondary {\n    background: rgba(37, 99, 235, 0.08);",
            ".status-chip {\n    min-width: 118px;\n    display: grid;\n    gap: 4px;\n    padding: 10px 12px;\n    border: 1px solid var(--border);\n    border-radius: var(--radius-control);\n    background: var(--surface-2);",
            "#log-container {\n    flex: 1;\n    min-height: 0;\n    background:\n        radial-gradient(circle at top center, rgba(37, 99, 235, 0.12), transparent 34%),\n        var(--log-bg);",
        ]

        for expected_snippet in expectations:
            self.assertIn(expected_snippet, self.css)

    def test_templates_opt_into_light_bootstrap_theme(self):
        self.assertIn('<html lang="zh-CN" data-bs-theme="light">', self.index_html)
        self.assertIn('<html lang="zh-CN" data-bs-theme="light">', self.login_html)
        self.assertNotIn("暗色", self.index_html)
        self.assertNotIn("暗色", self.login_html)


if __name__ == "__main__":
    unittest.main()

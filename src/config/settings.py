"""应用运行配置。"""

import os
import secrets

from src.config.env import load_env, save_env
from src.config.yaml import load_yaml_config, save_yaml_config


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
CONFIG_YAML_PATH = os.path.join(PROJECT_ROOT, "config.yaml")

ENV_VARS = load_env(ENV_PATH)
YAML_CONFIG = load_yaml_config(CONFIG_YAML_PATH)


def get_web_secret_key(env_path: str | None = None) -> str:
    """读取或生成 Web 会话密钥。"""
    env_path = env_path or ENV_PATH
    env_vars = load_env(env_path)
    secret_key = env_vars.get("WEB_SECRET_KEY") or os.environ.get("WEB_SECRET_KEY")
    if secret_key:
        return secret_key

    secret_key = secrets.token_hex(32)
    save_env(env_path, {"WEB_SECRET_KEY": secret_key})
    ENV_VARS["WEB_SECRET_KEY"] = secret_key
    return secret_key


CTP_NAME = ENV_VARS.get("CTP_NAME", "Unknown")
CTP_USERNAME = ENV_VARS.get("CTP_USERNAME", "")
CTP_BROKER_ID = ENV_VARS.get("CTP_BROKER_ID", "")
CTP_TD_SERVER = ENV_VARS.get("CTP_TD_SERVER", "")
CTP_APP_ID = ENV_VARS.get("APPID", "")
CTP_AUTH_CODE = ENV_VARS.get("CTP_AUTH_CODE", "")
ATOMIC_WAIT_SECONDS = 7
RPC_PORT = 9999
RPC_HOST = "127.0.0.1"

CTP_SETTING = {
    "用户名": CTP_USERNAME,
    "密码": ENV_VARS.get("CTP_PASSWORD", ""),
    "经纪商代码": CTP_BROKER_ID,
    "交易服务器": CTP_TD_SERVER,
    "行情服务器": ENV_VARS.get("CTP_MD_SERVER", ""),
    "产品名称": CTP_APP_ID,
    "授权编码": CTP_AUTH_CODE,
    "产品信息": ENV_VARS.get("CTP_PRODUCT_INFO", ""),
}

TEST_SYMBOL = YAML_CONFIG.get("test_symbol", "IF2602")
SAFE_BUY_PRICE = float(YAML_CONFIG.get("safe_buy_price", 4700.0))
DEAL_BUY_PRICE = float(YAML_CONFIG.get("deal_buy_price", 4800.0))
REPEAT_OPEN_THRESHOLD = int(YAML_CONFIG.get("repeat_open_threshold", 2) or 2)
REPEAT_CLOSE_THRESHOLD = int(YAML_CONFIG.get("repeat_close_threshold", 2) or 2)
VOLUME_LIMIT_VOLUME = int(YAML_CONFIG.get("volume_limit_volume", 10000) or 10000)
ORDER_MONITOR_THRESHOLD = int(YAML_CONFIG.get("order_monitor_threshold", 1) or 1)
CANCEL_MONITOR_THRESHOLD = int(YAML_CONFIG.get("cancel_monitor_threshold", 1) or 1)

REST_TEST_SYMBOL = YAML_CONFIG.get("rest_test_symbol", "LC2607")
REST_TEST_PRICE = float(YAML_CONFIG.get("rest_test_price", 168220))

RISK_THRESHOLDS = YAML_CONFIG.get(
    "risk_thresholds",
    {
        "max_order_count": 5,
        "max_cancel_count": 5,
        "max_symbol_order_count": 2,
    },
)

__all__ = [
    "ATOMIC_WAIT_SECONDS",
    "CANCEL_MONITOR_THRESHOLD",
    "CONFIG_YAML_PATH",
    "CTP_APP_ID",
    "CTP_AUTH_CODE",
    "CTP_BROKER_ID",
    "CTP_NAME",
    "CTP_SETTING",
    "CTP_TD_SERVER",
    "CTP_USERNAME",
    "DEAL_BUY_PRICE",
    "ENV_PATH",
    "ENV_VARS",
    "ORDER_MONITOR_THRESHOLD",
    "PROJECT_ROOT",
    "REPEAT_CLOSE_THRESHOLD",
    "REPEAT_OPEN_THRESHOLD",
    "REST_TEST_PRICE",
    "REST_TEST_SYMBOL",
    "RISK_THRESHOLDS",
    "RPC_HOST",
    "RPC_PORT",
    "SAFE_BUY_PRICE",
    "TEST_SYMBOL",
    "VOLUME_LIMIT_VOLUME",
    "YAML_CONFIG",
    "get_web_secret_key",
    "load_env",
    "load_yaml_config",
    "save_env",
    "save_yaml_config",
]

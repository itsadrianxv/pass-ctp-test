import os
import re
import secrets
import tempfile
from typing import Any, Dict

import yaml


_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env(env_path: str) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}
    if not os.path.exists(env_path):
        return env_vars

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}


def _normalize_env_key(key: str) -> str:
    key_text = str(key or "").strip()
    if not _ENV_KEY_RE.fullmatch(key_text):
        raise ValueError(f"invalid env key: {key!r}")
    return key_text


def _normalize_env_value(value: Any) -> str:
    value_text = "" if value is None else str(value)
    if "\r" in value_text or "\n" in value_text:
        raise ValueError("env values must not contain line breaks")
    return value_text


def _atomic_write_text(path: str, content: str) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
CONFIG_YAML_PATH = os.path.join(PROJECT_ROOT, "config.yaml")


ENV_VARS = load_env(ENV_PATH)
YAML_CONFIG = load_yaml_config(CONFIG_YAML_PATH)


def save_env(env_path: str, data: Dict[str, Any]) -> None:
    normalized_data = {
        _normalize_env_key(key): _normalize_env_value(value)
        for key, value in data.items()
    }

    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    processed_keys = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" in line:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key in normalized_data:
                new_lines.append(f"{key}={normalized_data[key]}\n")
                processed_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    for key, value in normalized_data.items():
        if key not in processed_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={value}\n")

    _atomic_write_text(env_path, "".join(new_lines))


def save_yaml_config(config_path: str, data: Dict[str, Any]) -> None:
    current_config = load_yaml_config(config_path)
    current_config.update(data)

    serialized = yaml.safe_dump(current_config, allow_unicode=True, default_flow_style=False)
    _atomic_write_text(config_path, serialized)


def get_web_secret_key(env_path: str | None = None) -> str:
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

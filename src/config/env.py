"""环境变量文件读写。"""

import os
import re
import tempfile
from typing import Any, Dict


ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env(env_path: str) -> Dict[str, str]:
    """读取 .env 文件。"""
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


def normalize_key(key: str) -> str:
    """校验并规范环境变量名。"""
    key_text = str(key or "").strip()
    if not ENV_KEY_RE.fullmatch(key_text):
        raise ValueError(f"invalid env key: {key!r}")
    return key_text


def normalize_value(value: Any) -> str:
    """校验并规范环境变量值。"""
    value_text = "" if value is None else str(value)
    if "\r" in value_text or "\n" in value_text:
        raise ValueError("env values must not contain line breaks")
    return value_text


def atomic_write_text(path: str, content: str) -> None:
    """原子写入文本文件。"""
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


def save_env(env_path: str, data: Dict[str, Any]) -> None:
    """保存 .env 文件。"""
    normalized_data = {
        normalize_key(key): normalize_value(value)
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

    atomic_write_text(env_path, "".join(new_lines))

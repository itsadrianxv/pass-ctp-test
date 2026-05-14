"""YAML 配置读写。"""

from typing import Any, Dict

import os
import yaml

from src.config.env import atomic_write_text


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """读取 YAML 配置。"""
    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}


def save_yaml_config(config_path: str, data: Dict[str, Any]) -> None:
    """合并保存 YAML 配置。"""
    current_config = load_yaml_config(config_path)
    current_config.update(data)

    serialized = yaml.safe_dump(current_config, allow_unicode=True, default_flow_style=False)
    atomic_write_text(config_path, serialized)

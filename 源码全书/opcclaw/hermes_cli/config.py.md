# `opcclaw/hermes_cli/config.py`

> 路径：`opcclaw/hermes_cli/config.py` | 行数：65


---


```python
#!/usr/bin/env python3
"""
hermes_cli.config — OPCclaw 兼容存根
"""

import os
import sys


HERMES_CONFIG_DIRS = [".hermes", "~/.hermes", "~/.config/hermes"]


def _resolve_path(path: str) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def get_hermes_home() -> str:
    """获取 Hermes 主配置目录，可被 HERMES_HOME 环境变量覆盖。"""
    env = os.environ.get("HERMES_HOME")
    if env:
        return _resolve_path(env)
    for candidate in HERMES_CONFIG_DIRS:
        full = _resolve_path(candidate)
        if os.path.isdir(full):
            return full
    return _resolve_path("~/.hermes")


def get_env_value(key: str, default=None):
    """从环境变量获取值，支持嵌套键（如 HERMES_LLM_PROVIDER）。"""
    env_key = key.replace(".", "_").upper()
    return os.environ.get(env_key, default)


def load_config(config_path: str = None):
    """加载配置：先从内置默认值开始，再合并 YAML 配置文件（可选）。"""
    defaults = {
        "security.allow_private_urls": False,
        "security.website_blocklist_enabled": False,
        "llm.default_provider": "openai",
    }

    if config_path is None:
        config_path = os.path.join(get_hermes_home(), "config.yaml")

    resolved = _resolve_path(config_path)
    if os.path.isfile(resolved):
        try:
            import yaml
            with open(resolved, "r", encoding="utf-8") as f:
                file_cfg = yaml.safe_load(f) or {}
            defaults.update(file_cfg)
        except Exception:
            pass

    return defaults


def cfg_get(key: str, default=None):
    """获取配置值。先从环境变量，再从配置文件。"""
    env_val = get_env_value(key)
    if env_val is not None:
        return env_val
    _config_cache = load_config()
    return _config_cache.get(key, default)

```

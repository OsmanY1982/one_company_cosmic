#!/usr/bin/env python3
"""
utils — Iqra 兼容存根
"""

import os

def is_truthy_value(value) -> bool:
    """判断值是否为真值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)


def atomic_replace(src: str, dst: str):
    """原子替换文件：将 src 移动到 dst，跨文件系统也安全。"""
    try:
        os.replace(src, dst)
    except OSError:
        # 跨文件系统回退：复制后删除
        import shutil
        shutil.copy2(src, dst)
        os.unlink(src)


def atomic_json_write(filepath: str, data, indent: int = 2):
    """原子写入 JSON 文件：先写临时文件，再原子重命名。"""
    import json
    import tempfile

    dirname = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(dirname, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=dirname)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def base_url_host_matches(base_url: str, host: str) -> bool:
    """检查 base_url 的 host 是否与给定 host 一致。"""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(base_url)
        return parsed.hostname == host
    except Exception:
        return False


def base_url_hostname(base_url: str) -> str:
    """从 base_url 提取 hostname。"""
    from urllib.parse import urlparse

    try:
        return urlparse(base_url).hostname or ""
    except Exception:
        return ""


def safe_json_loads(text: str):
    """安全 JSON 解析：解析失败返回空 dict。"""
    import json

    if not text or not isinstance(text, str):
        return {}
    try:
        result = json.loads(text)
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def normalize_proxy_env_vars():
    """规范化代理环境变量：统一 HTTP_PROXY / HTTPS_PROXY 大小写。"""
    for key in list(os.environ.keys()):
        lower = key.lower()
        if lower in ("http_proxy", "https_proxy", "all_proxy", "no_proxy"):
            os.environ[lower] = os.environ.pop(key)


def atomic_yaml_write(filepath: str, data, **kwargs):
    """原子写入 YAML 文件：先写临时文件，再原子重命名。"""
    import tempfile

    try:
        import yaml
    except ImportError:
        import json
        atomic_json_write(filepath, data)
        return

    dirname = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(dirname, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix=".yaml", dir=dirname)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, **kwargs)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

"""
Firecrawl 抓取缓存

基于 URL → hash 映射，缓存到 cache/firecrawl/ 目录。
TTL 默认 1 小时，可通过 FIRECRAWL_CACHE_TTL 环境变量配置。

内部函数（供 __init__.py 调用）：
  _get_cache(url) → dict | None
  _set_cache(url, content) → None
"""

import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── 缓存目录 ──
_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cache",
    "firecrawl",
)
os.makedirs(_CACHE_DIR, exist_ok=True)

# ── TTL（秒）──
_DEFAULT_TTL = 3600  # 1 小时


def _get_ttl() -> int:
    try:
        return int(os.environ.get("FIRECRAWL_CACHE_TTL", str(_DEFAULT_TTL)))
    except (ValueError, TypeError):
        return _DEFAULT_TTL


def _url_hash(url: str) -> str:
    """计算 URL 的 SHA-256 哈希，用作缓存文件名。"""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


def _cache_path(url: str) -> str:
    """返回 URL 对应的缓存文件路径。"""
    return os.path.join(_CACHE_DIR, f"{_url_hash(url)}.json")


def _get_cache(url: str) -> Optional[Dict[str, Any]]:
    """
    从缓存读取 URL 对应的内容。

    返回:
        缓存命中且未过期 → dict（含 markdown/html/title）
        缓存未命中或已过期 → None
    """
    path = _cache_path(url)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            entry: Dict[str, Any] = json.load(f)

        cached_at = entry.get("cached_at", 0)
        ttl = entry.get("ttl", _get_ttl())

        if time.time() - cached_at > ttl:
            # 过期，删除缓存文件
            try:
                os.remove(path)
            except OSError:
                pass
            return None

        return entry.get("content")

    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.debug("Firecrawl 缓存读取失败: %s", e)
        return None


def _set_cache(url: str, content: Dict[str, Any], *, ttl: Optional[int] = None) -> None:
    """
    将 URL 对应的内容写入缓存。

    参数:
        url: 原始 URL
        content: 要缓存的内容 dict（含 markdown/html/title 等）
        ttl: 可选，覆盖默认 TTL
    """
    if ttl is None:
        ttl = _get_ttl()

    path = _cache_path(url)
    entry: Dict[str, Any] = {
        "url": url,
        "cached_at": int(time.time()),
        "ttl": ttl,
        "content": content,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.debug("Firecrawl 缓存写入失败: %s", e)

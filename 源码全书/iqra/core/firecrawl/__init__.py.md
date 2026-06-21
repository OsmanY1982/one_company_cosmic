# `iqra/core/firecrawl/__init__.py`

> 路径：`iqra/core/firecrawl/__init__.py` | 行数：320


---


```python
"""
Firecrawl 网页抓取与内容转换模块

提供四个核心能力：
  scrape_url(url)          → 抓取单个网页，返回 Markdown
  crawl_site(url, max_pg)  → 爬取整个站点
  search_web(query, n)     → 搜索并抓取结果
  extract_structured(url, schema) → 按 schema 提取结构化数据

认证：环境变量 FIRECRAWL_API_KEY
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from iqra.core.firecrawl.cache import _get_cache, _set_cache
from iqra.core.firecrawl.converter import html_to_markdown

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.firecrawl.dev"


def _api_headers() -> Dict[str, str]:
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY 环境变量未设置。请在 https://firecrawl.dev 获取 API Key"
        )
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


# ─────────────────────────────────────────────
# 1. scrape_url — 抓取单个网页
# ─────────────────────────────────────────────

def scrape_url(
    url: str,
    *,
    formats: Optional[List[str]] = None,
    only_main_content: bool = True,
    wait_for: int = 0,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    抓取单个网页并返回 Markdown 格式内容。

    参数:
        url: 目标网页 URL
        formats: 输出格式列表，默认 ["markdown", "html"]
        only_main_content: 是否仅提取正文
        wait_for: 等待 JS 渲染时间（毫秒）
        use_cache: 是否使用缓存

    返回:
        {"url": str, "markdown": str, "html": str, "title": str, "cached": bool}
    """
    if formats is None:
        formats = ["markdown", "html"]

    if use_cache:
        cached = _get_cache(url)
        if cached is not None:
            cached["cached"] = True
            return cached

    headers = _api_headers()
    body: Dict[str, Any] = {
        "url": url,
        "formats": formats,
        "onlyMainContent": only_main_content,
    }
    if wait_for:
        body["waitFor"] = wait_for

    try:
        response = requests.post(
            f"{_BASE_URL}/v1/scrape",
            headers=headers,
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        result: Dict[str, Any] = {
            "url": url,
            "markdown": data.get("markdown", ""),
            "html": data.get("html", ""),
            "title": data.get("metadata", {}).get("title", ""),
            "cached": False,
        }

        if use_cache and result["markdown"]:
            _set_cache(url, result)

        return result

    except requests.exceptions.RequestException as e:
        logger.error("Firecrawl scrape_url 失败: %s", e)
        return {"error": str(e), "url": url, "markdown": "", "html": "", "title": "", "cached": False}


# ─────────────────────────────────────────────
# 2. crawl_site — 爬取整个站点
# ─────────────────────────────────────────────

def crawl_site(
    url: str,
    *,
    max_pages: int = 10,
    formats: Optional[List[str]] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    爬取整个站点，返回所有页面的 Markdown 列表。

    参数:
        url: 起始 URL
        max_pages: 最大爬取页数
        formats: 输出格式列表，默认 ["markdown"]
        use_cache: 是否使用缓存

    返回:
        {"url": str, "pages": [{"url": ..., "markdown": ..., "title": ...}], "total": int}
    """
    if formats is None:
        formats = ["markdown"]

    headers = _api_headers()
    body: Dict[str, Any] = {
        "url": url,
        "maxPages": max_pages,
        "formats": formats,
    }

    try:
        # Step 1: 创建爬取任务
        crawl_response = requests.post(
            f"{_BASE_URL}/v1/crawl",
            headers=headers,
            json=body,
            timeout=30,
        )
        crawl_response.raise_for_status()
        crawl_id = crawl_response.json().get("id", "")

        if not crawl_id:
            return {"error": "Failed to get crawl ID", "url": url, "pages": [], "total": 0}

        # Step 2: 轮询任务状态
        import time as _time
        max_wait = 300  # 最多等 5 分钟
        elapsed = 0
        interval = 3

        while elapsed < max_wait:
            status_response = requests.get(
                f"{_BASE_URL}/v1/crawl/{crawl_id}",
                headers=headers,
                timeout=30,
            )
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get("status") in ("completed", "failed", "cancelled"):
                break

            _time.sleep(interval)
            elapsed += interval

        pages = status_data.get("data", [])
        results: List[Dict[str, Any]] = []

        for page in pages:
            page_url = page.get("metadata", {}).get("url", page.get("url", ""))
            markdown = page.get("markdown", "")
            title = page.get("metadata", {}).get("title", "")

            entry: Dict[str, Any] = {
                "url": page_url,
                "markdown": markdown,
                "title": title,
                "cached": False,
            }

            if use_cache and markdown:
                _set_cache(page_url, {"url": page_url, "markdown": markdown, "html": "", "title": title, "cached": False})

            results.append(entry)

        return {"url": url, "pages": results, "total": len(results)}

    except requests.exceptions.RequestException as e:
        logger.error("Firecrawl crawl_site 失败: %s", e)
        return {"error": str(e), "url": url, "pages": [], "total": 0}


# ─────────────────────────────────────────────
# 3. search_web — 搜索并抓取结果
# ─────────────────────────────────────────────

def search_web(
    query: str,
    *,
    max_results: int = 5,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    搜索网页并抓取结果内容。

    参数:
        query: 搜索关键词
        max_results: 最大结果数
        use_cache: 是否使用缓存

    返回:
        {"query": str, "results": [{"url": ..., "markdown": ..., "title": ...}], "total": int}
    """
    headers = _api_headers()
    body: Dict[str, Any] = {
        "query": query,
        "maxResults": max_results,
        "scrapeOptions": {"formats": ["markdown"]},
    }

    try:
        response = requests.post(
            f"{_BASE_URL}/v1/search",
            headers=headers,
            json=body,
            timeout=300,
        )
        response.raise_for_status()
        pages = response.json().get("data", [])

        results: List[Dict[str, Any]] = []
        for page in pages:
            page_url = page.get("metadata", {}).get("url", page.get("url", ""))
            markdown = page.get("markdown", "")
            title = page.get("metadata", {}).get("title", "")

            entry: Dict[str, Any] = {
                "url": page_url,
                "markdown": markdown,
                "title": title,
                "snippet": page.get("metadata", {}).get("description", ""),
                "cached": False,
            }

            if use_cache and markdown:
                _set_cache(page_url, {"url": page_url, "markdown": markdown, "html": "", "title": title, "cached": False})

            results.append(entry)

        return {"query": query, "results": results, "total": len(results)}

    except requests.exceptions.RequestException as e:
        logger.error("Firecrawl search_web 失败: %s", e)
        return {"error": str(e), "query": query, "results": [], "total": 0}


# ─────────────────────────────────────────────
# 4. extract_structured — 结构化提取
# ─────────────────────────────────────────────

def extract_structured(
    url: str,
    schema: Dict[str, Any],
    *,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    按 JSON Schema 从网页提取结构化数据。

    参数:
        url: 目标 URL
        schema: JSON Schema 定义，如 {"type": "object", "properties": {...}}
        use_cache: 是否使用缓存

    返回:
        {"url": str, "data": {...}, "cached": bool}
    """
    headers = _api_headers()
    body: Dict[str, Any] = {
        "url": url,
        "extract": {"schema": schema},
    }

    try:
        response = requests.post(
            f"{_BASE_URL}/v1/scrape",
            headers=headers,
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        extracted = data.get("extract", data.get("llm_extraction", {}))
        result: Dict[str, Any] = {
            "url": url,
            "data": extracted,
            "cached": False,
        }

        if use_cache:
            _set_cache(url + "#structured", result)

        return result

    except requests.exceptions.RequestException as e:
        logger.error("Firecrawl extract_structured 失败: %s", e)
        return {"error": str(e), "url": url, "data": {}, "cached": False}

```

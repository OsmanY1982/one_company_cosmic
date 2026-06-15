# `opcclaw/core/multi_channel/platforms/zhihu.py`

> 路径：`opcclaw/core/multi_channel/platforms/zhihu.py` | 行数：191


---


```python
# -*- coding: utf-8 -*-
"""
知乎适配器
==========
通过知乎 API 发布文章/回答。

环境变量:
    ZHIHU_ACCESS_TOKEN  — 知乎 OAuth2 access_token

API 文档: https://www.zhihu.com/people/edit
"""

import os
import traceback
from typing import Dict, Any, List, Optional

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False


class ZhihuAdapter:
    """知乎适配器"""

    API_BASE = "https://api.zhihu.com"
    ARTICLE_URL = f"{API_BASE}/articles"
    ANSWER_URL = f"{API_BASE}/questions"  # /{question_id}/answers
    CONTENT_URL = f"{API_BASE}/people/self/contents"

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.environ.get("ZHIHU_ACCESS_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def check_health(self) -> Dict[str, Any]:
        status = self.is_configured()
        # 即使未配置 token，知乎也支持降级为本地草稿模式
        return {
            "platform": "zhihu",
            "configured": status,
            "mode": "live" if status else "draft_only",
            "error": None if status else "知乎未配置 access_token，将仅支持本地草稿模式",
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # ── 发布文章 ──

    def create_article(self, title: str, content: str,
                       topic_tags: Optional[List[str]] = None,
                       title_image_url: str = "") -> Dict[str, Any]:
        """
        发布知乎文章

        Args:
            title: 文章标题
            content: 文章内容（HTML 或 Markdown）
            topic_tags: 话题标签列表
            title_image_url: 题图 URL

        Returns:
            {"success": bool, "id": str, "url": str}
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "知乎未配置，请设置 ZHIHU_ACCESS_TOKEN",
                "mode": "draft_only",
            }

        if not _HAVE_REQUESTS:
            return {"success": False, "error": "缺少 requests 库"}

        body = {
            "title": title,
            "content": content,
        }
        if topic_tags:
            body["topics"] = topic_tags
        if title_image_url:
            body["title_image_url"] = title_image_url

        try:
            resp = requests.post(
                self.ARTICLE_URL,
                headers=self._headers(),
                json=body,
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        if "id" in data:
            return {
                "success": True,
                "id": str(data["id"]),
                "title": title,
                "url": data.get("url", f"https://zhuanlan.zhihu.com/p/{data['id']}"),
            }
        return {"success": False, "error": data.get("error", {}).get("message", "发布失败")}

    # ── 回答问题 ──

    def create_answer(self, question_id: str, content: str,
                      is_copyable: bool = True) -> Dict[str, Any]:
        """
        回答问题

        Args:
            question_id: 问题 ID
            content: 回答内容
            is_copyable: 是否允许转载

        Returns:
            {"success": bool, "id": str}
        """
        if not self.is_configured():
            return {"success": False, "error": "知乎未配置", "mode": "draft_only"}

        if not _HAVE_REQUESTS:
            return {"success": False, "error": "缺少 requests 库"}

        body = {
            "content": content,
            "is_copyable": is_copyable,
        }

        try:
            resp = requests.post(
                f"{self.ANSWER_URL}/{question_id}/answers",
                headers=self._headers(),
                json=body,
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        if "id" in data:
            return {
                "success": True,
                "id": str(data["id"]),
                "question_id": question_id,
                "url": data.get("url", ""),
            }
        return {"success": False, "error": data.get("error", {}).get("message", "发布失败")}

    # ── 获取已发布内容 ──

    def list_articles(self, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """获取已发布文章列表"""
        if not self.is_configured():
            return {"success": False, "error": "知乎未配置"}
        try:
            resp = requests.get(
                self.ARTICLE_URL,
                headers=self._headers(),
                params={"offset": offset, "limit": limit},
                timeout=30,
            )
            data = resp.json()
            if "data" in data:
                return {"success": True, "articles": data["data"],
                        "paging": data.get("paging", {})}
            return {"success": False, "error": "获取失败"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def publish(self, content: str, title: str = "",
                cover_image: str = "",
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用发布接口 — 优先创建文章"""
        extra = extra or {}
        question_id = extra.get("question_id", "")
        if question_id:
            return self.create_answer(question_id=question_id, content=content)
        return self.create_article(
            title=title or "无标题",
            content=content,
            topic_tags=extra.get("topic_tags"),
        )

```

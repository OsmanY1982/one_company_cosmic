# `opcclaw/core/multi_channel/platforms/linkedin.py`

> 路径：`opcclaw/core/multi_channel/platforms/linkedin.py` | 行数：145


---


```python
# -*- coding: utf-8 -*-
"""
LinkedIn 适配器
================
通过 LinkedIn API 发布动态/文章。

环境变量:
    LINKEDIN_ACCESS_TOKEN  — LinkedIn OAuth2 Access Token
    LINKEDIN_ORGANIZATION  — 组织 ID（发布组织动态时使用）

API 文档: https://learn.microsoft.com/en-us/linkedin/
"""

import os
import traceback
from typing import Dict, Any, List, Optional

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False


class LinkedInAdapter:
    """LinkedIn 适配器"""

    API_BASE = "https://api.linkedin.com/v2"
    POST_URL = f"{API_BASE}/ugcPosts"
    ARTICLE_URL = f"{API_BASE}/shares"
    ME_URL = f"{API_BASE}/me"

    def __init__(self, access_token: str = "", organization: str = ""):
        self.access_token = access_token or os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        self.organization = organization or os.environ.get("LINKEDIN_ORGANIZATION", "")

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def check_health(self) -> Dict[str, Any]:
        return {
            "platform": "linkedin",
            "configured": self.is_configured(),
            "organization": bool(self.organization),
            "error": None if self.is_configured() else "LinkedIn 未配置，请设置 LINKEDIN_ACCESS_TOKEN",
        }

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _get_author_urn(self) -> Optional[str]:
        """获取当前用户的 URN"""
        try:
            resp = requests.get(self.ME_URL, headers=self._headers(), timeout=30)
            data = resp.json()
            return data.get("id")
        except Exception:
            return None

    def post_status(self, text: str, url: str = "",
                    visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        发布 LinkedIn 动态

        Args:
            text: 动态文本
            url: 附带链接
            visibility: 可见性（PUBLIC / CONNECTIONS）

        Returns:
            {"success": bool, "id": str}
        """
        if not self.is_configured():
            return {"success": False, "error": "LinkedIn 未配置，请设置 LINKEDIN_ACCESS_TOKEN"}

        if not _HAVE_REQUESTS:
            return {"success": False, "error": "缺少 requests 库"}

        author_urn = self._get_author_urn()
        if not author_urn:
            return {"success": False, "error": "无法获取用户身份"}

        body = {
            "author": f"urn:li:person:{author_urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE" if url else "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility,
            },
        }
        if url:
            body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": url,
            }]

        try:
            resp = requests.post(
                self.POST_URL,
                headers=self._headers(),
                json=body,
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        if "id" in data:
            return {"success": True, "id": data["id"]}
        return {"success": False, "error": data.get("message", str(data))}

    def publish_article(self, title: str, content: str,
                        description: str = "",
                        visibility: str = "PUBLIC") -> Dict[str, Any]:
        """
        分享文章链接

        Args:
            title: 文章标题
            content: 分享评论文本
            description: 文章描述
            visibility: 可见性

        Returns:
            {"success": bool, "id": str}
        """
        # LinkedIn 的发布本质上是分享带评论的动态
        text = f"{title}\n\n{content}" if title else content
        return self.post_status(text=text, visibility=visibility)

    def publish(self, content: str, title: str = "",
                cover_image: str = "",
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用发布接口"""
        return self.publish_article(title=title, content=content)

```

# `iqra/core/multi_channel/platforms/twitter.py`

> 路径：`iqra/core/multi_channel/platforms/twitter.py` | 行数：116


---


```python
# -*- coding: utf-8 -*-
"""
Twitter/X 适配器
=================
通过 Twitter API v2 发布推文。

环境变量:
    TWITTER_API_KEY             — API Key
    TWITTER_API_SECRET          — API Secret
    TWITTER_ACCESS_TOKEN        — Access Token
    TWITTER_ACCESS_TOKEN_SECRET — Access Token Secret

API 文档: https://developer.x.com/en/docs
"""

import os
import traceback
from typing import Dict, Any, List, Optional

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False


class TwitterAdapter:
    """Twitter/X 适配器"""

    API_BASE = "https://api.twitter.com/2"
    TWEET_URL = f"{API_BASE}/tweets"

    def __init__(self, api_key: str = "", api_secret: str = "",
                 access_token: str = "", access_secret: str = ""):
        self.api_key = api_key or os.environ.get("TWITTER_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("TWITTER_API_SECRET", "")
        self.access_token = access_token or os.environ.get("TWITTER_ACCESS_TOKEN", "")
        self.access_secret = access_secret or os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

    def is_configured(self) -> bool:
        return all([self.api_key, self.api_secret, self.access_token, self.access_secret])

    def check_health(self) -> Dict[str, Any]:
        missing = []
        if not self.api_key: missing.append("TWITTER_API_KEY")
        if not self.api_secret: missing.append("TWITTER_API_SECRET")
        if not self.access_token: missing.append("TWITTER_ACCESS_TOKEN")
        if not self.access_secret: missing.append("TWITTER_ACCESS_TOKEN_SECRET")
        return {
            "platform": "twitter",
            "configured": self.is_configured(),
            "error": None if not missing else f"缺少环境变量: {', '.join(missing)}",
        }

    def _make_oauth1_request(self, method: str, url: str, json_body: dict = None,
                             timeout: int = 30) -> requests.Response:
        """使用 OAuth 1.0a 发送请求"""
        from requests_oauthlib import OAuth1
        auth = OAuth1(
            self.api_key, self.api_secret,
            self.access_token, self.access_secret,
        )
        kwargs = {"auth": auth, "timeout": timeout}
        if json_body is not None:
            kwargs["json"] = json_body
        return requests.request(method, url, **kwargs)

    def post_tweet(self, text: str) -> Dict[str, Any]:
        """
        发布推文

        Args:
            text: 推文内容（最多 280 字符）

        Returns:
            {"success": bool, "id": str, "text": str}
        """
        if not self.is_configured():
            return {"success": False, "error": "Twitter API 未配置，请设置 TWITTER_API_KEY 等环境变量"}

        if not _HAVE_REQUESTS:
            return {"success": False, "error": "缺少 requests 库"}

        # 截断超长文本
        if len(text) > 280:
            text = text[:277] + "..."

        try:
            resp = self._make_oauth1_request(
                "POST", self.TWEET_URL,
                json_body={"text": text},
            )
            data = resp.json()
        except ImportError:
            return {
                "success": False,
                "error": "缺少 requests_oauthlib 库（pip install requests_oauthlib）",
            }
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        if "data" in data and "id" in data["data"]:
            return {
                "success": True,
                "id": data["data"]["id"],
                "text": data["data"]["text"],
            }
        return {"success": False, "error": data.get("detail", str(data))}

    def publish(self, content: str, title: str = "",
                cover_image: str = "",
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用发布接口"""
        # Twitter 不支持标题，全内容即为推文
        return self.post_tweet(text=content)

```

# `opcclaw/core/multi_channel/platforms/weibo.py`

> 路径：`opcclaw/core/multi_channel/platforms/weibo.py` | 行数：153


---


```python
# -*- coding: utf-8 -*-
"""
微博适配器
==========
通过微博开放平台 API 发布微博。

环境变量:
    WEIBO_ACCESS_TOKEN  — 微博 OAuth2 access_token

API 文档: https://open.weibo.com/wiki/API文档V2
"""

import os
import traceback
from typing import Dict, Any, List, Optional

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False


class WeiboAdapter:
    """微博适配器"""

    API_BASE = "https://api.weibo.com/2"
    POST_URL = f"{API_BASE}/statuses/share.json"
    UPLOAD_URL = f"{API_BASE}/statuses/upload_url_text.json"
    TIMELINE_URL = f"{API_BASE}/statuses/user_timeline.json"

    # 微博字数限制
    MAX_TEXT_LENGTH = 140

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.environ.get("WEIBO_ACCESS_TOKEN", "")

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def check_health(self) -> Dict[str, Any]:
        return {
            "platform": "weibo",
            "configured": self.is_configured(),
            "error": None if self.is_configured() else "微博未配置，请设置环境变量 WEIBO_ACCESS_TOKEN",
        }

    # ── 发布微博 ──

    def post_status(self, text: str, images: Optional[List[str]] = None,
                    visible: int = 0) -> Dict[str, Any]:
        """
        发布微博

        Args:
            text: 微博文本（最多 140 字）
            images: 图片本地路径列表
            visible: 可见性（0=所有人，1=仅自己，6=好友圈）

        Returns:
            {"success": bool, "id": str, ...}
        """
        if not self.is_configured():
            return {"success": False, "error": "微博未配置，请设置 WEIBO_ACCESS_TOKEN"}

        if not _HAVE_REQUESTS:
            return {"success": False, "error": "缺少 requests 库"}

        # 截断超长文本
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH - 3] + "..."

        try:
            if images:
                # 带图微博
                resp = requests.post(
                    self.UPLOAD_URL,
                    params={"access_token": self.access_token, "status": text,
                            "visible": visible},
                    files={"pic": _open_image_files(images)},
                    timeout=60,
                )
            else:
                # 纯文本微博
                resp = requests.post(
                    self.POST_URL,
                    data={
                        "access_token": self.access_token,
                        "status": text,
                        "visible": visible,
                    },
                    timeout=30,
                )
            data = resp.json()
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

        if "id" in data or "idstr" in data:
            return {
                "success": True,
                "id": data.get("idstr", str(data.get("id", ""))),
                "text": text,
                "created_at": data.get("created_at", ""),
            }
        return {
            "success": False,
            "error": data.get("error", "发布失败"),
            "error_code": data.get("error_code", -1),
        }

    def publish(self, content: str, title: str = "",
                images: Optional[List[str]] = None,
                cover_image: str = "",
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用发布接口"""
        all_images = list(images or [])
        if cover_image:
            all_images.append(cover_image)
        return self.post_status(text=content, images=all_images or None)

    # ── 获取已发布微博 ──

    def get_timeline(self, count: int = 20, page: int = 1) -> Dict[str, Any]:
        """获取已发布微博列表"""
        if not self.is_configured():
            return {"success": False, "error": "微博未配置"}
        try:
            resp = requests.get(
                self.TIMELINE_URL,
                params={
                    "access_token": self.access_token,
                    "count": min(count, 100),
                    "page": page,
                },
                timeout=30,
            )
            data = resp.json()
            if "statuses" in data:
                return {"success": True, "statuses": data["statuses"],
                        "total_number": data.get("total_number", 0)}
            return {"success": False, "error": data.get("error", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}


def _open_image_files(paths: List[str]) -> List:
    """打开图片文件列表"""
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(("pic", (os.path.basename(p), open(p, "rb"), "image/*")))
    return files

```

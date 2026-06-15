# `opcclaw/core/multi_channel/platforms/wechat.py`

> 路径：`opcclaw/core/multi_channel/platforms/wechat.py` | 行数：260


---


```python
# -*- coding: utf-8 -*-
"""
微信公众号适配器
================
通过微信公众号 API 发布图文消息。

环境变量:
    WECHAT_APPID      — 公众号 AppID
    WECHAT_APPSECRET  — 公众号 AppSecret

API 文档: https://developers.weixin.qq.com/doc/offiaccount/
"""

import os
import json
import time
import traceback
from typing import Dict, Any, List, Optional

try:
    import requests
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False


class WechatAdapter:
    """微信公众号适配器"""

    # 微信 API 端点
    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
    DRAFT_LIST_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
    DRAFT_PUBLISH_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
    MATERIAL_ADD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    ARTICLE_LIST_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/batchget"

    def __init__(self, appid: str = "", appsecret: str = ""):
        self.appid = appid or os.environ.get("WECHAT_APPID", "")
        self.appsecret = appsecret or os.environ.get("WECHAT_APPSECRET", "")
        self._access_token: str = ""
        self._token_expires_at: float = 0

    # ── 认证 ──

    def get_access_token(self) -> Optional[str]:
        """获取/刷新 access_token"""
        if self._access_token and time.time() < self._token_expires_at - 300:
            return self._access_token

        if not self.appid or not self.appsecret:
            return None

        if not _HAVE_REQUESTS:
            return None

        try:
            resp = requests.get(
                self.TOKEN_URL,
                params={
                    "grant_type": "client_credential",
                    "appid": self.appid,
                    "secret": self.appsecret,
                },
                timeout=10,
            )
            data = resp.json()
            if "access_token" in data:
                self._access_token = data["access_token"]
                self._token_expires_at = time.time() + data.get("expires_in", 7200)
                return self._access_token
            else:
                return None
        except Exception:
            traceback.print_exc()
            return None

    def is_configured(self) -> bool:
        """检查 API 凭据是否已配置"""
        return bool(self.appid and self.appsecret)

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        token = self.get_access_token()
        return {
            "platform": "wechat",
            "configured": self.is_configured(),
            "authenticated": token is not None,
            "error": None if token else "access_token 获取失败（请检查 WECHAT_APPID / WECHAT_APPSECRET）",
        }

    # ── 素材管理 ──

    def upload_image(self, image_path: str) -> Dict[str, Any]:
        """上传图片素材，返回 media_id"""
        if not os.path.isfile(image_path):
            return {"success": False, "error": f"图片文件不存在: {image_path}"}

        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "未获取到 access_token"}

        try:
            with open(image_path, "rb") as f:
                resp = requests.post(
                    self.MATERIAL_ADD_URL,
                    params={"access_token": token, "type": "image"},
                    files={"media": f},
                    timeout=30,
                )
            data = resp.json()
            if "media_id" in data:
                return {"success": True, "media_id": data["media_id"],
                        "url": data.get("url", "")}
            return {"success": False, "error": data.get("errmsg", str(data))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 发布图文 ──

    def publish_article(self, title: str, content: str,
                        cover_image: str = "", digest: str = "",
                        need_open_comment: int = 0,
                        only_fans_can_comment: int = 0) -> Dict[str, Any]:
        """
        发布图文消息（先存草稿再发布）

        Args:
            title: 标题
            content: 正文（支持 HTML）
            cover_image: 封面图本地路径
            digest: 摘要
            need_open_comment: 是否开启评论
            only_fans_can_comment: 是否仅粉丝可评论

        Returns:
            {"success": bool, "msg_id": str, "draft_id": str}
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "微信公众号未配置，请设置环境变量 WECHAT_APPID 和 WECHAT_APPSECRET",
            }

        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "access_token 获取失败"}

        # Step 1: 上传封面图
        thumb_media_id = ""
        if cover_image and os.path.isfile(cover_image):
            upload_result = self.upload_image(cover_image)
            if upload_result.get("success"):
                thumb_media_id = upload_result["media_id"]

        # Step 2: 创建草稿
        articles = [{
            "title": title,
            "content": content,
            "digest": digest or content[:100].replace("\n", " "),
            "content_source_url": "",
            "need_open_comment": need_open_comment,
            "only_fans_can_comment": only_fans_can_comment,
        }]
        if thumb_media_id:
            articles[0]["thumb_media_id"] = thumb_media_id

        try:
            resp = requests.post(
                self.DRAFT_ADD_URL,
                params={"access_token": token},
                json={"articles": articles},
                timeout=30,
            )
            data = resp.json()
        except Exception as e:
            return {"success": False, "error": f"创建草稿请求失败: {e}"}

        if "media_id" not in data:
            return {"success": False, "error": data.get("errmsg", "未知错误"),
                    "errcode": data.get("errcode", -1)}

        draft_media_id = data["media_id"]

        # Step 3: 发布草稿
        try:
            resp = requests.post(
                self.DRAFT_PUBLISH_URL,
                params={"access_token": token},
                json={"media_id": draft_media_id},
                timeout=30,
            )
            pub_data = resp.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"发布请求失败: {e}",
                "draft_id": draft_media_id,
            }

        if "publish_id" in pub_data:
            return {
                "success": True,
                "draft_id": draft_media_id,
                "publish_id": pub_data["publish_id"],
                "msg_id": pub_data.get("msg_data_id", ""),
                "message": "图文已发布",
            }

        # 可能返回 errcode=0 但没有 publish_id（发布中）
        if pub_data.get("errcode") == 0:
            return {
                "success": True,
                "draft_id": draft_media_id,
                "publish_id": pub_data.get("publish_id", draft_media_id),
                "msg_id": "",
                "message": "图文已提交发布",
            }

        return {
            "success": False,
            "error": pub_data.get("errmsg", "发布失败"),
            "draft_id": draft_media_id,
            "errcode": pub_data.get("errcode", -1),
        }

    # ── 通用 publish 接口 ──

    def publish(self, content: str, title: str = "", cover_image: str = "",
                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """通用发布接口"""
        return self.publish_article(
            title=title or "无标题",
            content=content,
            cover_image=cover_image,
            **(extra or {}),
        )

    # ── 获取已发布列表 ──

    def get_published_articles(self, offset: int = 0, count: int = 20) -> Dict[str, Any]:
        """获取已发布文章列表"""
        token = self.get_access_token()
        if not token:
            return {"success": False, "error": "access_token 获取失败"}

        try:
            resp = requests.post(
                self.ARTICLE_LIST_URL,
                params={"access_token": token},
                json={"offset": offset, "count": count, "no_content": 1},
                timeout=30,
            )
            data = resp.json()
            if "item" in data:
                return {"success": True, "items": data["item"],
                        "total_count": data.get("total_count", 0)}
            return {"success": False, "error": data.get("errmsg", "获取失败")}
        except Exception as e:
            return {"success": False, "error": str(e)}

```

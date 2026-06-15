"""
飞书机器人适配器

使用飞书开放平台 API 发送消息。
支持文本消息、交互卡片、富文本消息。

环境变量:
    FEISHU_APP_ID     — 飞书应用 App ID
    FEISHU_APP_SECRET — 飞书应用 App Secret

依赖:
    requests（已有）

注意事项:
    本适配器当前仅支持发送消息（出站）。
    如需接收消息，需配置飞书事件订阅 + HTTP Server 接收回调。
"""

import json
import logging
import os
import time
from typing import Optional

from opcclaw.adapters.channels import (
    BaseChannelAdapter,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class FeishuAdapter(BaseChannelAdapter):
    """
    飞书机器人适配器（API 出站模式）。

    用法:
        adapter = FeishuAdapter()
        adapter.send_message("", OutgoingMessage(text="任务完成"))
        adapter.send_card("ou_xxx", card_json)

    API 参考:
        https://open.feishu.cn/document/server-docs/im-v1/message/create
    """

    channel_name = "feishu"

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, app_id: Optional[str] = None,
                 app_secret: Optional[str] = None):
        super().__init__()
        self._app_id = app_id or os.getenv("FEISHU_APP_ID", "")
        self._app_secret = app_secret or os.getenv("FEISHU_APP_SECRET", "")
        self._access_token: Optional[str] = None
        self._token_expire_at: float = 0.0

    # ── 启动 / 停止 ──

    def start(self) -> bool:
        if not _HAS_REQUESTS:
            logger.warning("requests 未安装，飞书适配器不可用")
            return False

        if not self._app_id or not self._app_secret:
            logger.warning("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未设置")
            return False

        self.is_running = True
        logger.info("飞书适配器就绪 (API 模式)")
        return True

    def stop(self) -> bool:
        self.is_running = False
        return True

    # ── Access Token ──

    def _get_access_token(self) -> Optional[str]:
        """获取/刷新 tenant_access_token"""
        if self._access_token and time.time() < self._token_expire_at - 60:
            return self._access_token

        try:
            resp = requests.post(
                f"{self.BASE_URL}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self._app_id,
                    "app_secret": self._app_secret,
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"飞书获取 token 失败: {data.get('msg', 'unknown')}")
                return None

            self._access_token = data["tenant_access_token"]
            self._token_expire_at = time.time() + data.get("expire", 7200)
            return self._access_token

        except Exception as e:
            logger.error(f"飞书 token 请求异常: {e}")
            return None

    # ── 发送 ──

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送文本消息。

        target_id: 飞书用户 open_id / chat_id / 群聊 chat_id
                   格式: "ou_xxx" / "oc_xxx" / "on_xxx"
        """
        token = self._get_access_token()
        if not token:
            return False

        content = {
            "text": message.text,
        }

        payload = {
            "receive_id": target_id,
            "msg_type": "text",
            "content": json.dumps(content),
        }

        return self._do_send(token, payload)

    def send_card(self, target_id: str, card_json: dict) -> bool:
        """
        发送交互卡片。

        card_json: 飞书卡片 JSON 对象
                   参考: https://open.feishu.cn/document/uAjLw4CM/ukzMukzMukzM/feishu-cards/card-components
        """
        token = self._get_access_token()
        if not token:
            return False

        payload = {
            "receive_id": target_id,
            "msg_type": "interactive",
            "content": json.dumps(card_json),
        }

        return self._do_send(token, payload)

    def send_rich_text(self, target_id: str, post_content: dict) -> bool:
        """
        发送富文本消息。

        post_content: 飞书 post 格式的 content 字典
                      参考: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/message/create
        """
        token = self._get_access_token()
        if not token:
            return False

        payload = {
            "receive_id": target_id,
            "msg_type": "post",
            "content": json.dumps(post_content),
        }

        return self._do_send(token, payload)

    def _do_send(self, token: str, payload: dict) -> bool:
        """执行飞书消息发送 API"""
        try:
            resp = requests.post(
                f"{self.BASE_URL}/im/v1/messages?receive_id_type=open_id",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"飞书发送失败: {data.get('msg', 'unknown')}")
                return False
            return True
        except Exception as e:
            logger.error(f"飞书请求异常: {e}")
            return False

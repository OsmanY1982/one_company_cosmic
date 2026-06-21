"""
Slack Bot 适配器

使用 Slack Bolt (Socket Mode) 接入 Slack。
支持 WebSocket 实时消息收发、事件回调。

环境变量:
    SLACK_BOT_TOKEN  — Slack Bot User OAuth Token (xoxb-...)
    SLACK_APP_TOKEN  — Slack App-Level Token (xapp-...), Socket Mode 必需

依赖（可选）:
    slack-bolt>=1.0
"""

import logging
import os
import threading
from typing import Callable, Optional

from iqra.adapters.channels import (
    BaseChannelAdapter,
    IncomingMessage,
    OutgoingMessage,
)

logger = logging.getLogger(__name__)

_HAS_SLACK = False

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    _HAS_SLACK = True
except ImportError:
    pass


class SlackAdapter(BaseChannelAdapter):
    """
    Slack Bot 适配器（Socket Mode）。

    用法:
        adapter = SlackAdapter()
        adapter.set_callback(lambda msg: print(f"收到: {msg.text}"))
        adapter.start()
        adapter.send_message(channel_id, OutgoingMessage(text="Hello"))
    """

    channel_name = "slack"

    def __init__(self, bot_token: Optional[str] = None,
                 app_token: Optional[str] = None):
        super().__init__()
        self._bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN", "")
        self._app_token = app_token or os.getenv("SLACK_APP_TOKEN", "")
        self._app: Optional[App] = None
        self._handler: Optional[SocketModeHandler] = None
        self._thread: Optional[threading.Thread] = None

    # ── 启动 / 停止 ──

    def start(self) -> bool:
        if not _HAS_SLACK:
            logger.warning("slack-bolt 未安装，Slack 适配器不可用")
            return False

        if not self._bot_token or not self._app_token:
            logger.warning("SLACK_BOT_TOKEN 或 SLACK_APP_TOKEN 未设置")
            return False

        if self.is_running:
            return True

        try:
            self._app = App(token=self._bot_token)

            @self._app.message()
            def handle_message(message, say):
                self._handle_message(message)

            @self._app.event("app_mention")
            def handle_mention(body, say):
                event = body.get("event", {})
                self._handle_message(event)

            self._handler = SocketModeHandler(self._app, self._app_token)

            self._thread = threading.Thread(
                target=self._handler.start,
                daemon=True,
                name="slack-socket",
            )
            self._thread.start()
            self.is_running = True
            logger.info("Slack Bot 已启动 (Socket Mode)")
            return True

        except Exception as e:
            logger.error(f"启动 Slack Bot 失败: {e}")
            self.is_running = False
            return False

    def stop(self) -> bool:
        if not self._handler:
            self.is_running = False
            return True

        try:
            self._handler.close()
            self.is_running = False
            logger.info("Slack Bot 已停止")
            return True
        except Exception as e:
            logger.error(f"停止 Slack Bot 失败: {e}")
            self.is_running = False
            return False

    # ── 消息处理 ──

    def _handle_message(self, event: dict) -> None:
        """处理接收到的 Slack 消息"""
        text = event.get("text", "")
        if not text:
            return

        # 跳过 bot 自身的消息和子类型消息
        if event.get("bot_id") or event.get("subtype"):
            return

        msg = IncomingMessage(
            channel="slack",
            user_id=event.get("user", ""),
            user_name=event.get("user", ""),  # Slack 事件通常不含 display name
            text=text,
            chat_id=event.get("channel", ""),
        )

        # 处理文件附件
        files = event.get("files", [])
        for f in files:
            msg.attachments.append({
                "type": f.get("mimetype", "file"),
                "url": f.get("url_private", ""),
                "name": f.get("name", ""),
            })

        self._notify(msg)

    # ── 发送 ──

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送消息到指定 Slack 频道/用户。

        target_id: Slack channel_id (C..., G..., D...)
        """
        if not self._app:
            logger.warning("Slack Bot 未启动，无法发送消息")
            return False

        try:
            result = self._app.client.chat_postMessage(
                channel=target_id,
                text=message.text,
                thread_ts=message.reply_to,
            )
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Slack 发送消息失败: {e}")
            return False

    def send_photo(self, target_id: str, image_path: str, caption: str = "") -> bool:
        """发送图片到指定 Slack 频道"""
        if not self._app:
            return False

        if not os.path.exists(image_path):
            logger.error(f"图片不存在: {image_path}")
            return False

        try:
            result = self._app.client.files_upload_v2(
                channel=target_id,
                file=image_path,
                initial_comment=caption or None,
            )
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Slack 发送图片失败: {e}")
            return False

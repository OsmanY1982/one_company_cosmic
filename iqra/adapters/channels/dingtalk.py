"""
钉钉机器人适配器

使用钉钉自定义机器人 Webhook 模式发送消息。
支持文本、Markdown、Link、ActionCard 等消息类型。

环境变量:
    DINGTALK_WEBHOOK_URL — 钉钉机器人 Webhook 地址
    DINGTALK_SECRET      — 加签密钥（可选，安全设置中配置）

依赖:
    requests（已有）

注意事项:
    钉钉 Webhook 模式仅支持出站消息（机器人 → 群），不支持接收消息。
    如需双向通信，需使用钉钉 Stream 模式或企业内部机器人。
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

from iqra.adapters.channels import (
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


class DingTalkAdapter(BaseChannelAdapter):
    """
    钉钉机器人适配器（Webhook 出站模式）。

    用法:
        adapter = DingTalkAdapter()
        adapter.send_message("", OutgoingMessage(text="任务完成"))
        adapter.send_markdown("日报", "## 今日工作总结\n...")
    """

    channel_name = "dingtalk"

    def __init__(self, webhook_url: Optional[str] = None,
                 secret: Optional[str] = None):
        super().__init__()
        self._webhook_url = webhook_url or os.getenv("DINGTALK_WEBHOOK_URL", "")
        self._secret = secret or os.getenv("DINGTALK_SECRET", "")

    # ── 启动 / 停止（Webhook 模式无需监听） ──

    def start(self) -> bool:
        if not _HAS_REQUESTS:
            logger.warning("requests 未安装，钉钉适配器不可用")
            return False

        if not self._webhook_url:
            logger.warning("DINGTALK_WEBHOOK_URL 未设置，钉钉适配器不可用")
            return False

        self.is_running = True
        logger.info("钉钉适配器就绪 (Webhook 模式，仅出站)")
        return True

    def stop(self) -> bool:
        self.is_running = False
        return True

    # ── 签名 ──

    def _generate_sign(self) -> tuple:
        """生成钉钉加签参数 (timestamp, sign)"""
        if not self._secret:
            return None, None
        timestamp = str(round(time.time() * 1000))
        secret_enc = self._secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self._secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    # ── 发送 ──

    def send_message(self, target_id: str, message: OutgoingMessage) -> bool:
        """
        发送文本消息到钉钉群。
        target_id 在 Webhook 模式下可忽略。
        """
        return self._do_send({
            "msgtype": "text",
            "text": {"content": message.text},
        })

    def send_markdown(self, title: str, markdown_text: str) -> bool:
        """
        发送 Markdown 消息到钉钉群。

        参数:
            title: 消息标题
            markdown_text: Markdown 格式文本
        """
        return self._do_send({
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": markdown_text,
            },
        })

    def send_link(self, title: str, text: str, message_url: str,
                  pic_url: str = "") -> bool:
        """发送链接消息"""
        return self._do_send({
            "msgtype": "link",
            "link": {
                "title": title,
                "text": text,
                "messageUrl": message_url,
                "picUrl": pic_url or "",
            },
        })

    def _do_send(self, payload: dict) -> bool:
        """执行 HTTP POST 到 Webhook"""
        if not self._webhook_url:
            logger.warning("钉钉 Webhook URL 未配置")
            return False

        url = self._webhook_url
        timestamp, sign = self._generate_sign()
        if timestamp and sign:
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            result = resp.json()
            if result.get("errcode") == 0:
                return True
            logger.error(f"钉钉发送失败: {result.get('errmsg', 'unknown')}")
            return False
        except Exception as e:
            logger.error(f"钉钉请求异常: {e}")
            return False
